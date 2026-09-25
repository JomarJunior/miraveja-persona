"""Author's notes get only the hard-line, money, visitor and secret rules (T042, FR-033)."""

from __future__ import annotations

from pathlib import Path

from miraveja_persona.check import check_file


def note(tmp_path: Path, examples: Path, truth: str) -> Path:
    text = (examples / "lighthouse-mural.note.yaml").read_text(encoding="utf-8")
    start = text.index("truth: |")
    end = text.index("writtenBy:")
    path = tmp_path / "n.note.yaml"
    path.write_text(text[:start] + f"truth: {truth!r}\n" + text[end:], encoding="utf-8")
    return path


def test_motives_and_orders_are_allowed_in_notes(tmp_path: Path, examples: Path) -> None:
    truth = "Ivo lies because he is jealous of the gull, and he must never admit it."
    rules = {f.rule for f in check_file(note(tmp_path, examples, truth)).findings}
    assert not {r for r in rules if r.startswith(("order.", "past."))}


def test_money_and_hard_lines_still_apply(tmp_path: Path, examples: Path) -> None:
    truth = "The night fisher sold the gull painting and imitates Corvan Dace."
    rules = {f.rule for f in check_file(note(tmp_path, examples, truth)).findings}
    assert {"metric.money", "hardline.living-artist-style"} <= rules
