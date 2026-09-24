"""`load_synthetic` (T019)."""

from __future__ import annotations

from pathlib import Path

import pytest

from miraveja_persona import Definition, DefinitionRefused, load_synthetic

from ..conftest import as_resident


def test_returns_every_part(examples: Path) -> None:
    d = load_synthetic(examples / "pellam-quist.persona.yaml")
    assert isinstance(d, Definition)
    assert d.identity.public_name == "Pellam Quist"
    assert d.identity.openly_ai is True
    assert d.identity.self_understanding
    assert d.taste.themes and d.taste.dislikes and d.voice.speech and d.tendencies.work
    assert d.cares and d.craft and d.self_image
    assert d.lore is not None and d.lore.names[0].name == "Gullmouth"
    assert [m.id for m in d.seed_memories] == ["first-storm", "leaving-gullmouth"]
    regatta = d.shared_pasts[0]
    assert "{1}" in regatta.happened and "{2}" in regatta.happened
    assert regatta.participants[0] == d.identity.id


def test_is_frozen(examples: Path) -> None:
    d = load_synthetic(examples / "pellam-quist.persona.yaml")
    with pytest.raises(Exception):  # noqa: B017  pydantic raises ValidationError on frozen models
        d.identity.public_name = "Someone Else"  # type: ignore[misc]


def refused(path: Path) -> str:
    with pytest.raises(DefinitionRefused) as error:
        load_synthetic(path)
    return error.value.reason


def test_refuses_resident(tmp_path: Path, examples: Path) -> None:
    path = as_resident(examples / "pellam-quist.persona.yaml", tmp_path / "p.persona.yaml")
    assert refused(path) == "resident_outside_studio"


def test_refuses_author_note(examples: Path) -> None:
    assert refused(examples / "lighthouse-mural.note.yaml") == "author_note"


def test_refuses_unsupported_version(tmp_path: Path, examples: Path) -> None:
    path = tmp_path / "v.persona.yaml"
    text = (examples / "pellam-quist.persona.yaml").read_text(encoding="utf-8")
    path.write_text(text.replace("miravejaPersona: 1", "miravejaPersona: 2"), encoding="utf-8")
    with pytest.raises(DefinitionRefused) as error:
        load_synthetic(path)
    assert error.value.reason == "unsupported_version"
    assert "supported: 1" in str(error.value)


def test_refuses_invalid(tmp_path: Path, examples: Path) -> None:
    path = tmp_path / "v.persona.yaml"
    text = (examples / "pellam-quist.persona.yaml").read_text(encoding="utf-8")
    path.write_text(text.replace("openlyAI: true", "openlyAI: false"), encoding="utf-8")
    with pytest.raises(DefinitionRefused) as error:
        load_synthetic(path)
    assert error.value.reason == "invalid"
    assert error.value.findings
