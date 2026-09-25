"""Shared pasts across definitions (R-7): the cross-definition checks and the listing."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .check import FileReport, check_file
from .findings import Finding, make

FIELDS = ("participants", "when", "happened")


@dataclass(frozen=True)
class Entry:
    report: FileReport
    index: int
    past: dict[str, Any]

    @property
    def data(self) -> Any:
        assert self.report.doc is not None
        return self.report.doc.data

    def finding(self, rule: str, part: str, quote: str, cites: str, certain: bool) -> Finding:
        assert self.report.doc is not None
        pointer = f"/sharedPasts/{self.index}{part}"
        return make(
            file=self.report.path,
            rule=rule,
            part=pointer,
            data=self.data,
            line=self.report.doc.line_of(pointer),
            quote=quote,
            cites=cites,
            certainty="certain" if certain else "uncertain",
        )


def _normal(value: Any) -> Any:
    return re.sub(r"\s+", " ", value).strip() if isinstance(value, str) else value


def _entries(reports: list[FileReport]) -> tuple[dict[str, FileReport], dict[str, list[Entry]]]:
    by_id: dict[str, FileReport] = {}
    stories: dict[str, list[Entry]] = {}
    for report in reports:
        if report.kind != "persona" or not report.valid_structure or report.doc is None:
            continue
        data = report.doc.data
        by_id[data["identity"]["id"]] = report
        for i, past in enumerate(data.get("sharedPasts", [])):
            stories.setdefault(past["story"], []).append(Entry(report, i, past))
    return by_id, stories


def cross_definition_findings(reports: list[FileReport]) -> list[Finding]:
    by_id, stories = _entries(reports)
    names = {pid: r.doc.data["identity"]["publicName"] for pid, r in by_id.items() if r.doc}
    findings: list[Finding] = []
    for story, entries in stories.items():
        for entry in entries:
            own = entry.data["identity"]["id"]
            for j, pid in enumerate(entry.past["participants"]):
                if pid not in by_id:
                    findings.append(
                        entry.finding(
                            "past.unknown-participant",
                            f"/participants/{j}",
                            f"no definition has identifier {pid}",
                            "FR-027",
                            True,
                        )
                    )
                elif pid != own and names.get(pid, "\0") in entry.past["happened"]:
                    findings.append(
                        entry.finding(
                            "structure.placeholder",
                            "/happened",
                            f"names a participant by public name instead of {{{j + 1}}}",
                            "FR-027",
                            True,
                        )
                    )
        if len(entries) < 2:
            continue
        tellings = {e.past["telling"] for e in entries}
        if len(tellings) > 1:
            for entry in entries:
                findings.append(
                    entry.finding(
                        "past.telling-mismatch",
                        "/telling",
                        f"story {story} is marked both agreed and intended-difference",
                        "FR-029",
                        True,
                    )
                )
            continue
        if tellings == {"intended-difference"}:
            continue
        differing = [
            f for f in FIELDS if len({json.dumps(_normal(e.past[f])) for e in entries}) > 1
        ]
        if differing:
            for entry in entries:
                findings.append(
                    entry.finding(
                        "past.possible-mistake",
                        f"/{differing[0]}",
                        f"story {story}: {', '.join(differing)} differ between definitions; "
                        "mark intended-difference if this is on purpose",
                        "FR-029",
                        False,
                    )
                )
    return findings


def list_pasts(root: Path) -> list[dict[str, Any]]:
    """Every shared past in the vault, as the baseline for spec 007 (FR-028)."""
    from .vault import vault_files

    reports = [check_file(p) for p in vault_files(root.resolve())]
    by_id, stories = _entries(reports)
    names = {pid: r.doc.data["identity"]["publicName"] for pid, r in by_id.items() if r.doc}
    root = root.resolve()
    listing = []
    for story in sorted(stories):
        entries = stories[story]
        tellings = {e.past["telling"] for e in entries}
        if len(entries) == 1:
            kind = "one-sided"
        elif len(tellings) > 1:
            kind = "mixed"
        elif tellings == {"intended-difference"}:
            kind = "intended-difference"
        else:
            kind = "agreed"
        versions: list[dict[str, Any]] = []
        for entry in entries:
            version = {
                "definition": str(entry.report.path.relative_to(root)),
                "toldBy": names.get(entry.data["identity"]["id"], "?"),
                "when": _normal(entry.past["when"]),
                "happened": _normal(entry.past["happened"]),
            }
            if not any(
                v["when"] == version["when"] and v["happened"] == version["happened"]
                for v in versions
            ):
                versions.append(version)
        participants = []
        for pid in dict.fromkeys(p for e in entries for p in e.past["participants"]):
            participants.append({"id": pid, "publicName": names.get(pid)})
        listing.append(
            {"story": story, "telling": kind, "participants": participants, "versions": versions}
        )
    return listing


def render(stories: list[dict[str, Any]], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(stories, indent=2, ensure_ascii=False)
    if not stories:
        return "no shared pasts"
    blocks = []
    for s in stories:
        people = ", ".join(f"{p['publicName'] or 'unknown'} ({p['id']})" for p in s["participants"])
        lines = [f"{s['story']}  [{s['telling']}]", f"  participants: {people}"]
        for v in s["versions"]:
            lines.append(f"  told by {v['toldBy']} ({v['definition']}), {v['when']}:")
            lines.append(f"    {v['happened']}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
