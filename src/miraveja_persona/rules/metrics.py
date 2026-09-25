"""Money and metrics (Principle II; Charter Articles 9 and 10)."""

from __future__ import annotations

import re

from ..findings import Finding
from . import Subject
from .text import flat, phrase

MONEY = [
    phrase(
        "money",
        "moneys",
        "price",
        "prices",
        "priced",
        "pricing",
        "paid",
        "payment",
        "payments",
        "earn",
        "earns",
        "earned",
        "earning",
        "earnings",
        "sell",
        "sells",
        "selling",
        "sold",
        "sale",
        "sales",
        "buy",
        "buys",
        "buying",
        "bought",
        "buyer",
        "buyers",
        "income",
        "wealth",
        "wealthy",
        "currency",
        "dollars?",
        "euros?",
        "cash",
        "fees?",
        "auction",
        "auctions",
        "auctioned",
        "profit",
        "profits",
        "profitable",
        "revenue",
        "salary",
        "wages?",
        "cost",
        "costs",
        "costly",
        "invest",
        "investment",
    ),
    re.compile(r"(?i)\bpay(?:s|ing)?\b(?!\s+(?:no\s+|little\s+|close\s+)?attention)"),
    re.compile(r"[$€£¥]\s?\d|\b\d+(?:[.,]\d+)?\s?(?:USD|EUR|BRL|GBP)\b"),
]
AUDIENCE = (
    r"(?:likes|views|followers|subscribers|reactions|hearts|fans|upvotes|shares|clicks"
    r"|impressions|votes)"
)
COUNT = [
    phrase(
        "followers",
        "subscribers",
        "upvotes",
        "downvotes",
        "leaderboard",
        "ranking",
        "rankings",
        "ranked",
        "trending",
        "viral",
        "engagement",
        "metrics?",
        "analytics",
        "impressions",
        "popularity",
        "ratings?",
        "stats",
        "statistics",
    ),
    re.compile(rf"(?i)\b\d[\d,.]*\s*(?:k\s+)?{AUDIENCE}\b"),
    re.compile(
        rf"(?i)\b(?:more|most|many|few|fewer|lots\s+of|number\s+of|count\s+of|get|gets"
        rf"|getting|got|gain|gains|gained|chase|chases|chasing|win|wins|won|collect"
        rf"|collects)\s+{AUDIENCE}\b"
    ),
    re.compile(r"(?i)\bmost\s+popular\b|\bpopular\s+(?:with|among)\b"),
    re.compile(r"(?i)\btop\s+\d+\b"),
]
NUMBER = [
    re.compile(
        r"(?i)\b(?:\d[\d,.]*|dozens|hundreds|thousands|millions)\s+(?:of\s+)?(?:people"
        r"|visitors|fans|admirers|viewers|readers|reactions|comments|votes|hearts)\b"
    ),
    phrase("scores?", "scored"),
]


def check(subject: Subject) -> list[Finding]:
    findings: list[Finding] = []
    for prose in subject.prose():
        text = flat(prose.text)
        for rule, patterns, certainty in (
            ("metric.money", MONEY, "certain"),
            ("metric.count", COUNT, "certain"),
            ("metric.number", NUMBER, "uncertain"),
        ):
            if rule == "metric.number" and prose.is_when:
                continue
            for pattern in patterns:
                for match in pattern.finditer(text):
                    findings.append(
                        subject.finding(
                            rule,
                            prose,
                            match.group(0),
                            "FR-013, Charter Arts. 9 and 10",
                            "certain" if certainty == "certain" else "uncertain",
                        )
                    )
    return findings
