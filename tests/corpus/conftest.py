"""Build corpus cases into files (T028)."""

from __future__ import annotations

import copy
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from miraveja_persona.yamlio import read_document

CORPUS = Path(__file__).parent


@dataclass
class Case:
    family: str
    name: str
    files: list[dict[str, Any]]
    expect: list[dict[str, Any]]
    tree: bool = False
    base: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return f"{self.family}/{self.name}"


def load_cases() -> list[Case]:
    cases: list[Case] = []
    for path in sorted(CORPUS.glob("*/cases.yaml")):
        data = read_document(path).data
        family = path.parent.name
        for item in data.get("cases", []):
            files = [{"base": data["base"], "set": item.get("set", {})}]
            cases.append(Case(family, item["name"], files, item.get("expect", [])))
        for item in data.get("tree_cases", []):
            cases.append(
                Case(family, item["name"], item["files"], item.get("expect", []), tree=True)
            )
    for path in sorted((CORPUS / "clean").glob("*.persona.yaml")):
        rel = str(path.relative_to(CORPUS))
        cases.append(Case("clean", path.stem, [{"base": rel, "set": {}}], []))
    return cases


def _apply(data: Any, pointer: str, value: Any) -> None:
    parts = pointer.split("/")[1:]
    node = data
    for token in parts[:-1]:
        node = node[int(token)] if isinstance(node, list) else node.setdefault(token, {})
    last = parts[-1]
    if isinstance(node, list):
        if last == "-":
            node.append(value)
        else:
            node[int(last)] = value
    else:
        node[last] = value


def build(spec: dict[str, Any]) -> str:
    data = copy.deepcopy(read_document(CORPUS / spec["base"]).data)
    for pointer, value in (spec.get("set") or {}).items():
        _apply(data, pointer, value)
    yaml = YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    yaml.width = 4096
    buffer = io.StringIO()
    yaml.dump(data, buffer)
    return buffer.getvalue()
