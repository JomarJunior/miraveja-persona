"""The private vault: whole-tree checks, the birth ledger and freezing (R-7, R-8)."""

from __future__ import annotations

import datetime
import hashlib
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from .check import FileReport, Unreadable, check_file
from .findings import Finding, make
from .yamlio import YamlProblem, read_document

MARKER = ".cofrealma"
LEDGER = Path("ledger/births.yaml")
NOTE_KEYS = {
    "miravejaAuthorNote",
    "truth",
    "authorNote",
    "authorsNote",
    "authorNotes",
    "note",
    "notes",
}


@dataclass
class CheckResult:
    findings: list[Finding] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)


def is_vault(root: Path) -> bool:
    return (root / MARKER).is_file()


def vault_files(root: Path) -> list[Path]:
    found = [
        p.resolve()
        for pattern in ("*.persona.yaml", "*.note.yaml")
        for p in root.rglob(pattern)
        if ".git" not in p.relative_to(root).parts
    ]
    return sorted(set(found))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_ledger(root: Path) -> list[dict[str, Any]]:
    path = root / LEDGER
    if not path.is_file():
        return []
    data = read_document(path).data
    return [e for e in data if isinstance(e, dict)] if isinstance(data, list) else []


def ledger_entry(root: Path, persona_id: str) -> dict[str, Any] | None:
    for entry in read_ledger(root):
        if entry.get("id") == persona_id:
            return entry
    return None


def _write_ledger(root: Path, entries: list[dict[str, Any]]) -> None:
    yaml = YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    buffer = io.StringIO()
    buffer.write("# Birth ledger: one entry per persona that came alive. Append only (FR-037).\n")
    yaml.dump(entries, buffer)
    path = root / LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def _vault_finding(
    path: Path,
    rule: str,
    quote: str,
    cites: str,
    certainty: str = "certain",
    line: int = 1,
    part: str = "",
) -> Finding:
    return make(
        file=path,
        rule=rule,
        part=part,
        data=None,
        line=line,
        quote=quote,
        cites=cites,
        certainty="certain" if certainty == "certain" else "uncertain",
    )


def _has_note_keys(data: Any) -> str | None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in NOTE_KEYS:
                return str(key)
            found = _has_note_keys(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _has_note_keys(item)
            if found:
                return found
    return None


def _vault_rules(root: Path, reports: list[FileReport]) -> list[Finding]:
    findings: list[Finding] = []
    definitions = [r for r in reports if r.kind == "persona" and r.doc is not None]
    by_id: dict[str, list[Path]] = {}
    by_name: dict[str, list[Path]] = {}
    for report in definitions:
        assert report.doc is not None
        data = report.doc.data
        identity = data.get("identity") if isinstance(data.get("identity"), dict) else {}
        if isinstance(identity.get("id"), str):
            by_id.setdefault(identity["id"], []).append(report.path)
        if isinstance(identity.get("publicName"), str):
            by_name.setdefault(identity["publicName"], []).append(report.path)
        key = _has_note_keys(data)
        if key:
            findings.append(
                _vault_finding(
                    report.path,
                    "vault.note-inside",
                    f"author's note field '{key}' inside a definition",
                    "FR-031, FR-032",
                )
            )
        if data.get("nature") == "synthetic":
            findings.append(
                _vault_finding(
                    report.path,
                    "vault.synthetic-in-vault",
                    "a synthetic definition sits in the vault",
                    "FR-022",
                    certainty="uncertain",
                    part="/nature",
                    line=report.doc.line_of("/nature"),
                )
            )

    def rel(path: Path) -> str:
        return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)

    for label, index in (("identifier", by_id), ("public name", by_name)):
        for value, paths in index.items():
            for path in paths:
                for other in paths:
                    if other != path:
                        findings.append(
                            _vault_finding(
                                path,
                                "vault.reused",
                                f"{label} {value} is also used by {rel(other)}",
                                "FR-037",
                            )
                        )

    ledger_path = root / LEDGER
    ledger_doc = None
    if ledger_path.is_file():
        try:
            ledger_doc = read_document(ledger_path)
        except YamlProblem:
            findings.append(
                _vault_finding(
                    ledger_path, "structure.yaml", "the birth ledger is not valid YAML", "FR-037"
                )
            )
    for i, entry in enumerate(read_ledger(root) if ledger_doc else []):
        assert ledger_doc is not None
        line = ledger_doc.line_of(f"/{i}")
        target = (root / str(entry.get("definition", ""))).resolve()
        if not target.is_file():
            findings.append(
                _vault_finding(
                    ledger_path,
                    "vault.frozen-missing",
                    f"frozen definition {entry.get('definition')} is gone",
                    "FR-037",
                    line=line,
                )
            )
        elif entry.get("sha256") != sha256(target):
            findings.append(
                _vault_finding(
                    target,
                    "vault.frozen-changed",
                    f"changed since birth on {entry.get('bornOn')}",
                    "FR-018, FR-037",
                )
            )
        checks: list[tuple[str, dict[str, list[Path]], object]] = [
            ("identifier", by_id, entry.get("id")),
            ("public name", by_name, entry.get("publicName")),
        ]
        for label, index, taken in checks:
            for path in index.get(str(taken), []):
                if path != target:
                    findings.append(
                        _vault_finding(
                            path,
                            "vault.reused",
                            f"{label} {taken} belongs to a born persona "
                            f"({entry.get('definition')})",
                            "FR-037",
                        )
                    )
    return findings


