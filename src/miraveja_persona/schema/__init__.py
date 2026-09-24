"""Bundled copies of the hub's schemas (R-3)."""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any, Literal

FILES = {
    "persona": "persona-definition-v1.schema.json",
    "author-note": "author-note-v1.schema.json",
}


@cache
def load_schema(kind: Literal["persona", "author-note"]) -> dict[str, Any]:
    text = resources.files(__name__).joinpath(FILES[kind]).read_text(encoding="utf-8")
    schema: dict[str, Any] = json.loads(text)
    return schema
