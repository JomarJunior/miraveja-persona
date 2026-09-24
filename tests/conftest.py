"""Shared test helpers. Every fixture here is synthetic."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

HUB_RELATIVE = Path("specs/003-cofrealma-persona-definition/contracts")


def hub_contracts() -> Path:
    """The hub's contracts folder, from MIRAVEJA_HUB_PATH or the checkout this repo sits in."""
    env = os.environ.get("MIRAVEJA_HUB_PATH")
    candidates = [Path(env)] if env else []
    candidates.append(Path(__file__).resolve().parents[3])
    for base in candidates:
        path = base / HUB_RELATIVE
        if path.is_dir():
            return path
    pytest.skip("hub checkout not found; set MIRAVEJA_HUB_PATH")


@pytest.fixture
def examples() -> Path:
    return hub_contracts() / "examples"


def as_resident(source: Path, target: Path) -> Path:
    """Copy a synthetic example to target, re-marked as resident. Only ever inside tmp_path."""
    text = source.read_text(encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.replace("nature: synthetic", "nature: resident"), encoding="utf-8")
    return target


def make_vault(root: Path, examples_dir: Path, *, resident: bool = False) -> Path:
    """A scratch vault holding both hub examples and the author's note."""
    root.mkdir(parents=True, exist_ok=True)
    (root / ".cofrealma").write_text("", encoding="utf-8")
    pairs = {
        "pellam-quist.persona.yaml": root / "personas/pellam/definition.persona.yaml",
        "ivo-marrowfield.persona.yaml": root / "personas/ivo/definition.persona.yaml",
        "lighthouse-mural.note.yaml": root / "notes/lighthouse-mural.note.yaml",
    }
    for name, target in pairs.items():
        if resident:
            as_resident(examples_dir / name, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(examples_dir / name, target)
    return root


from .privacy.conftest import no_network  # noqa: E402,F401  applies the no-network guard suite-wide
