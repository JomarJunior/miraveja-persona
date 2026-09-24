"""Decisions on uncertain findings, kept beside each definition (R-6). Filled in by US3."""

from __future__ import annotations

from pathlib import Path

from .findings import Finding


def apply_decisions(findings: list[Finding]) -> tuple[list[Finding], list[str]]:
    return findings, []


def decide(fingerprint: str, decision: str, by: str, tree: Path | None) -> tuple[bool, str]:
    return False, f"no current finding has fingerprint {fingerprint}"
