"""The bundled schemas never drift from the hub's (R-3)."""

from __future__ import annotations

from importlib import resources

from jsonschema import Draft202012Validator

from miraveja_persona.schema import load_schema
from miraveja_persona.yamlio import read_document

from .conftest import hub_contracts

NAMES = ["persona-definition-v1.schema.json", "author-note-v1.schema.json"]


def test_bundled_schemas_match_the_hub() -> None:
    hub = hub_contracts()
    for name in NAMES:
        bundled = resources.files("miraveja_persona.schema").joinpath(name).read_bytes()
        assert bundled == (hub / name).read_bytes(), f"{name} differs from the hub copy"


def test_hub_examples_validate_against_bundled_schemas() -> None:
    examples = hub_contracts() / "examples"
    for path in sorted(examples.glob("*.yaml")):
        doc = read_document(path)
        schema = load_schema("author-note" if "miravejaAuthorNote" in doc.data else "persona")
        errors = list(Draft202012Validator(schema).iter_errors(doc.data))
        assert not errors, (path.name, [e.message for e in errors])
