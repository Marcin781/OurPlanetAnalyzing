"""Deterministic application security guard for OurPlanetAnalyzing.

This is a defensive baseline, not a claim of protection against every attack.
It deliberately keeps enforcement rules small and high-confidence so that an
AI component cannot directly make destructive security decisions.
"""

from __future__ import annotations

import re
import secrets
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import unquote


@dataclass(frozen=True)
class SecurityFinding:
    category: str
    severity: str
    action: str
    event_id: str


RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("path_traversal", "critical", ("../", "..\\", "%2e%2e", "%252e%252e")),
    ("xss", "high", ("<script", "javascript:", "onerror=", "onload=")),
    ("sql_injection", "high", ("union select", "or 1=1", "and 1=1", "drop table", "sleep(")),
    ("ssrf", "high", ("169.254.169.254", "metadata.google.internal", "127.0.0.1", "localhost")),
    ("command_injection", "high", (";cat /", "|cat /", "&& cat /", "$(cat /", "`cat /")),
)

SEVERITY_ACTION = {
    "critical": "block",
    "high": "block",
    "medium": "alert",
    "low": "log",
}

_event_counts: Counter[str] = Counter()


def _normalize(value: str) -> str:
    value = unquote(value)
    value = unquote(value)
    return re.sub(r"\s+", " ", value.lower())


def inspect_request(path: str, query: str = "", method: str = "") -> list[SecurityFinding]:
    """Inspect request metadata and return high-confidence findings only."""
    target = _normalize(f"{method} {path}?{query}")
    findings: list[SecurityFinding] = []
    for category, severity, indicators in RULES:
        if any(indicator in target for indicator in indicators):
            _event_counts[category] += 1
            findings.append(
                SecurityFinding(
                    category=category,
                    severity=severity,
                    action=SEVERITY_ACTION[severity],
                    event_id=f"sec-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}",
                )
            )
    return findings


def security_summary() -> dict:
    """Return non-sensitive security telemetry for administrators."""
    return {
        "enabled": True,
        "mode": "deterministic_guard",
        "enforcement": "high_confidence_request_blocking",
        "events": dict(_event_counts),
        "note": "This layer is a baseline and does not guarantee protection against all attacks.",
    }