def check_tree(root: Path) -> CheckResult:
    root = root.resolve()
    files = vault_files(root)
    reports = [check_file(path) for path in files]
    findings = [f for r in reports for f in r.findings]
    findings.extend(_vault_rules(root, reports))
    from .pasts import cross_definition_findings

    findings.extend(cross_definition_findings(reports))
    from .decisions import apply_decisions

    findings, stale = apply_decisions(findings, files)
    return CheckResult(findings, stale)


def check_paths(paths: list[Path], tree: Path | None = None) -> CheckResult:
    """`check PATH... [--tree ROOT]`. With a tree, the whole vault is checked, plus any
    path outside it."""
    from .decisions import apply_decisions

    for path in paths:
        if not path.is_file():
            raise Unreadable(f"{path}: no such file")
    if tree is None:
        findings = [f for path in paths for f in check_file(path).findings]
        findings, stale = apply_decisions(findings, paths)
        return CheckResult(findings, stale)
    if not is_vault(tree):
        raise Unreadable(f"{tree} is not a vault: it has no {MARKER} marker")
    result = check_tree(tree)
    root = tree.resolve()
    outside = [p for p in paths if not p.resolve().is_relative_to(root)]
    more, stale = apply_decisions([f for p in outside for f in check_file(p).findings], outside)
    return CheckResult(result.findings + more, result.stale + stale)


def freeze(path: Path, root: Path) -> tuple[bool, str]:
    root, path = root.resolve(), path.resolve()
    if not is_vault(root):
        return False, f"refused: {root} has no {MARKER} marker"
    if not path.is_file() or not path.is_relative_to(root):
        return False, "refused: the definition must be a file inside the vault"
    try:
        data = read_document(path).data
    except YamlProblem:
        return False, "refused: not one safe YAML document"
    if not isinstance(data, dict) or data.get("nature") != "resident":
        return False, "refused: only a resident definition can be frozen"
    persona_id = data.get("identity", {}).get("id")
    if ledger_entry(root, str(persona_id)) is not None:
        return False, "refused: this persona is already frozen"
    blocking = [
        f
        for f in check_tree(root).findings
        if Path(f.file).resolve() == path and (f.certainty == "certain" or not f.decided)
    ]
    if blocking:
        return False, f"refused: {len(blocking)} findings; run check --tree first"
    entries = read_ledger(root)
    entries.append(
        {
            "id": persona_id,
            "publicName": data["identity"]["publicName"],
            "definition": str(path.relative_to(root)),
            "sha256": sha256(path),
            "bornOn": datetime.date.today().isoformat(),
        }
    )
    _write_ledger(root, entries)
    return True, f"frozen {path.relative_to(root)}"
