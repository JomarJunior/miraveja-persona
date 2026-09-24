"""The rule catalog (contracts/check-rules.md). One module per rule family."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from ..findings import Certainty, Finding, make
from ..validate import Kind
from ..yamlio import Document

TENDENCY_PREFIXES = ("/tendencies/", "/taste/", "/voice/", "/craft")
# The prefixes of rule ids that apply to author's notes (FR-033).
NOTE_RULES = ("structure.", "hardline.", "metric.money", "forbidden.visitor", "forbidden.secret")


@dataclass(frozen=True)
class Prose:
    pointer: str
    text: str

    @property
    def is_when(self) -> bool:
        return self.pointer.endswith("/when")

    @property
    def is_tendency(self) -> bool:
        return self.pointer.startswith(TENDENCY_PREFIXES)

    @property
    def is_past(self) -> bool:
        return self.pointer.startswith(("/seedMemories/", "/sharedPasts/"))

    @property
    def is_shared_past(self) -> bool:
        return self.pointer.startswith("/sharedPasts/")


@dataclass(frozen=True)
class Subject:
    doc: Document
    kind: Kind
    allowed_names: frozenset[str] = field(default_factory=frozenset)

    @property
    def data(self) -> Any:
        return self.doc.data

    def prose(self) -> Iterator[Prose]:
        yield from iter_prose(self.data, self.kind)

    def finding(
        self, rule: str, where: Prose | str, quote: str, cites: str, certainty: Certainty
    ) -> Finding:
        pointer = where.pointer if isinstance(where, Prose) else where
        return make(
            file=self.doc.path,
            rule=rule,
            part=pointer,
            data=self.data,
            line=self.doc.line_of(pointer),
            quote=quote,
            cites=cites,
            certainty=certainty,
        )


def iter_prose(data: Any, kind: Kind) -> Iterator[Prose]:
    if kind == "author-note":
        if isinstance(data.get("truth"), str):
            yield Prose("/truth", data["truth"])
        return
    identity = data.get("identity", {})
    for key in ("about", "selfUnderstanding"):
        if isinstance(identity.get(key), str):
            yield Prose(f"/identity/{key}", identity[key])
    for section, keys in (
        ("taste", ("drawnTo", "stylesAndMedia", "dislikes")),
        ("voice", ("speech", "temperament")),
        ("tendencies", ("presence", "work")),
    ):
        part = data.get(section, {})
        for key in keys:
            if isinstance(part.get(key), str):
                yield Prose(f"/{section}/{key}", part[key])
    for i, theme in enumerate(data.get("taste", {}).get("themes", [])):
        if isinstance(theme, str):
            yield Prose(f"/taste/themes/{i}", theme)
    for i, care in enumerate(data.get("cares", [])):
        if isinstance(care, str):
            yield Prose(f"/cares/{i}", care)
    for key in ("craft", "selfImage"):
        if isinstance(data.get(key), str):
            yield Prose(f"/{key}", data[key])
    for list_name in ("seedMemories", "sharedPasts"):
        for i, item in enumerate(data.get(list_name, [])):
            for key in ("when", "happened"):
                if isinstance(item, dict) and isinstance(item.get(key), str):
                    yield Prose(f"/{list_name}/{i}/{key}", item[key])


RuleFn = Callable[[Subject], list[Finding]]


def all_rules() -> list[RuleFn]:
    from . import forbidden, hardlines, metrics, openly_ai, orders, pasts

    return [
        orders.check,
        metrics.check,
        hardlines.check,
        openly_ai.check,
        pasts.check,
        forbidden.check,
    ]


def applies_to(rule_id: str, kind: Kind) -> bool:
    return kind == "persona" or rule_id.startswith(NOTE_RULES)
