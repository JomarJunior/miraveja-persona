"""The guard never prints the content it blocks (T049, R-9)."""

from __future__ import annotations

from pathlib import Path

import pytest

from miraveja_persona.cli import main

from .test_refusal_messages import MARKER, marked_copy


def test_output_is_file_line_and_reason_only(
    tmp_path: Path, examples: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = tmp_path / "public"
    marked_copy(examples / "pellam-quist.persona.yaml", folder / "a.persona.yaml", "resident")
    marked_copy(examples / "ivo-marrowfield.persona.yaml", folder / "b.yaml", "resident")
    note = folder / "c.note.yaml"
    note.write_text(
        (examples / "lighthouse-mural.note.yaml")
        .read_text()
        .replace("nature: synthetic", "nature: resident")
        .replace("Neither", f"Neither {MARKER}")
    )
    pasted = folder / "d.md"
    pasted.write_text(f"miravejaPersona: 1\nidentity:\n  about: {MARKER}\n")
    assert main(["guard", str(folder)]) == 1
    captured = capsys.readouterr()
    assert MARKER not in captured.out and MARKER not in captured.err
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 4
    for line in lines:
        location, state, reason = line.split("  ", 2)
        assert state == "blocked" and ":" in location and reason


def test_secret_values_are_never_printed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = tmp_path / "public"
    folder.mkdir()
    secret = "gh" + "p_" + "Z9y8X7w6V5u4T3s2R1q0P9o8"
    (folder / "settings.toml").write_text(f'token = "{secret}"\n')
    assert main(["guard", str(folder)]) == 1
    captured = capsys.readouterr()
    assert secret not in captured.out + captured.err
    assert "secret-shaped value" in captured.out
