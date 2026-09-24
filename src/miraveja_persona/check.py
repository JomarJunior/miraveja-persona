"""Run the structure checks and the rule catalog over files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .findings import Finding, make
from .rules import Subject, all_rules, applies_to
from .validate import Kind, document_kind, structure_findings
from .yamlio import Document, YamlProblem, read_document


class Unreadable(Exception):
    """The path is missing or is not UTF-8 text. A usage problem, not a finding."""


@dataclass
class FileReport:
    path: Path
    kind: Kind | None
    doc: Document | None
    findings: list[Finding] = field(default_factory=list)

    @property
    def valid_structure(self) -> bool:
        return self.doc is not None and not any(
            f.rule.startswith("structure.") for f in self.findings
        )


def allowed_names(doc: Document, kind: Kind) -> frozenset[str]:
    """Declared lore names and the persona's own public name (R-5)."""
    names: set[str] = set()
    data = doc.data
    if kind == "persona" and isinstance(data, dict):
        identity = data.get("identity")
        if isinstance(identity, dict) and isinstance(identity.get("publicName"), str):
            names.add(identity["publicName"])
        lore = data.get("lore")
        if isinstance(lore, dict):
            for item in lore.get("names") or []:
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    names.add(item["name"])
    return frozenset(names)


def check_document(doc: Document, *, extra_names: frozenset[str] = frozenset()) -> list[Finding]:
    findings = structure_findings(doc)
    kind = document_kind(doc.data)
    if kind is None or any(f.rule == "structure.version" for f in findings):
        return findings
    subject = Subject(doc, kind, allowed_names(doc, kind) | extra_names)
    for rule in all_rules():
        findings.extend(f for f in rule(subject) if applies_to(f.rule, kind))
    return _dedupe(findings)


def check_file(path: Path | str, *, extra_names: frozenset[str] = frozenset()) -> FileReport:
    path = Path(path)
    if not path.is_file():
        raise Unreadable(f"{path}: no such file")
    try:
        doc = read_document(path)
    except YamlProblem as problem:
        if problem.line == 0 and "UTF-8" in problem.message:
            raise Unreadable(f"{path}: {problem.message}") from None
        finding = make(
            file=path,
            rule="structure.yaml",
            part="",
            data=None,
            line=max(problem.line, 1),
            quote=problem.message,
            cites="FR-009",
            certainty="certain",
        )
        return FileReport(path, None, None, [finding])
    return FileReport(
        path, document_kind(doc.data), doc, check_document(doc, extra_names=extra_names)
    )


def _dedupe(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str, str]] = set()
    unique = []
    for f in sorted(findings, key=lambda f: (f.line, f.part, f.rule)):
        marker = (f.rule, f.part, f.quote)
        if marker not in seen:
            seen.add(marker)
            unique.append(f)
    return unique


def exit_code(findings: list[Finding]) -> int:
    if any(f.certainty == "certain" for f in findings):
        return 1
    if any(f.certainty == "uncertain" and not f.decided for f in findings):
        return 3
    return 0
