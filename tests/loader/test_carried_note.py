"""A definition carrying an author's note is refused by both loaders (T065; FR-032, SC-008)."""

from __future__ import annotations

from pathlib import Path

import pytest

from miraveja_persona import DefinitionRefused, load_resident, load_synthetic
from miraveja_persona.cli import main

from ..conftest import make_vault

CARRIED = [
    "truth: the gull was painted by someone else\n",
    "authorNote: the gull was painted by someone else\n",
    "miravejaAuthorNote: 1\n",
]


@pytest.mark.parametrize("line", CARRIED)
def test_load_synthetic_refuses(tmp_path: Path, examples: Path, line: str) -> None:
    path = tmp_path / "carried.persona.yaml"
    path.write_text((examples / "pellam-quist.persona.yaml").read_text() + line)
    with pytest.raises(DefinitionRefused):
        load_synthetic(path)


@pytest.mark.parametrize("line", CARRIED)
def test_load_resident_refuses(tmp_path: Path, examples: Path, line: str) -> None:
    vault = make_vault(tmp_path / "vault", examples, resident=True)
    path = vault / "personas/pellam/definition.persona.yaml"
    assert main(["freeze", str(path), "--tree", str(vault)]) == 0
    path.write_text(path.read_text() + line)
    with pytest.raises(DefinitionRefused) as error:
        load_resident(path, vault)
    assert error.value.reason in {"invalid", "author_note", "changed_since_birth"}
