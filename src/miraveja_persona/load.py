"""Loading a definition for a runtime (R-10).

Two entry points, so a synthetic persona can never be brought to life as a resident by
passing a flag. Refusals carry a reason code and never any prose from the file.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .check import check_document
from .findings import Finding
from .model import Definition
from .validate import SUPPORTED_VERSIONS, document_kind
from .yamlio import Document, YamlProblem, read_document


class DefinitionRefused(Exception):
    """A definition the runtime must not use.

    `reason` is one of the codes in contracts/cli.md. The message never contains prose
    from the file; `findings` does, so a runtime must never log it.
    """

    def __init__(self, reason: str, detail: str = "", findings: Sequence[Finding] = ()) -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.findings = tuple(findings)


def _read(path: Path) -> Document:
    try:
        doc = read_document(path)
    except YamlProblem as problem:
        raise DefinitionRefused(
            "invalid", f"not one safe YAML document (line {problem.line})"
        ) from None
    kind = document_kind(doc.data)
    if kind == "author-note":
        raise DefinitionRefused("author_note", "no runtime may read an author's note")
    if kind is None:
        raise DefinitionRefused("invalid", "not a persona definition")
    if doc.data.get("miravejaPersona") not in SUPPORTED_VERSIONS:
        supported = ", ".join(str(v) for v in SUPPORTED_VERSIONS)
        raise DefinitionRefused("unsupported_version", f"supported: {supported}")
    return doc


def _validated(doc: Document) -> Definition:
    certain = [f for f in check_document(doc) if f.certainty == "certain"]
    if certain:
        raise DefinitionRefused("invalid", f"{len(certain)} certain findings", certain)
    return Definition.model_validate(doc.data)


def load_synthetic(path: Path | str) -> Definition:
    """A synthetic persona, for tests and examples."""
    doc = _read(Path(path))
    if doc.data.get("nature") != "synthetic":
        raise DefinitionRefused("resident_outside_studio", "use load_resident inside the vault")
    return _validated(doc)


def load_resident(path: Path | str, cofrealma_root: Path | str) -> Definition:
    """A born resident persona, from inside the marked vault on the Studio."""
    from .vault import MARKER, ledger_entry, sha256

    path, root = Path(path).resolve(), Path(cofrealma_root).resolve()
    doc = _read(path)
    if doc.data.get("nature") != "resident":
        raise DefinitionRefused("synthetic_as_resident", "use load_synthetic for tests")
    if not (root / MARKER).is_file() or not path.is_relative_to(root):
        raise DefinitionRefused("outside_vault", "resident definitions load only from the vault")
    identity = doc.data.get("identity")
    persona_id = identity.get("id") if isinstance(identity, dict) else None
    entry = ledger_entry(root, persona_id) if isinstance(persona_id, str) else None
    if entry is None:
        raise DefinitionRefused("not_born", "no birth ledger entry; run freeze first")
    if entry.get("sha256") != sha256(path):
        raise DefinitionRefused("changed_since_birth", "the file differs from its frozen copy")
    return _validated(doc)
