"""`pasts` lists every shared past in the vault (T046; FR-028, SC-007)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from miraveja_persona.cli import main

from ..conftest import make_vault


def test_lists_agreed_and_intended_differences(
    tmp_path: Path, examples: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = make_vault(tmp_path / "vault", examples)
    started = time.monotonic()
    assert main(["pasts", str(vault), "--format", "json"]) == 0
    assert time.monotonic() - started < 1.0
    stories = {s["story"]: s for s in json.loads(capsys.readouterr().out)}
    regatta, mural = stories["junior-regatta"], stories["lighthouse-mural"]
    assert regatta["telling"] == "agreed" and len(regatta["versions"]) == 1
    assert mural["telling"] == "intended-difference" and len(mural["versions"]) == 2
    names = {p["publicName"] for p in mural["participants"]}
    ids = {p["id"] for p in mural["participants"]}
    assert names == {"Pellam Quist", "Ivo Marrowfield"}
    assert ids == {"00000000-0000-4000-8000-00000000a001", "00000000-0000-4000-8000-00000000a002"}


def test_text_output(tmp_path: Path, examples: Path, capsys: pytest.CaptureFixture[str]) -> None:
    vault = make_vault(tmp_path / "vault", examples)
    assert main(["pasts", str(vault)]) == 0
    out = capsys.readouterr().out
    assert "lighthouse-mural  [intended-difference]" in out
    assert "Pellam Quist (00000000-0000-4000-8000-00000000a001)" in out


def test_empty_vault(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / ".cofrealma").write_text("")
    assert main(["pasts", str(tmp_path)]) == 0
    assert "no shared pasts" in capsys.readouterr().out
