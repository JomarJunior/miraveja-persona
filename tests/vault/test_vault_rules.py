"""Vault-wide rules (T025)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from miraveja_persona.cli import main
from miraveja_persona.vault import check_tree

from ..conftest import as_resident, make_vault


@pytest.fixture
def vault(tmp_path: Path, examples: Path) -> Path:
    return make_vault(tmp_path / "vault", examples, resident=True)


def rules(vault: Path) -> list[str]:
    return [f.rule for f in check_tree(vault).findings]


def pellam(vault: Path) -> Path:
    return vault / "personas/pellam/definition.persona.yaml"


def test_clean_vault_has_no_vault_findings(vault: Path) -> None:
    assert not [r for r in rules(vault) if r.startswith("vault.")]


def test_frozen_changed(vault: Path) -> None:
    main(["freeze", str(pellam(vault)), "--tree", str(vault)])
    pellam(vault).write_text(pellam(vault).read_text().replace("quiet", "calm"))
    assert "vault.frozen-changed" in rules(vault)


def test_frozen_missing(vault: Path) -> None:
    main(["freeze", str(pellam(vault)), "--tree", str(vault)])
    pellam(vault).unlink()
    assert "vault.frozen-missing" in rules(vault)


def test_reused_identifier_and_public_name(vault: Path) -> None:
    copy = vault / "personas/copy/definition.persona.yaml"
    copy.parent.mkdir()
    shutil.copy(pellam(vault), copy)
    quotes = [f.quote for f in check_tree(vault).findings if f.rule == "vault.reused"]
    assert any(q.startswith("identifier") for q in quotes)
    assert any(q.startswith("public name") for q in quotes)


def test_reuse_of_a_departed_persona(vault: Path, examples: Path) -> None:
    """A ledger entry keeps its identifier and name taken even when its file moved away."""
    main(["freeze", str(pellam(vault)), "--tree", str(vault)])
    moved = vault / "personas/pellam-new/definition.persona.yaml"
    moved.parent.mkdir()
    shutil.move(pellam(vault), moved)
    assert "vault.reused" in rules(vault)


def test_note_inside_a_definition(vault: Path) -> None:
    text = pellam(vault).read_text()
    pellam(vault).write_text(text + "truth: hidden lore\n")
    assert "vault.note-inside" in rules(vault)


def test_synthetic_in_vault_is_asked_about(tmp_path: Path, examples: Path) -> None:
    root = make_vault(tmp_path / "s", examples)
    found = [f for f in check_tree(root).findings if f.rule == "vault.synthetic-in-vault"]
    assert found and all(f.certainty == "uncertain" for f in found)


def test_check_tree_exit_codes(vault: Path, examples: Path, tmp_path: Path) -> None:
    assert main(["check", "--tree", str(vault), str(pellam(vault))]) == 0
    as_resident(examples / "pellam-quist.persona.yaml", vault / "personas/dup/x.persona.yaml")
    assert main(["check", "--tree", str(vault), str(pellam(vault))]) == 1
