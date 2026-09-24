"""Structure: the schema, the version, and the rules a schema cannot state."""

from __future__ import annotations

import re
from typing import Any, Literal

from jsonschema import Draft202012Validator, FormatChecker

from .findings import Finding, make
from .schema import load_schema
from .yamlio import Document, escape

Kind = Literal["persona", "author-note"]
SUPPORTED_VERSIONS = (1,)
SIGNATURES: dict[str, Kind] = {"miravejaPersona": "persona", "miravejaAuthorNote": "author-note"}
PLACEHOLDER = re.compile(r"\{(\d+)\}")


def document_kind(data: Any) -> Kind | None:
    if isinstance(data, dict):
        for key, kind in SIGNATURES.items():
            if key in data:
                return kind
    return None


def _pointer(path: Any) -> str:
    return "".join(f"/{escape(str(p))}" for p in path)


def _finding(doc: Document, rule: str, part: str, quote: str, cites: str) -> Finding:
    return make(
        file=doc.path,
        rule=rule,
        part=part,
        data=doc.data,
        line=doc.line_of(part),
        quote=quote,
        cites=cites,
        certainty="certain",
    )


def structure_findings(doc: Document) -> list[Finding]:
    kind = document_kind(doc.data)
    if kind is None:
        return [
            _finding(
                doc,
                "structure.schema",
                "",
                "no miravejaPersona or miravejaAuthorNote key",
                "FR-001",
            )
        ]
    signature = "miravejaPersona" if kind == "persona" else "miravejaAuthorNote"
    version = doc.data.get(signature)
    if version not in SUPPORTED_VERSIONS:
        supported = ", ".join(str(v) for v in SUPPORTED_VERSIONS)
        return [
            _finding(
                doc,
                "structure.version",
                f"/{signature}",
                f"format version {version!r} is not supported; supported: {supported}",
                "FR-019",
            )
        ]
    validator = Draft202012Validator(load_schema(kind), format_checker=FormatChecker())
    findings = []
    for error in sorted(validator.iter_errors(doc.data), key=lambda e: list(e.absolute_path)):
        findings.append(
            _finding(
                doc,
                "structure.schema",
                _pointer(error.absolute_path),
                error.message,
                "FR-001 to FR-009, FR-034",
            )
        )
    if kind == "persona" and not findings:
        findings.extend(_persona_rules(doc))
    return findings


def _persona_rules(doc: Document) -> list[Finding]:
    data = doc.data
    findings: list[Finding] = []
    for list_name, field in (("seedMemories", "id"), ("sharedPasts", "story")):
        seen: set[str] = set()
        for i, item in enumerate(data.get(list_name, [])):
            value = item[field]
            if value in seen:
                findings.append(
                    _finding(doc, "structure.ids", f"/{list_name}/{i}/{field}", value, "FR-008")
                )
            seen.add(value)
    own_id = data["identity"]["id"]
    for i, past in enumerate(data.get("sharedPasts", [])):
        if own_id not in past["participants"]:
            findings.append(
                _finding(
                    doc,
                    "structure.self-in-participants",
                    f"/sharedPasts/{i}/participants",
                    "the persona's own identifier is not a participant",
                    "FR-027",
                )
            )
        count = len(past["participants"])
        for match in PLACEHOLDER.finditer(past["happened"]):
            if not 1 <= int(match.group(1)) <= count:
                findings.append(
                    _finding(
                        doc,
                        "structure.placeholder",
                        f"/sharedPasts/{i}/happened",
                        match.group(0),
                        "FR-027",
                    )
                )
    return findings
