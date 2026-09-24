"""`freeze` and the birth ledger (T023)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from miraveja_persona.cli import main
from miraveja_persona.yamlio import read_document

from ..conftest import make_vault


@pytest.fixture
def vault(tmp_path: Path, examples: Path) -> Path:
    return make_vault(tmp_path / "vault", examples, resident=True)


def freeze(path: Path, vault: Path) -> int:
    return main(["freeze", str(path), "--tree", str(vault)])


def test_freeze_records_a_birth(vault: Path) -> None:
    path = vault / "personas/pellam/definition.persona.yaml"
    assert freeze(path, vault) == 0
    (entry,) = read_document(vault / "ledger/births.yaml").data
    assert entry["id"] == "00000000-0000-4000-8000-00000000a001"
    assert entry["publicName"] == "Pellam Quist"
    assert entry["definition"] == "personas/pellam/definition.persona.yaml"
    assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert len(entry["bornOn"]) == 10


def test_ledger_is_append_only(vault: Path) -> None:
    assert freeze(vault / "personas/pellam/definition.persona.yaml", vault) == 0
    first = read_document(vault / "ledger/births.yaml").data[0]
    assert freeze(vault / "personas/ivo/definition.persona.yaml", vault) == 0
    entries = read_document(vault / "ledger/births.yaml").data
    assert entries[0] == first and len(entries) == 2


def test_refuses_already_frozen(vault: Path) -> None:
    path = vault / "personas/pellam/definition.persona.yaml"
    assert freeze(path, vault) == 0
    assert freeze(path, vault) == 1


def test_refuses_synthetic(tmp_path: Path, examples: Path) -> None:
    root = make_vault(tmp_path / "s", examples)
    assert freeze(root / "personas/pellam/definition.persona.yaml", root) == 1
    assert not (root / "ledger/births.yaml").exists()


def test_refuses_a_definition_failing_the_check(vault: Path) -> None:
    path = vault / "personas/pellam/definition.persona.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("openlyAI: true", "openlyAI: false"))
    assert freeze(path, vault) == 1
