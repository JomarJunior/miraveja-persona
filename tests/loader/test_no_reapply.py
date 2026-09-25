"""Nothing can pull a living persona back toward its definition (T056, US5, FR-018)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import miraveja_persona
from miraveja_persona import model
from miraveja_persona.model import Definition

FORBIDDEN = re.compile(r"(?i)(update|merge|reload|reapply|re_apply|diff|compare|restore|reset)")


def own_methods(cls: type) -> set[str]:
    names: set[str] = set()
    for klass in cls.__mro__:
        if klass.__module__ == model.__name__:
            names |= {n for n, v in vars(klass).items() if callable(v) and not n.startswith("__")}
    return names


@pytest.mark.parametrize(
    "cls",
    [c for c in vars(model).values() if isinstance(c, type) and c.__module__ == model.__name__],
)
def test_models_define_no_reapplying_method(cls: type) -> None:
    assert not {n for n in own_methods(cls) if FORBIDDEN.search(n)}


def test_public_api_has_nothing_that_compares_a_persona_to_its_definition() -> None:
    assert not [n for n in miraveja_persona.__all__ if FORBIDDEN.search(n)]


def test_definition_is_frozen(examples: Path) -> None:
    definition = miraveja_persona.load_synthetic(examples / "pellam-quist.persona.yaml")
    assert Definition.model_config.get("frozen") is True
    with pytest.raises(Exception):  # noqa: B017  pydantic's frozen-instance error
        definition.nature = "resident"  # type: ignore[misc]
