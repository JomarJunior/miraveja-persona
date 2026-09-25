"""The public-repository guard (R-9).

Blocks any persona definition, author's note or vault marker not marked synthetic. It
prints the file, the line and the reason, and never a word of the content it blocks.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .check import Unreadable
from .vault import MARKER
from .yamlio import YamlProblem, parse_text

SIGNATURES = ("miravejaPersona", "miravejaAuthorNote")
NAMED = (".persona.yaml", ".note.yaml")
LOOKAHEAD = 15


@dataclass(frozen=True)
class Blocked:
    file: str
    line: int
    reason: str

    def render(self) -> str:
        return f"{self.file}:{self.line}  blocked  {self.reason}"


def _tracked() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        raise Unreadable("not a git repository; pass the paths to scan") from None
    return [Path(p) for p in out.decode("utf-8", "replace").split("\0") if p]


def _expand(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files += sorted(p for p in path.rglob("*") if p.is_file() and ".git" not in p.parts)
        elif path.is_file() or path.name == MARKER:
            files.append(path)
        else:
            raise Unreadable(f"{path}: no such file or folder")
    return files


def _text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    return raw.decode("utf-8", "replace")


def _yaml_verdict(path: Path, text: str) -> Blocked | bool | None:
    """For YAML files: a Blocked, None if allowed, or False if not a persona document."""
    try:
        doc = parse_text(text, path)
    except YamlProblem as problem:
        if path.name.endswith(NAMED):
            return Blocked(str(path), max(problem.line, 1), "unreadable persona file")
        return False
    data = doc.data
    signed = isinstance(data, dict) and any(key in data for key in SIGNATURES)
    if not signed:
        if path.name.endswith(NAMED):
            return Blocked(str(path), 1, "persona file without a recognized signature")
        return False
    assert isinstance(data, dict)
    if data.get("nature") == "synthetic":
        return None
    kind = "author's note" if "miravejaAuthorNote" in data else "persona definition"
    line = doc.lines.get("/nature", 1)
    return Blocked(str(path), line, f"{kind} not marked synthetic")


def _fragments(path: Path, text: str) -> list[Blocked]:
    lines = text.splitlines()
    blocked = []
    for i, line in enumerate(lines):
        if line.lstrip().startswith(tuple(f"{s}:" for s in SIGNATURES)):
            window = lines[i + 1 : i + 1 + LOOKAHEAD]
            if not any(w.strip() == "nature: synthetic" for w in window):
                blocked.append(Blocked(str(path), i + 1, "pasted persona fragment"))
    return blocked


def check_file(path: Path) -> list[Blocked]:
    if path.name == MARKER:
        return [Blocked(str(path), 1, "vault marker")]
    text = _text(path)
    if text is None:
        if path.name.endswith(NAMED):
            return [Blocked(str(path), 1, "unreadable persona file")]
        return []
    if path.suffix in (".yaml", ".yml"):
        verdict = _yaml_verdict(path, text)
        if verdict is None:
            return []
        if isinstance(verdict, Blocked):
            return [verdict]
    return _fragments(path, text)


def guard(paths: list[Path]) -> list[Blocked]:
    files = _expand(paths) if paths else _tracked()
    return [b for path in files for b in check_file(path)]
