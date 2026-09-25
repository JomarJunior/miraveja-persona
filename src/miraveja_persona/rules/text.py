"""Small text helpers shared by the rule modules."""

from __future__ import annotations

import re
from collections.abc import Iterator

SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n\s*\n")
WORD = r"[A-Za-z][A-Za-z'\u2019-]*"
NAME_TOKEN = re.compile(r"[A-Z][A-Za-z'\u2019-]*")

# Capitalized words that are never names. Months and weekdays are capitalized in English.
COMMON = {
    "I",
    "I'm",
    "I've",
    "I'd",
    "I'll",
    "AI",
    "OK",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
    "The",
    "A",
    "An",
}


def flat(text: str) -> str:
    """Block scalars wrap lines mid-sentence; treat single newlines as spaces."""
    return re.sub(r"(?<!\n)\n(?!\n)", " ", text).strip()


def sentences(text: str) -> Iterator[str]:
    for part in SENTENCE_END.split(flat(text)):
        if part.strip():
            yield part.strip()


def phrase(*alternatives: str) -> re.Pattern[str]:
    """A case-insensitive pattern matching any alternative as whole words."""
    return re.compile(r"(?i)\b(?:" + "|".join(alternatives) + r")\b")


PUNCT = "\"'\u201c\u201d\u2018\u2019()[],.;:!?"
POSSESSIVE = re.compile(r"['\u2019]s$")


def name_runs(sentence: str) -> Iterator[str]:
    """Runs of capitalized words, skipping the sentence's first word (R-5)."""
    run: list[str] = []
    for index, raw in enumerate(sentence.split()):
        word = raw.strip(PUNCT)
        base = POSSESSIVE.sub("", word)
        if index > 0 and base and NAME_TOKEN.fullmatch(base) and base not in COMMON:
            run.append(base)
            if base != word or raw[-1] in PUNCT:
                yield " ".join(run)
                run = []
        elif run:
            yield " ".join(run)
            run = []
    if run:
        yield " ".join(run)


def allowed_run(run: str, allowed: frozenset[str]) -> bool:
    """A run is allowed if it is, or is made of words from, a declared name."""
    if run in allowed:
        return True
    tokens = {t for name in allowed for t in name.split()}
    return all(t in tokens for t in run.split())
