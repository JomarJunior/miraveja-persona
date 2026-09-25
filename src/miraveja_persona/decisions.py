"""Decisions on uncertain findings, kept in `decisions.yaml` beside each definition (R-6).

Only uncertain findings can be decided. A decided finding is still reported, marked with
its decision, so nothing passes silently (FR-017).
"""

from __future__ import annotations

import datetime
import io
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from .findings import Finding
from .yamlio import YamlProblem, read_document

FILE = "decisions.yaml"


def _read(directory: Path) -> list[dict[str, Any]]:
    path = directory / FILE
    if not path.is_file():
        return []
    try:
        data = read_document(path).data
    except YamlProblem:
        return []
    return [d for d in data if isinstance(d, dict)] if isinstance(data, list) else []


def apply_decisions(
    findings: list[Finding], checked: list[Path] | None = None
) -> tuple[list[Finding], list[str]]:
    """Mark decided findings. `checked` are the files checked, so decisions in a folder whose
    findings are all gone are still reported as stale."""
    by_dir: dict[Path, dict[str, str]] = {}
    directories = [Path(f.file).resolve().parent for f in findings]
    directories += [p.resolve().parent for p in checked or []]
    for directory in directories:
        if directory not in by_dir:
            by_dir[directory] = {
                str(d.get("finding")): str(d.get("decision")) for d in _read(directory)
            }
    used: set[tuple[Path, str]] = set()
    out = []
    for f in findings:
        directory = Path(f.file).resolve().parent
        decision = by_dir[directory].get(f.fingerprint)
        if decision and f.certainty == "uncertain":
            used.add((directory, f.fingerprint))
            out.append(f.with_decision(decision))
        else:
            out.append(f)
    stale = [
        f"{directory / FILE}: {fp}"
        for directory, decided in by_dir.items()
        for fp in decided
        if (directory, fp) not in used
    ]
    return out, stale


def _append(directory: Path, entry: dict[str, Any]) -> None:
    entries = [*_read(directory), entry]
    yaml = YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    buffer = io.StringIO()
    buffer.write("# Team decisions on uncertain findings (FR-017). One entry per finding.\n")
    yaml.dump(entries, buffer)
    (directory / FILE).write_text(buffer.getvalue(), encoding="utf-8")


def decide(fingerprint: str, decision: str, by: str, tree: Path | None) -> tuple[bool, str]:
    from .check import check_file
    from .vault import check_tree

    if tree is not None:
        findings = check_tree(tree).findings
    else:
        files = sorted(Path.cwd().rglob("*.persona.yaml")) + sorted(Path.cwd().rglob("*.note.yaml"))
        findings, _ = apply_decisions([f for p in files for f in check_file(p).findings])
    matches = [f for f in findings if f.fingerprint == fingerprint]
    if not matches:
        return False, f"refused: no current finding has fingerprint {fingerprint}"
    finding = matches[0]
    if finding.certainty == "certain":
        return False, "refused: certain findings cannot be decided; change the definition"
    directory = Path(finding.file).resolve().parent
    _append(
        directory,
        {
            "finding": fingerprint,
            "decision": decision,
            "by": by,
            "on": datetime.date.today().isoformat(),
        },
    )
    return True, f"recorded {decision} for {fingerprint} in {directory / FILE}"
