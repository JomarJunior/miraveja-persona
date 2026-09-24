"""`check` on single files (T016)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from miraveja_persona.cli import main


def test_examples_are_valid(examples: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", *map(str, sorted(examples.glob("*.yaml")))]) == 0
    assert capsys.readouterr().out.strip() == ""


def test_scaffold_names_each_empty_required_part(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "nine.persona.yaml"
    main(["new", "--name", "Test Persona Nine", "--synthetic", "-o", str(path)])
    capsys.readouterr()
    assert main(["check", str(path)]) == 1
    out = capsys.readouterr().out
    for part in [
        "/identity/about",
        "/taste/drawnTo",
        "/voice/speech",
        "/tendencies/work",
        "/cares/0",
        "/seedMemories/0/happened",
    ]:
        assert part in out, part


def test_unreadable_file_is_a_usage_error(tmp_path: Path) -> None:
    assert main(["check", str(tmp_path / "missing.persona.yaml")]) == 2


def test_json_output_is_a_list_of_findings(
    tmp_path: Path, examples: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    text = (examples / "pellam-quist.persona.yaml").read_text(encoding="utf-8")
    path = tmp_path / "v.persona.yaml"
    path.write_text(text.replace("openlyAI: true", "openlyAI: false"), encoding="utf-8")
    assert main(["check", "--format", "json", str(path)]) == 1
    rows = json.loads(capsys.readouterr().out)
    assert rows and {"rule", "part", "line", "quote", "cites", "certainty", "fingerprint"} <= set(
        rows[0]
    )
