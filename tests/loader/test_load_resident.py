"""`load_resident` in a scratch vault (T020)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from miraveja_persona import DefinitionRefused, load_resident
from miraveja_persona.cli import main

from ..conftest import as_resident, make_vault


@pytest.fixture
def vault(tmp_path: Path, examples: Path) -> Path:
    return make_vault(tmp_path / "vault", examples, resident=True)


def pellam(vault: Path) -> Path:
    return vault / "personas/pellam/definition.persona.yaml"


def refused(path: Path, root: Path) -> str:
    with pytest.raises(DefinitionRefused) as error:
        load_resident(path, root)
    return error.value.reason


def test_accepts_a_born_unchanged_resident(vault: Path) -> None:
    assert main(["freeze", str(pellam(vault)), "--tree", str(vault)]) == 0
    d = load_resident(pellam(vault), vault)
    assert d.nature == "resident"


def test_refuses_synthetic(tmp_path: Path, examples: Path) -> None:
    root = make_vault(tmp_path / "v", examples)
    assert refused(root / "personas/pellam/definition.persona.yaml", root) == (
        "synthetic_as_resident"
    )


def test_refuses_outside_vault(tmp_path: Path, examples: Path, vault: Path) -> None:
    outside = as_resident(examples / "pellam-quist.persona.yaml", tmp_path / "loose.persona.yaml")
    assert refused(outside, vault) == "outside_vault"
    unmarked = tmp_path / "unmarked"
    shutil.copytree(vault, unmarked)
    (unmarked / ".cofrealma").unlink()
    assert refused(pellam(unmarked), unmarked) == "outside_vault"


def test_refuses_not_born(vault: Path) -> None:
    assert refused(pellam(vault), vault) == "not_born"


def test_refuses_changed_since_birth(vault: Path) -> None:
    assert main(["freeze", str(pellam(vault)), "--tree", str(vault)]) == 0
    path = pellam(vault)
    path.write_text(path.read_text(encoding="utf-8").replace("quiet", "calm"), encoding="utf-8")
    assert refused(path, vault) == "changed_since_birth"


def test_refuses_author_note(vault: Path) -> None:
    assert refused(vault / "notes/lighthouse-mural.note.yaml", vault) == "author_note"
