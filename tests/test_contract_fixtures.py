"""Contract checks for the sanitized Ko-fi fixture corpus."""

from __future__ import annotations

import json
from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_every_json_fixture_is_an_object_with_documented_provenance() -> None:
    provenance = (FIXTURES / "README.md").read_text(encoding="utf-8")

    for fixture_path in FIXTURES.glob("*.json"):
        assert isinstance(load_fixture(fixture_path.name), dict)
        assert f"`{fixture_path.name}`" in provenance


def test_private_and_digital_fixtures_do_not_invent_public_or_shipping_data() -> None:
    private = load_fixture("donation_private.json")
    digital = load_fixture("shop_order_digital.json")

    assert private["is_public"] is False
    assert "message" not in private
    assert "shipping" not in digital


def test_physical_shipping_does_not_require_a_telephone_number() -> None:
    shipping = load_fixture("shop_order_physical.json")["shipping"]

    assert isinstance(shipping, dict)
    assert "telephone" not in shipping


def test_duplicate_delivery_pair_differs_by_nothing() -> None:
    first = load_fixture("duplicate_first.json")
    retry = load_fixture("duplicate_retry.json")

    assert retry == first
    assert retry["message_id"] == first["message_id"]


def test_commission_fixture_is_explicitly_synthetic() -> None:
    provenance = (FIXTURES / "README.md").read_text(encoding="utf-8")

    assert "`commission.synthetic.json` | Synthetic" in provenance
    assert "authenticated Ko-fi Webhooks page" in provenance
