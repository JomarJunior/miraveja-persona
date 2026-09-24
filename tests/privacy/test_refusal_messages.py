"""Refusals never carry prose from the file (T021, Principle VIII)."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import pytest

from miraveja_persona import DefinitionRefused, load_resident, load_synthetic
from miraveja_persona.check import check_file
from miraveja_persona.rules import iter_prose
from miraveja_persona.yamlio import read_document

from ..conftest import make_vault

MARKER = "zqxmarkerphrase"


def marked_copy(source: Path, target: Path, nature: str) -> Path:
    """Put a unique marker at the end of every prose field."""
    text = source.read_text(encoding="utf-8").replace("nature: synthetic", f"nature: {nature}")
    doc = read_document(source)
    for prose in iter_prose(doc.data, "persona"):
        last = prose.text.rstrip().splitlines()[-1]
        text = text.replace(last, f"{last} {MARKER}", 1)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def test_marker_is_in_every_prose_field(tmp_path: Path, examples: Path) -> None:
    path = marked_copy(
        examples / "pellam-quist.persona.yaml", tmp_path / "m.persona.yaml", "synthetic"
    )
    doc = read_document(path)
    assert all(MARKER in p.text for p in iter_prose(doc.data, "persona"))
    assert check_file(path).findings == []


@pytest.mark.parametrize("nature", ["resident", "synthetic"])
def test_refusals_have_no_prose(tmp_path: Path, examples: Path, nature: str) -> None:
    root = make_vault(tmp_path / "v", examples)
    inside = marked_copy(
        examples / "pellam-quist.persona.yaml",
        root / "personas/marked/definition.persona.yaml",
        nature,
    )
    outside = marked_copy(
        examples / "pellam-quist.persona.yaml", tmp_path / "o.persona.yaml", nature
    )
    broken = tmp_path / "b.persona.yaml"
    broken.write_text(
        outside.read_text(encoding="utf-8").replace("openlyAI: true", "openlyAI: false")
    )
    attempts: list[Callable[[], object]] = [
        lambda: load_resident(inside, root),
        lambda: load_resident(outside, root),
        lambda: load_synthetic(outside),
        lambda: load_synthetic(broken),
    ]
    for attempt in attempts:
        try:
            attempt()
        except DefinitionRefused as error:
            assert MARKER not in str(error)
            assert MARKER not in repr(error)
            assert re.fullmatch(r"[a-z_]+", error.reason)
