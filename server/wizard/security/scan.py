"""Security scanner for self-evolution proposals.

Runs before any proposal may enter ``pending``.  Detects three red-line
categories (design/04-hermes-self-evolution.md §5):

  1. Prompt-injection patterns  (ignore previous / repeat above / jailbreak)
  2. Credential leaks          (AK/SK, private-key blocks, Bearer tokens,
                                 password assignments)
  3. Backdoor / reverse-shell command patterns

A hit on ANY category rejects the proposal at the scanned state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScanHit:
    category: str
    description: str
    evidence: str = ""          # the matched snippet (truncated)
    evidence_span: str = ""     # alias kept for the API contract


@dataclass
class ScanResult:
    passed: bool
    hits: list[ScanHit] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Pattern table — (category, compiled regex, human description)
# --------------------------------------------------------------------------- #
def _compile(pattern: str, flags: int = re.IGNORECASE) -> re.Pattern:
    return re.compile(pattern, flags)


_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    # -- prompt injection ---------------------------------------------------
    ("prompt_injection",
     _compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)"),
     "ignore previous instructions prompt-injection"),
    ("prompt_injection",
     _compile(r"disregard\s+(all\s+)?(previous|prior|above|earlier)"),
     "disregard prior instructions prompt-injection"),
    ("prompt_injection",
     _compile(r"repeat\s+(the\s+)?(above|following|previous)\s+(text|prompt|message)"),
     "repeat above prompt-injection"),
    ("prompt_injection",
     _compile(r"\b(jailbreak|jail\s*break|dan\s+mode|developer\s+mode)\b"),
     "jailbreak phrase"),
    ("prompt_injection",
     _compile(r"you\s+are\s+now\s+(a|an)\s+(DAN|different\s+AI|unrestricted)"),
     "role-swap jailbreak prompt-injection"),

    # -- credential leaks ---------------------------------------------------
    ("credential_leak",
     _compile(r"\bAK[A-Za-z0-9]{16,}\b"),
     "Volcengine-style AccessKey leak"),
    ("credential_leak",
     _compile(r"-----BEGIN\s+[A-Z ]*PRIVATE\s+KEY-----"),
     "private key block leak"),
    ("credential_leak",
     _compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]{20,}={0,2}\b"),
     "Bearer token leak"),
    ("credential_leak",
     _compile(r"\b(password|passwd|pwd|secret|api[_-]?key)\b\s*[:=]\s*['\"]?[^\s'\"{}]{8,}"),
     "password / secret / api-key assignment leak"),
    ("credential_leak",
     _compile(r"(sk|pk|ak)-[A-Za-z0-9]{16,}"),
     "generic API key (sk-/pk-/ak-) leak"),

    # -- backdoor / reverse shell -------------------------------------------
    ("backdoor",
     _compile(r"bash\s+-i\b"),
     "interactive bash reverse shell"),
    ("backdoor",
     _compile(r"/dev/tcp/[0-9a-zA-Z.\-_]+/\d+"),
     "/dev/tcp reverse shell"),
    ("backdoor",
     _compile(r"\b(nc|ncat|netcat)\b[^\n]*-[ce]\b"),
     "netcat reverse shell (-e/-c)"),
    ("backdoor",
     _compile(r"rm\s+-rf\s+(/|~|\*)\b"),
     "recursive destructive delete"),
    ("backdoor",
     _compile(r"curl\s+[^|]*\|\s*(bash|sh|zsh)\b"),
     "pipe curl output to shell"),
]


def _truncate(text: str, max_len: int = 120) -> str:
    text = text.strip().replace("\n", " ")
    return text[:max_len] + ("…" if len(text) > max_len else "")


def scan_proposal_text(text: str) -> ScanResult:
    """Scan a proposal's diff/rationale text for red-line patterns.

    Args:
        text: the raw proposal diff + rationale string.

    Returns:
        ScanResult with ``passed=False`` and populated ``hits`` when any
        pattern matches.
    """
    hits: list[ScanHit] = []
    for category, regex, description in _PATTERNS:
        m = regex.search(text)
        if m:
            hits.append(ScanHit(
                category=category,
                description=description,
                evidence=_truncate(m.group(0)),
                evidence_span=_truncate(m.group(0)),
            ))
    return ScanResult(passed=len(hits) == 0, hits=hits)


def scan_proposal(
    diff: str = "",
    rationale: str = "",
) -> dict[str, Any]:
    """Convenience wrapper returning a JSON-serialisable dict.

    Returns:
        ``{"passed": bool, "hits": [{"category", "description", "evidence_span"}]}``
    """
    combined = f"{diff}\n{rationale}"
    result = scan_proposal_text(combined)
    return {
        "passed": result.passed,
        "hits": [
            {
                "category": h.category,
                "description": h.description,
                "evidence_span": h.evidence_span,
            }
            for h in result.hits
        ],
    }
