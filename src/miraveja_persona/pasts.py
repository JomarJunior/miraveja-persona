"""Shared pasts across definitions (R-7). Filled in by US3."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .check import FileReport
from .findings import Finding


def cross_definition_findings(reports: list[FileReport]) -> list[Finding]:
    return []


def list_pasts(root: Path) -> list[dict[str, Any]]:
    return []


def render(stories: list[dict[str, Any]], fmt: str) -> str:
    return ""
