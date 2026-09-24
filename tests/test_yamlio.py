"""Safe YAML reading (T008, T009)."""

from __future__ import annotations

from pathlib import Path

import pytest

from miraveja_persona.check import check_file
from miraveja_persona.yamlio import YamlProblem, read_document


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "x.persona.yaml"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ("a: 1\na: 2\n", 2),
        ("a: &x 1\nb: *x\n", 1),
        ("a: !custom 1\n", 1),
        ("a: 1\n---\nb: 2\n", 2),
    ],
)
def test_unsafe_yaml_is_refused_with_a_line(tmp_path: Path, text: str, line: int) -> None:
    with pytest.raises(YamlProblem) as problem:
        read_document(write(tmp_path, text))
    assert problem.value.line == line


@pytest.mark.parametrize("text", ["a: 1\na: 2\n", "a: &x 1\nb: *x\n", "a: !t 1\n"])
def test_unsafe_yaml_becomes_a_structure_finding(tmp_path: Path, text: str) -> None:
    report = check_file(write(tmp_path, text))
    assert [f.rule for f in report.findings] == ["structure.yaml"]
    assert report.findings[0].line >= 1


def test_date_shaped_values_stay_strings(tmp_path: Path) -> None:
    doc = read_document(write(tmp_path, "when: 2026-09-24\nn: 3\nflag: true\nq: '3'\n"))
    assert doc.data == {"when": "2026-09-24", "n": 3, "flag": True, "q": "3"}


def test_lines_are_kept_per_field(tmp_path: Path) -> None:
    doc = read_document(write(tmp_path, "a:\n  b: |\n    text\n  c: [x, y]\n"))
    assert doc.line_of("/a/b") == 2
    assert doc.line_of("/a/c/1") == 4
