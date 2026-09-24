"""A stand-in runtime starts a persona from its definition alone (T027, SC-002)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from miraveja_persona import Definition, load_synthetic
from miraveja_persona.yamlio import read_document


class StandInRuntime:
    """Everything it knows about a persona comes from the definition it is given."""

    def __init__(self, definition: Definition) -> None:
        dumped = definition.model_dump(mode="json", by_alias=True, exclude_none=True)
        self.state: dict[str, Any] = dumped

    def introduce(self) -> str:
        identity = self.state["identity"]
        return f"{identity['publicName']}: {identity['about'].strip()}"


def test_every_field_reaches_the_runtime(examples: Path) -> None:
    for name in ("pellam-quist.persona.yaml", "ivo-marrowfield.persona.yaml"):
        path = examples / name
        runtime = StandInRuntime(load_synthetic(path))
        assert runtime.state == read_document(path).data


def test_swapping_definitions_changes_only_data(examples: Path) -> None:
    pellam = StandInRuntime(load_synthetic(examples / "pellam-quist.persona.yaml"))
    ivo = StandInRuntime(load_synthetic(examples / "ivo-marrowfield.persona.yaml"))
    assert type(pellam) is type(ivo)
    assert pellam.introduce().startswith("Pellam Quist")
    assert ivo.introduce().startswith("Ivo Marrowfield")
