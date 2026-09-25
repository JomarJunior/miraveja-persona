"""Hard lines (Charter Article 3). Real people cannot be known offline, so any proper
name the definition does not declare as invented is asked about (R-5)."""

from __future__ import annotations

import re

from ..findings import Finding
from . import Subject
from .text import allowed_run, flat, name_runs, phrase, sentences

NAME = r"([A-Z][A-Za-z'\u2019-]*(?:\s+[A-Z][A-Za-z'\u2019-]*)*)"
STYLE = re.compile(
    r"(?i:\b(?:in\s+the\s+(?:style|manner)\s+of|imitat(?:es|ing|e|ed)|like\s+the\s+work\s+of"
    r"|channels|channeling|after\s+the\s+style\s+of|à\s+la)\s+(?:the\s+)?)" + NAME
)
LIKENESS = re.compile(
    r"(?i:\b(?:looks?\s+like|resembles?|resembling|the\s+face\s+of|a\s+double\s+of"
    r"|a\s+lookalike\s+of|the\s+spitting\s+image\s+of)\s+(?:the\s+)?)" + NAME
)
MINOR = phrase(
    "child",
    "children",
    "kid",
    "kids",
    "minor",
    "minors",
    "underage",
    "teen",
    "teens",
    "teenager",
    "teenagers",
    "schoolgirl",
    "schoolgirls",
    "schoolboy",
    "schoolboys",
    "toddler",
    "toddlers",
    "infant",
    "infants",
    "baby",
    "babies",
    "little girl",
    "little boy",
    "young girl",
    "young boy",
    "preteen",
)
SEXUAL = re.compile(
    r"(?i)\b(?:sex\w*|nude|nudes|naked|erotic\w*|seduct\w*|seduc\w*|aroused"
    r"|lingerie|explicit|porn\w*|fetish\w*|lewd)\b"
)
HARM = re.compile(
    r"(?i)\b(?:abus\w*|tortur\w*|molest\w*|rap(?:e|ed|ing)|murder\w*|kill(?:ed|ing|s)?"
    r"|assault\w*|mutilat\w*|beaten|whipped|starv\w*|maimed|wounded|bleeding"
    r"|dismember\w*|strangl\w*)\b"
)


def check(subject: Subject) -> list[Finding]:
    findings: list[Finding] = []
    allowed = subject.allowed_names
    for prose in subject.prose():
        text = flat(prose.text)
        certain_names: set[str] = set()
        for rule, pattern in (
            ("hardline.living-artist-style", STYLE),
            ("hardline.likeness", LIKENESS),
        ):
            for match in pattern.finditer(text):
                name = match.group(1)
                if not allowed_run(name, allowed):
                    certain_names.add(name)
                    findings.append(
                        subject.finding(
                            rule, prose, match.group(0), "FR-012, FR-036, Charter Art. 3", "certain"
                        )
                    )
        for sentence in sentences(prose.text):
            if MINOR.search(sentence) and (SEXUAL.search(sentence) or HARM.search(sentence)):
                findings.append(
                    subject.finding(
                        "hardline.minors", prose, sentence, "FR-012, Charter Art. 3", "certain"
                    )
                )
            for run in name_runs(sentence):
                if run in certain_names or allowed_run(run, allowed):
                    continue
                if any(run in name for name in certain_names):
                    continue
                findings.append(
                    subject.finding(
                        "hardline.real-name", prose, run, "FR-012, Charter Art. 3", "uncertain"
                    )
                )
    return findings
