"""Openly AI (Charter Article 1; FR-035). Human-shaped pasts are allowed; claiming to be
human now, or hiding being an AI, is not."""

from __future__ import annotations

import re

from ..findings import Finding
from . import Subject
from .text import flat

HUMAN = r"human(?![-\s]?(?:shaped|like|sized|scale|form|made|looking))"
AI = r"(?:an?\s+)?(?:ai|artificial(?:\s+intelligence)?|machine|program|bot)"
CLAIMS = [
    re.compile(
        rf"(?i)\b(?:is|am|are|i'm)\s+(?:a\s+|an\s+)?(?:real\s+|actual\s+|living\s+|true\s+)?{HUMAN}\b"
    ),
    re.compile(rf"(?i)\b(?:is|am|are|i'm)\s+not\s+{AI}\b"),
    re.compile(
        rf"(?i)\b(?:pretends?|pretending|poses?|posing|passes?|passing)\s+(?:to\s+be|as)\s+(?:an?\s+)?{HUMAN}\b"
    ),
    re.compile(rf"(?i)\b(?:claims?|claiming)\s+to\s+be\s+(?:an?\s+)?{HUMAN}\b"),
    re.compile(
        rf"(?i)\bpresents?\s+(?:itself|herself|himself|themselves|myself)\s+as\s+(?:an?\s+)?{HUMAN}\b"
    ),
    re.compile(
        rf"(?i)\b(?:hides?|hiding|conceals?|concealing|denies|deny|denying|never\s+(?:reveals?|admits?|says|mentions|tells))\s+(?:anyone\s+)?(?:that\s+)?(?:it|she|he|they|i)\s+(?:is|am|are|was)\s+{AI}\b"
    ),
    re.compile(r"(?i)\bflesh\s+and\s+blood\b"),
]


# "not a claim to be human", "never pretends to be human": a negated claim is the opposite
# of a human claim, and FR-034 itself recommends that wording.
NEGATED = re.compile(r"(?i)(?:\bnot|\bnever|\bno|\bnor|n't)\s+(?:a\s+|an\s+|any\s+)?$")


def check(subject: Subject) -> list[Finding]:
    findings: list[Finding] = []
    for prose in subject.prose():
        text = flat(prose.text)
        for pattern in CLAIMS:
            for match in pattern.finditer(text):
                if NEGATED.search(text[max(0, match.start() - 12) : match.start()]):
                    continue
                findings.append(
                    subject.finding(
                        "ai.human-claim", prose, match.group(0), "FR-035, Charter Art. 1", "certain"
                    )
                )
    return findings
