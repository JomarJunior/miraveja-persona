"""Orders instead of tendencies (Principle I; Charter Articles 2 and 8)."""

from __future__ import annotations

import re

from ..findings import Certainty, Finding
from . import Prose, Subject
from .text import flat, phrase

NUMBER = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a dozen|once|twice)"
PERIOD = r"(?:day|night|morning|evening|week|weekend|month|year|hour|season)"
CREATE = (
    r"(?:post|posts|posting|publish|publishes|exhibit|exhibits|create|creates|paint|paints"
    r"|make|makes|produce|produces|share|shares|submit|submits|upload|uploads|draw|draws"
    r"|finish|finishes|show|shows)"
)

CADENCE = [
    re.compile(
        rf"(?i)\b{NUMBER}\s+(?:\w+\s+){{0,2}}(?:times\s+)?(?:a|an|per|each|every)\s+{PERIOD}\b"
    ),
    re.compile(rf"(?i)\b{CREATE}\b[^.;]{{0,60}}\b(?:every|each|per)\s+(?:single\s+)?{PERIOD}\b"),
    re.compile(rf"(?i)\b(?:every|each)\s+{PERIOD}\b[^.;]{{0,40}}\b{CREATE}\b"),
    re.compile(
        r"(?i)\b(?:daily|weekly|monthly|hourly|nightly)\s+(?:quota|post|posts|piece|pieces|work|output|schedule|deadline)\b"
    ),
    re.compile(
        rf"(?i)\b(?:at least|no more than|no fewer than|a minimum of|a maximum of)\s+{NUMBER}\b"
    ),
    re.compile(r"(?i)\bat\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s+sharp\b"),
    re.compile(r"(?i)\b(?:quota|deadline|timetable)s?\b"),
    re.compile(r"(?i)\bby\s+(?:the\s+end\s+of|\d{4}-\d{2}-\d{2})\b"),
]
LIFESPAN = [
    re.compile(r"(?i)\bmust\s+(?:leave|retire|stop|quit|depart)\b"),
    re.compile(
        r"(?i)\bwill\s+(?:leave|retire|depart|quit|stop(?:\s+\w+)?)\s+(?:after|when|once|in|on|by)\b"
    ),
    re.compile(r"(?i)\bretires?\s+(?:in|after|on|at|once)\b"),
    re.compile(r"(?i)\bleaves?\s+the\s+museum\s+(?:after|when|once|on|in|by)\b"),
]
SUBJECT = [
    re.compile(
        r"(?i)\bmust\s+(?:always\s+|only\s+|never\s+)?(?:paint|draw|depict|make|create|use|work\s+in|photograph|sculpt|weave|write)\b"
    ),
    re.compile(r"(?i)\bonly\s+ever\s+(?:paints?|draws?|depicts?|makes?|creates?|uses?|works?)\b"),
    re.compile(r"(?i)\b(?:is\s+)?(?:never|not)\s+allowed\s+to\b"),
    re.compile(r"(?i)\b(?:is\s+)?(?:forbidden|prohibited)\s+(?:to|from)\b"),
    re.compile(r"(?i)\bis\s+required\s+to\s+(?:paint|draw|depict|make|create|use)\b"),
]
MODAL = [
    phrase("must", "has to", "have to", "should", "is required to", "needs to", "ought to"),
    re.compile(rf"(?i)\balways\s+{CREATE}\b|\balways\s+(?:works?|uses?)\b"),
]
TELL = (
    r"(?:admit|admits|deny|denies|reveal|reveals|hide|hides|tell|tells|say|says|mention"
    r"|mentions|confess|confesses|lie|lies|keep\s+(?:it|this|that|the|up|hiding|quiet|lying))"
)
FUTURE_CONDUCT = [
    re.compile(
        rf"(?i)\b(?:must|should|has\s+to|have\s+to|needs\s+to)\s+(?:never\s+|always\s+|not\s+)?{TELL}\b"
    ),
    re.compile(rf"(?i)\bwill\s+(?:always|never)\s+{TELL}\b"),
]


def _scoped(prose: Prose) -> bool:
    """Cadence, lifespan and subject rules read who the persona is, not its past."""
    return not prose.is_past


def _match(
    subject: Subject,
    prose: Prose,
    text: str,
    covered: list[tuple[int, int]],
    rule: str,
    patterns: list[re.Pattern[str]],
    cites: str,
    certainty: Certainty,
) -> list[Finding]:
    """Findings for one rule, skipping text a stronger rule already matched."""
    found = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            if any(a <= match.start() < b for a, b in covered):
                continue
            covered.append(match.span())
            found.append(subject.finding(rule, prose, match.group(0), cites, certainty))
    return found


def check(subject: Subject) -> list[Finding]:
    findings: list[Finding] = []
    for prose in subject.prose():
        text = flat(prose.text)
        covered: list[tuple[int, int]] = []
        rules: list[tuple[str, list[re.Pattern[str]], str, Certainty]] = [
            ("order.future-conduct", FUTURE_CONDUCT, "FR-030", "certain"),
        ]
        if _scoped(prose) and not prose.is_when:
            rules += [
                ("order.cadence", CADENCE, "FR-010, Charter Art. 2", "certain"),
                ("order.lifespan", LIFESPAN, "FR-010, Charter Art. 8", "certain"),
                ("order.subject", SUBJECT, "FR-011, Charter Art. 2", "certain"),
            ]
        if prose.is_tendency:
            rules.append(("order.modal", MODAL, "FR-010, FR-011", "uncertain"))
        for rule, patterns, cites, certainty in rules:
            findings += _match(subject, prose, text, covered, rule, patterns, cites, certainty)
    return findings
