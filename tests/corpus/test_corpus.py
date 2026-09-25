"""The rule catalog, measured on the labeled corpus (T035; SC-003, SC-007, SC-008)."""

from __future__ import annotations

from pathlib import Path

import pytest

from miraveja_persona.check import check_file
from miraveja_persona.findings import Finding
from miraveja_persona.vault import check_tree

from .conftest import Case, build, load_cases

CASES = load_cases()


def run(case: Case, tmp_path: Path) -> tuple[list[Path], list[Finding]]:
    root = tmp_path / "vault"
    root.mkdir()
    paths = []
    for i, spec in enumerate(case.files):
        path = root / f"f{i}" / "definition.persona.yaml"
        path.parent.mkdir()
        path.write_text(build(spec), encoding="utf-8")
        paths.append(path.resolve())
    if case.tree:
        (root / ".cofrealma").write_text("", encoding="utf-8")
        findings = [f for f in check_tree(root).findings if f.rule != "vault.synthetic-in-vault"]
    else:
        findings = check_file(paths[0]).findings
    return paths, findings


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_case(case: Case, tmp_path: Path) -> None:
    paths, findings = run(case, tmp_path)
    found = {(Path(f.file).resolve(), f.rule, f.part) for f in findings}
    expected = {(paths[e.get("file", 0)], e["rule"], e["part"]) for e in case.expect}
    missing = expected - found
    false = [f for f in findings if (Path(f.file).resolve(), f.rule, f.part) not in expected]
    assert not missing, f"seeded violations not flagged: {sorted((r, p) for _, r, p in missing)}"
    assert len(false) <= 1, "more than one false finding: " + "; ".join(
        f"{f.rule} {f.part} {f.quote!r}" for f in false
    )


def test_recall_is_total() -> None:
    """SC-003, SC-007, SC-008: every family is seeded, and clean definitions exist."""
    families = {c.family for c in CASES}
    assert {
        "orders",
        "metrics",
        "hardlines",
        "openly-ai",
        "pasts",
        "forbidden",
        "clean",
    } <= families
    assert sum(1 for c in CASES if c.family == "clean") >= 10
