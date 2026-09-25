"""The public-repository guard (T048; FR-021, SC-004). Resident files exist only in tmp."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from miraveja_persona.cli import main

from ..conftest import as_resident

SIGNATURE = "miravejaPersona"


def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return root


def track(root: Path, *paths: Path) -> None:
    subprocess.run(["git", "add", "-f", *map(str, paths)], cwd=root, check=True)


def guard_in(root: Path, monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.chdir(root)
    return main(["guard"])


def test_synthetic_examples_pass(
    tmp_path: Path, examples: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repo(tmp_path)
    for path in examples.glob("*.yaml"):
        shutil.copy(path, root / path.name)
    track(root, *root.glob("*.yaml"))
    assert guard_in(root, monkeypatch) == 0


def test_resident_definition_is_blocked(
    tmp_path: Path, examples: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repo(tmp_path)
    track(root, as_resident(examples / "pellam-quist.persona.yaml", root / "p.persona.yaml"))
    assert guard_in(root, monkeypatch) == 1


@pytest.mark.parametrize("nature", [None, "unknown"])
def test_unmarked_or_unknown_marking_is_blocked(
    tmp_path: Path, examples: Path, monkeypatch: pytest.MonkeyPatch, nature: str | None
) -> None:
    root = repo(tmp_path)
    text = (examples / "pellam-quist.persona.yaml").read_text(encoding="utf-8")
    replacement = "" if nature is None else f"nature: {nature}"
    path = root / "definitions/renamed.yaml"
    path.parent.mkdir()
    path.write_text(text.replace("nature: synthetic", replacement), encoding="utf-8")
    track(root, path)
    assert guard_in(root, monkeypatch) == 1


def test_resident_author_note_is_blocked(
    tmp_path: Path, examples: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repo(tmp_path)
    track(root, as_resident(examples / "lighthouse-mural.note.yaml", root / "x.note.yaml"))
    assert guard_in(root, monkeypatch) == 1


def test_named_files_must_be_synthetic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repo(tmp_path)
    (root / "empty.persona.yaml").write_text("just: text\n")
    (root / "broken.note.yaml").write_text("a: [unclosed\n")
    track(root, root / "empty.persona.yaml", root / "broken.note.yaml")
    assert guard_in(root, monkeypatch) == 1


def test_vault_marker_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repo(tmp_path)
    (root / "nested").mkdir()
    (root / "nested/.cofrealma").write_text("")
    track(root, root / "nested/.cofrealma")
    assert guard_in(root, monkeypatch) == 1


def test_pasted_fragment_in_markdown_is_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repo(tmp_path)
    notes = root / "notes.md"
    notes.write_text(f"# Draft\n\n```yaml\n{SIGNATURE}: 1\nidentity:\n  about: x\n```\n")
    track(root, notes)
    assert guard_in(root, monkeypatch) == 1


def test_pasted_synthetic_fragment_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = repo(tmp_path)
    notes = root / "notes.md"
    notes.write_text(f"```yaml\n{SIGNATURE}: 1\nnature: synthetic\n```\n")
    track(root, notes)
    assert guard_in(root, monkeypatch) == 0


def test_untracked_files_are_ignored_by_default(
    tmp_path: Path, examples: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = repo(tmp_path)
    as_resident(examples / "pellam-quist.persona.yaml", root / "untracked.persona.yaml")
    assert guard_in(root, monkeypatch) == 0


def test_explicit_paths_are_scanned(tmp_path: Path, examples: Path) -> None:
    folder = tmp_path / "folder"
    as_resident(examples / "pellam-quist.persona.yaml", folder / "a.persona.yaml")
    assert main(["guard", str(folder)]) == 1
    assert main(["guard", str(examples)]) == 0


def test_missing_path_is_a_usage_error(tmp_path: Path) -> None:
    assert main(["guard", str(tmp_path / "nope")]) == 2
