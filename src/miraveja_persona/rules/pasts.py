"""Shared pasts hold facts, never feelings or motives (FR-026, FR-030)."""

from __future__ import annotations

import re

from ..findings import Finding
from . import Prose, Subject
from .text import flat, sentences

P = r"\{\d+\}"
FEELING_VERBS = (
    r"(?:resents?|resented|admires?|admired|loves?|loved|hates?|hated|envies|envied|envy"
    r"|despises?|despised|adores?|adored|idolizes?|idolized|fears?|feared|worships?|worshipped"
    r"|pities|pitied|misses|missed|trusts?|trusted|distrusts?|distrusted|likes|liked|dislikes?"
    r"|disliked|respects?|respected|forgives?|forgave|blames?|blamed|resent|admire|love|hate"
    r"|despise|adore|fear|trust|like|dislike|respect|blame|forgive"
    r"|is\s+jealous\s+of|was\s+jealous\s+of|is\s+envious\s+of|was\s+envious\s+of"
    r"|is\s+fond\s+of|was\s+fond\s+of|is\s+afraid\s+of|was\s+afraid\s+of|is\s+in\s+love\s+with"
    r"|was\s+in\s+love\s+with|fell\s+in\s+love\s+with|cannot\s+stand|can't\s+stand"
    r"|still\s+thinks\s+of|thinks\s+the\s+world\s+of|never\s+forgave|looks\s+up\s+to"
    r"|looked\s+up\s+to|is\s+proud\s+of|was\s+proud\s+of|is\s+ashamed\s+of|was\s+ashamed\s+of)"
)
FEELING = [
    re.compile(
        rf"(?i){P}\s+(?:still\s+|always\s+|secretly\s+|never\s+|deeply\s+|quietly\s+)?"
        rf"{FEELING_VERBS}\s+{P}"
    ),
    re.compile(
        r"(?i)\b(?:jealous|envious|resentful|ashamed|furious|heartbroken|humiliated"
        r"|in\s+love|infatuated|bitterly|spiteful|vengeful)\b"
    ),
]
MOTIVE = [
    re.compile(r"(?i)\bbecause\b"),
    re.compile(
        r"(?i)\bout\s+of\s+(?:jealousy|spite|pride|love|fear|envy|anger|kindness|pity"
        r"|revenge|shame|guilt|loyalty|resentment|respect|hatred)\b"
    ),
    re.compile(
        r"(?i)\bto\s+spite\b|\bfor\s+revenge\b|\bin\s+revenge\b|\bso\s+that\b"
        r"|\bin\s+order\s+to\b"
    ),
    re.compile(
        r"(?i)\bsince\b(?!\s+(?:then|that|the|this|childhood|last|early|before|after"
        r"|\d|[a-z]+\s+(?:day|year|summer|winter|spring|autumn)))"
    ),
]
AMBIGUOUS = re.compile(
    r"(?i)\b(?:close|closer|estranged|bitter|proud|fond|grudge|cold|warm"
    r"|inseparable|devoted|tender|lonely)\b"
)
UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def _applies(prose: Prose) -> bool:
    if prose.is_shared_past:
        return prose.pointer.endswith("/happened")
    return prose.pointer.startswith("/seedMemories/") and bool(UUID.search(prose.text))


def check(subject: Subject) -> list[Finding]:
    findings: list[Finding] = []
    for prose in subject.prose():
        if not _applies(prose):
            continue
        text = flat(prose.text)
        certain_spans: list[tuple[int, int]] = []
        for rule, patterns in (("past.feeling", FEELING), ("past.motive", MOTIVE)):
            for pattern in patterns:
                for match in pattern.finditer(text):
                    certain_spans.append(match.span())
                    findings.append(
                        subject.finding(rule, prose, match.group(0), "FR-026, FR-030", "certain")
                    )
        for sentence in sentences(prose.text):
            for match in AMBIGUOUS.finditer(sentence):
                findings.append(
                    subject.finding(
                        "past.feeling-ambiguous",
                        prose,
                        match.group(0),
                        "FR-026, FR-017",
                        "uncertain",
                    )
                )
    return findings
