# miraveja-persona

> Public format tools for **🖼️ MiraVeja** persona definitions: load, check, freeze and guard.

The format is public. Every resident persona stays private. This library is how both halves of that promise are kept: it reads and checks definitions written in the public format, and it stops any definition that is not marked synthetic from entering a public repository.

It is a generic library, not a museum component, so its name carries no brand emoji.

## What it does

| Command | Purpose |
|---|---|
| `miraveja-persona new --name "<public name>" [--synthetic]` | Write a scaffold for a new definition, with a fresh identifier and guidance for every part. |
| `miraveja-persona check PATH... [--tree ROOT]` | Check definitions and author's notes against the schema and the rule catalog. With `--tree`, also check the whole private vault. |
| `miraveja-persona decide FINGERPRINT --as accepted\|not-an-issue --by NAME` | Record a team member's decision on an uncertain finding. |
| `miraveja-persona pasts ROOT` | List every shared past in the vault. |
| `miraveja-persona freeze PATH --tree ROOT` | Record a definition's birth in the vault's ledger. |
| `miraveja-persona guard [PATH...]` | Block definitions, author's notes and vault markers in a public repository. Never prints their content. |

For the persona runtime:

```python
from miraveja_persona import load_resident, load_synthetic

definition = load_synthetic("pellam-quist.persona.yaml")
```

Nothing in this library opens a network connection.

## Where the rules live

The format, its schemas, the rule catalog and the synthetic examples are specified in the **🖼️ MiraVeja** hub, spec `003-cofrealma-persona-definition`:
<https://github.com/JomarJunior/miraveja-ecosystem/tree/main/specs/003-cofrealma-persona-definition>

The schemas bundled in `src/miraveja_persona/schema/` are copies of the hub's; CI fails if they drift.

## Development

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e . pytest ruff mypy types-jsonschema
MIRAVEJA_HUB_PATH=/path/to/miraveja-ecosystem .venv/bin/pytest
```

Every fixture is a synthetic persona. Resident-marked files are only ever created in temporary directories by the tests, never committed.

## License

Apache License 2.0.
