"""Findings: what the check reports, and how it prints them."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Literal

Certainty = Literal["certain", "uncertain"]

# Lists whose items carry a stable key, so reordering never breaks a decision (R-6).
KEYED_LISTS = {"seedMemories": "id", "sharedPasts": "story"}


@dataclass(frozen=True)
class Finding:
    file: str
    rule: str
    part: str
    key: str
    line: int
    quote: str
    cites: str
    certainty: Certainty
    decided: str | None = None

    @property
    def fingerprint(self) -> str:
        digest = hashlib.sha256(self.quote.encode("utf-8")).hexdigest()[:8]
        return f"{self.rule}:{self.key}:{digest}"

    def with_decision(self, decision: str) -> Finding:
        return replace(self, decided=decision)


def stable_key(pointer: str, data: Any) -> str:
    """`/sharedPasts/0/happened` becomes `/sharedPasts[junior-regatta]/happened`."""
    if not pointer:
        return ""
    out: list[str] = []
    node = data
    parts = pointer.split("/")[1:]
    i = 0
    while i < len(parts):
        token = parts[i]
        field = KEYED_LISTS.get(token)
        child = node.get(token) if isinstance(node, dict) else None
        if field and isinstance(child, list) and i + 1 < len(parts) and parts[i + 1].isdigit():
            index = int(parts[i + 1])
            item = child[index] if index < len(child) else None
            label = item.get(field) if isinstance(item, dict) else None
            out.append(f"/{token}[{label if isinstance(label, str) else index}]")
            node = item
            i += 2
            continue
        out.append(f"/{token}")
        if isinstance(node, dict):
            node = node.get(token)
        elif isinstance(node, list) and token.isdigit() and int(token) < len(node):
            node = node[int(token)]
        else:
            node = None
        i += 1
    return "".join(out)


def make(
    *,
    file: Path | str,
    rule: str,
    part: str,
    data: Any,
    line: int,
    quote: str,
    cites: str,
    certainty: Certainty,
) -> Finding:
    return Finding(
        file=str(file),
        rule=rule,
        part=part or "/",
        key=stable_key(part, data) or "/",
        line=line,
        quote=quote.strip(),
        cites=cites,
        certainty=certainty,
    )


def render_text(findings: list[Finding]) -> str:
    blocks = []
    for f in findings:
        state = f"{f.certainty}, decided {f.decided}" if f.decided else f.certainty
        blocks.append(
            f"{f.file}:{f.line}  {state}  {f.rule}  {f.part}\n"
            f'    "{f.quote}"\n'
            f"    breaks {f.cites}   fingerprint {f.fingerprint}"
        )
    return "\n".join(blocks)


def render_json(findings: list[Finding]) -> str:
    rows: list[dict[str, Any]] = []
    for f in findings:
        row = asdict(f)
        row["fingerprint"] = f.fingerprint
        rows.append(row)
    return json.dumps(rows, indent=2, ensure_ascii=False)
