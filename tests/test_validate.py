"""Structure validation (T012, T013)."""

from __future__ import annotations

from pathlib import Path

import pytest

from miraveja_persona.check import check_file
from miraveja_persona.yamlio import read_document


def rules_for(path: Path) -> list[str]:
    return [f.rule for f in check_file(path).findings]


def variant(tmp_path: Path, examples: Path, old: str, new: str) -> Path:
    text = (examples / "pellam-quist.persona.yaml").read_text(encoding="utf-8")
    assert old in text, old
    path = tmp_path / "variant.persona.yaml"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return path


def test_hub_examples_have_no_findings(examples: Path) -> None:
    for path in sorted(examples.glob("*.yaml")):
        assert check_file(path).findings == [], path.name


def test_pellam_uses_every_part_of_the_format(examples: Path) -> None:
    """FR-023: one example holds every required and optional part."""
    data = read_document(examples / "pellam-quist.persona.yaml").data
    for key in ["craft", "selfImage", "lore", "sharedPasts"]:
        assert key in data, key
    assert "selfUnderstanding" in data["identity"]
    assert "dislikes" in data["taste"]
    tellings = {p["telling"] for p in data["sharedPasts"]}
    assert tellings == {"agreed", "intended-difference"}


@pytest.mark.parametrize(
    ("old", "new", "rule"),
    [
        ("  drawnTo: |", "  notDrawnTo: |", "structure.schema"),
        ("cares:\n", "authorNote: hidden\ncares:\n", "structure.schema"),
        ("openlyAI: true", "openlyAI: false", "structure.schema"),
        ("publicName: Pellam Quist", "publicName: " + "P" * 81, "structure.schema"),
        ("- id: leaving-gullmouth", "- id: first-storm", "structure.ids"),
        ("miravejaPersona: 1", "miravejaPersona: 2", "structure.version"),
        ("the gull at its center", "the gull at its center with {3}", "structure.placeholder"),
    ],
)
def test_each_structure_problem_has_its_rule(
    tmp_path: Path, examples: Path, old: str, new: str, rule: str
) -> None:
    assert rule in rules_for(variant(tmp_path, examples, old, new))


def test_version_finding_names_the_supported_versions(tmp_path: Path, examples: Path) -> None:
    path = variant(tmp_path, examples, "miravejaPersona: 1", "miravejaPersona: 2")
    (finding,) = check_file(path).findings
    assert "supported: 1" in finding.quote


def test_missing_self_in_participants(tmp_path: Path, examples: Path) -> None:
    text = (examples / "pellam-quist.persona.yaml").read_text(encoding="utf-8")
    own = "      - 00000000-0000-4000-8000-00000000a001\n"
    stranger = "      - 00000000-0000-4000-8000-00000000a003\n"
    text = text.replace(own + "      - 00000000", stranger + "      - 00000000")
    path = tmp_path / "v.persona.yaml"
    path.write_text(text, encoding="utf-8")
    assert "structure.self-in-participants" in rules_for(path)
