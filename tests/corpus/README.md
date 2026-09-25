# The labeled corpus

Measures the rule catalog (SC-003, SC-007, SC-008). Every persona here is synthetic.

- `clean/` holds complete clean definitions. The check must report nothing on them, or at
  most one false finding each.
- Each family folder holds a `cases.yaml`: a `base` definition from `clean/`, then `cases`,
  each a `set` of JSON Pointer patches (a pointer ending in `/-` appends to a list) and the
  findings it must produce, as `rule` and `part`. A case with `expect: []` must pass.
- `tree_cases` build a scratch vault from several patched files and run the vault-wide
  checks; each expected finding names the `file` index it belongs to.

A seeded case passes when every expected finding is found. False findings are findings
that were not expected; no case may have more than one.
