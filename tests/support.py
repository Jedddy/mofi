"""Shared helpers for the webhook contract and adapter suites."""

from __future__ import annotations

import json
from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures"


def load_payload(name: str) -> dict[str, object]:
    """Load one decoded Ko-fi webhook fixture."""

    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def encoded_payload(name: str) -> str:
    """Return a fixture encoded as Ko-fi's `data` form value."""

    return json.dumps(load_payload(name))
