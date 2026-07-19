"""Shared helpers for the webhook contract and adapter suites."""

from __future__ import annotations

import json
from pathlib import Path

from mofi import Commission, Donation, PaymentEvent, ShopOrder, Subscription, UnknownPayment


FIXTURES = Path(__file__).parent / "fixtures"
FIXTURE_TOKEN = "fixture-token"
PAYMENT_CASES: tuple[tuple[str, type[PaymentEvent]], ...] = (
    ("donation.json", Donation),
    ("donation_private.json", Donation),
    ("donation_extra_field.json", Donation),
    ("subscription.json", Subscription),
    ("commission.synthetic.json", Commission),
    ("shop_order_physical.json", ShopOrder),
    ("shop_order_digital.json", ShopOrder),
    ("unknown_payment.json", UnknownPayment),
)


def load_payload(name: str) -> dict[str, object]:
    """Load one decoded Ko-fi webhook fixture."""

    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def encoded_payload(name: str) -> str:
    """Return a fixture encoded as Ko-fi's `data` form value."""

    return json.dumps(load_payload(name))
