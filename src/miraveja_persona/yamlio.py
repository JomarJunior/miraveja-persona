"""Safe reading of exactly one YAML document, with line numbers per field.

Anchors, aliases, explicit tags, duplicate keys and multiple documents are refused.
Scalars stay strings except the integers, booleans and nulls the schemas need,
so a date or a number-shaped value in prose is never silently converted.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.events import AliasEvent, DocumentStartEvent
from ruamel.yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

INT_TAG = "tag:yaml.org,2002:int"
BOOL_TAG = "tag:yaml.org,2002:bool"
NULL_TAG = "tag:yaml.org,2002:null"


class YamlProblem(Exception):
    """The file is not one safe YAML document. Carries a line, never file content."""

    def __init__(self, message: str, line: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.line = line


@dataclass(frozen=True)
class Document:
    path: Path
    data: Any
    lines: dict[str, int] = field(default_factory=dict)

    def line_of(self, pointer: str) -> int:
        """The line of a JSON Pointer, falling back to its nearest known parent."""
        while pointer:
            if pointer in self.lines:
                return self.lines[pointer]
            pointer = pointer.rsplit("/", 1)[0]
        return self.lines.get("", 1)


def escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _check_events(text: str) -> None:
    documents = 0
    for event in YAML(typ="rt").parse(io.StringIO(text)):
        line = event.start_mark.line + 1 if event.start_mark else 0
        if isinstance(event, DocumentStartEvent):
            documents += 1
            if documents > 1:
                raise YamlProblem("more than one YAML document", line)
        if isinstance(event, AliasEvent):
            raise YamlProblem("aliases are not allowed", line)
        if getattr(event, "anchor", None):
            raise YamlProblem("anchors are not allowed", line)
        if getattr(event, "tag", None):
            raise YamlProblem("explicit tags are not allowed", line)


def _convert(node: Node, pointer: str, lines: dict[str, int]) -> Any:
    lines[pointer] = node.start_mark.line + 1
    if isinstance(node, MappingNode):
        result: dict[str, Any] = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, ScalarNode):
                raise YamlProblem("mapping keys must be plain words", key_node.start_mark.line + 1)
            key = str(key_node.value)
            if key in result:
                raise YamlProblem(f"duplicate key '{key}'", key_node.start_mark.line + 1)
            result[key] = _convert(value_node, f"{pointer}/{escape(key)}", lines)
        return result
    if isinstance(node, SequenceNode):
        return [_convert(item, f"{pointer}/{i}", lines) for i, item in enumerate(node.value)]
    assert isinstance(node, ScalarNode)
    value = str(node.value)
    if node.style is None:
        if node.tag == INT_TAG:
            try:
                return int(value)
            except ValueError:
                return value
        if node.tag == BOOL_TAG and value in ("true", "false"):
            return value == "true"
        if node.tag == NULL_TAG:
            return None
    return value


def parse_text(text: str, path: Path) -> Document:
    try:
        _check_events(text)
        node = YAML(typ="rt").compose(io.StringIO(text))
    except YamlProblem:
        raise
    except YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        raise YamlProblem("not valid YAML", mark.line + 1 if mark else 0) from None
    if node is None:
        raise YamlProblem("the file is empty", 1)
    lines: dict[str, int] = {}
    data = _convert(node, "", lines)
    return Document(path=path, data=data, lines=lines)


def read_document(path: Path | str) -> Document:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raise YamlProblem("the file cannot be read as UTF-8 text", 0) from None
    return parse_text(text, path)
