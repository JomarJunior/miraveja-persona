"""The private vault: whole-tree checks, the birth ledger and freezing (R-8)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .check import check_file
from .findings import Finding


@dataclass
class CheckResult:
    findings: list[Finding] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)


def check_paths(paths: list[Path], tree: Path | None = None) -> CheckResult:
    findings: list[Finding] = []
    for path in paths:
        findings.extend(check_file(path).findings)
    return CheckResult(findings)
