"""`new` writes a scaffold for a fresh persona (T014, SC-001)."""

from __future__ import annotations

from pathlib import Path

import pytest

from miraveja_persona.cli import main
from miraveja_persona.scaffold import OPTIONAL_PARTS
from miraveja_persona.yamlio import read_document


def scaffold(tmp_path: Path, name: str = "nine") -> Path:
    path = tmp_path / f"{name}.persona.yaml"
    assert main(["new", "--name", "Test Persona Nine", "--synthetic", "-o", str(path)]) == 0
    return path


def test_scaffold_has_every_part_with_guidance(tmp_path: Path) -> None:
    path = scaffold(tmp_path)
    text = path.read_text(encoding="utf-8")
    data = read_document(path).data
    assert data["nature"] == "synthetic"
    assert data["identity"]["publicName"] == "Test Persona Nine"
    assert data["identity"]["openlyAI"] is True
    for part in ["identity", "taste", "voice", "tendencies", "cares", "seedMemories"]:
        assert part in data
    for part in OPTIONAL_PARTS:
        assert f"# {part}:" in text, f"optional part {part} missing from the scaffold"
    assert text.count("# ") > 20, "every part carries a guidance comment"


def test_guidance_never_reaches_the_loaded_data(tmp_path: Path) -> None:
    data = read_document(scaffold(tmp_path)).data
    assert "#" not in repr(data)


def test_fresh_identifier_each_time(tmp_path: Path) -> None:
    a = read_document(scaffold(tmp_path, "a")).data["identity"]["id"]
    b = read_document(scaffold(tmp_path, "b")).data["identity"]["id"]
    assert a != b


def test_refuses_to_overwrite(tmp_path: Path) -> None:
    path = scaffold(tmp_path)
    before = path.read_text(encoding="utf-8")
    assert main(["new", "--name", "Other", "-o", str(path)]) == 2
    assert path.read_text(encoding="utf-8") == before


def test_resident_is_the_default(tmp_path: Path) -> None:
    path = tmp_path / "r.persona.yaml"
    assert main(["new", "--name", "Test Persona Ten", "-o", str(path)]) == 0
    assert read_document(path).data["nature"] == "resident"


@pytest.mark.parametrize("name", ["", "x" * 81])
def test_public_name_bounds(tmp_path: Path, name: str) -> None:
    assert main(["new", "--name", name, "-o", str(tmp_path / "n.persona.yaml")]) == 2
