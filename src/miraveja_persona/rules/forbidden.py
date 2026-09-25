"""What never belongs in a definition (FR-007, FR-014, FR-015)."""

from __future__ import annotations

import re

from ..findings import Finding
from . import Subject
from .text import flat

VISITOR = [
    re.compile(r"(?i)\bmuseum\s+visitors?\b"),
    re.compile(
        r"(?i)\bvisitors?\s+(?:said|says|told|wrote|writes|commented|comments|reacted"
        r"|liked|loved|hated|asked|replied|called)\b"
    ),
    re.compile(r"(?i)\b(?:what|something)\s+(?:a|the|one)\s+visitor\s+(?:said|wrote|asked)\b"),
    re.compile(r"(?i)\bpseudonyms?\b"),
    re.compile(r"(?i)\b(?:curator|gate)\s+(?:rejected|accepted|approved|refused|judged)\b"),
    re.compile(r"(?i)\bverdicts?\b"),
    re.compile(r"(?i)\b(?:the\s+)?audience\s+(?:said|wrote|reacted|commented)\b"),
]
MODEL = [
    re.compile(r"(?i)\b(?:checkpoints?|lora|loras|cfg|safetensors|gguf|llm|llms)\b"),
    re.compile(r"(?i)\b(?:diffusion|language|text|image)\s+models?\b"),
    re.compile(r"(?i)\b(?:negative\s+)?prompt\s*:"),
    re.compile(r"(?i)\b(?:sampler|seed|steps|model|scheduler)\s*[:=]"),
    re.compile(
        r"(?i)\b\d+\s+(?:sampling\s+)?steps\b(?=[^.]*\b(?:checkpoint|lora|sampler|cfg|seed|model)\b)"
        r"|\b(?:checkpoint|lora|sampler|cfg|seed|model)\b[^.]*\b\d+\s+steps\b"
    ),
    re.compile(r"(?i)\bmodel\s+(?:version|v?\d)"),
]
# Token formats precise enough to scan any file with; the public-repository guard uses these.
SECRET_TOKENS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bsk-[A-Za-z0-9]{20,}\b|\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abp]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"https?://[^\s/:@]+:[^\s/@]+@"),
]
# In a definition's prose, any key-value credential is also refused; too noisy for code.
SECRET = [
    *SECRET_TOKENS,
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?key|token|password|passwd"
        r"|client[_-]?secret)\s*[:=]\s*\S+"
    ),
]


def check(subject: Subject) -> list[Finding]:
    findings: list[Finding] = []
    for prose in subject.prose():
        text = flat(prose.text)
        for rule, patterns, cites in (
            ("forbidden.visitor", VISITOR, "FR-014"),
            ("forbidden.model", MODEL, "FR-007"),
            ("forbidden.secret", SECRET, "FR-015"),
        ):
            for pattern in patterns:
                for match in pattern.finditer(text):
                    findings.append(subject.finding(rule, prose, match.group(0), cites, "certain"))
    return findings
