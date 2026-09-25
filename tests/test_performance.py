"""The plan's performance goals (T067)."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

from miraveja_persona.cli import main

LIBRARY = Path(__file__).resolve().parents[1]


def timed(argv: list[str]) -> float:
    started = time.monotonic()
    main(argv)
    return time.monotonic() - started


def test_check_one_definition_under_two_seconds(examples: Path) -> None:
    assert timed(["check", str(examples / "pellam-quist.persona.yaml")]) < 2.0


def test_check_tree_of_twenty_under_ten_seconds(tmp_path: Path, examples: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".cofrealma").write_text("")
    clean = sorted((LIBRARY / "tests/corpus/clean").glob("*.persona.yaml"))
    sources = [
        *clean,
        examples / "pellam-quist.persona.yaml",
        examples / "ivo-marrowfield.persona.yaml",
    ]
    for i in range(20):
        target = vault / f"p{i}" / "definition.persona.yaml"
        target.parent.mkdir()
        shutil.copy(sources[i % len(sources)], target)
    assert timed(["check", "--tree", str(vault), str(target)]) < 10.0


def test_guard_on_this_repository_under_ten_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    if not (LIBRARY / ".git").exists():
        pytest.skip("not a git checkout")
    monkeypatch.chdir(LIBRARY)
    assert timed(["guard"]) < 10.0
