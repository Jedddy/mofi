"""Framework-neutral Ko-fi payload parsing and dispatch selection."""

from __future__ import annotations

import copy
import json

import pytest

from mofi import Commission, Donation, ShopOrder, Subscription, UnknownPayment
from mofi.exceptions import InvalidEvent, InvalidPayload, VerificationFailed
from mofi.webhook import HandlerRegistry, parse_webhook
from tests.support import encoded_payload, load_payload


@pytest.mark.parametrize(
    ("fixture_name", "event_class"),
    [
        ("donation.json", Donation),
        ("subscription.json", Subscription),
        ("commission.synthetic.json", Commission),
        ("shop_order_physical.json", ShopOrder),
        ("shop_order_digital.json", ShopOrder),
    ],
)
def test_known_payments_create_the_expected_event(
    fixture_name: str,
    event_class: type[object],
) -> None:
    event = parse_webhook(encoded_payload(fixture_name), "fixture-token")

    assert isinstance(event, event_class)
    assert event.raw == load_payload(fixture_name)


def test_type_selection_is_normalized_without_changing_the_event_value() -> None:
    payload = load_payload("shop_order_digital.json")
    payload["type"] = "  shop_order  "

    event = parse_webhook(json.dumps(payload), "fixture-token")

    assert isinstance(event, ShopOrder)
    assert event.type == "  shop_order  "
    assert event.raw["type"] == "  shop_order  "


def test_unknown_payment_preserves_the_complete_payload() -> None:
    payload = load_payload("unknown_payment.json")

    event = parse_webhook(json.dumps(payload), "fixture-token")

    assert isinstance(event, UnknownPayment)
    assert event.raw == payload
    assert event.future_payment_field == {"reward": "sample"}


def test_known_payment_retains_added_fields() -> None:
    event = parse_webhook(
        encoded_payload("donation_extra_field.json"),
        "fixture-token",
    )

    assert isinstance(event, Donation)
    assert event.future_payment_field == "preserved"
    assert event.raw["future_payment_field"] == "preserved"


@pytest.mark.parametrize(
    "fixture_name",
    ["donation_private.json", "shop_order_digital.json", "shop_order_physical.json"],
)
def test_absent_optional_fields_remain_valid(fixture_name: str) -> None:
    parse_webhook(encoded_payload(fixture_name), "fixture-token")


@pytest.mark.parametrize("value", ["not json", "[]", "null", "42"])
def test_malformed_or_non_object_json_is_rejected(value: str) -> None:
    with pytest.raises(InvalidPayload, match="Invalid Ko-fi webhook payload"):
        parse_webhook(value, "fixture-token")


@pytest.mark.parametrize("field", ["verification_token", "message_id", "type"])
def test_missing_required_identity_is_rejected(field: str) -> None:
    payload = load_payload("donation.json")
    del payload[field]

    with pytest.raises(InvalidEvent, match="Invalid Ko-fi payment event"):
        parse_webhook(json.dumps(payload), "fixture-token")


@pytest.mark.parametrize("field", ["verification_token", "message_id", "type"])
@pytest.mark.parametrize("value", ["", "   ", None, 3])
def test_required_identity_must_be_non_empty_text(field: str, value: object) -> None:
    payload = load_payload("donation.json")
    payload[field] = value

    with pytest.raises(InvalidEvent, match="Invalid Ko-fi payment event"):
        parse_webhook(json.dumps(payload), "fixture-token")


def test_token_mismatch_is_secret_safe() -> None:
    payload = load_payload("invalid_token.json")

    with pytest.raises(VerificationFailed) as error:
        parse_webhook(json.dumps(payload), "fixture-token")

    message = str(error.value)
    assert "fixture-token" not in message
    assert "incorrect-fixture-token" not in message
    assert "Invalid Supporter" not in message


def test_token_comparison_uses_compare_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    compared: list[tuple[bytes, bytes]] = []

    def compare_digest(received: bytes, expected: bytes) -> bool:
        compared.append((received, expected))
        return True

    monkeypatch.setattr("mofi.webhook.hmac.compare_digest", compare_digest)

    parse_webhook(encoded_payload("donation.json"), "fixture-token")

    assert compared == [(b"fixture-token", b"fixture-token")]


def test_duplicate_message_ids_are_not_suppressed() -> None:
    first = parse_webhook(encoded_payload("duplicate_first.json"), "fixture-token")
    retry = parse_webhook(encoded_payload("duplicate_retry.json"), "fixture-token")

    assert first.message_id == retry.message_id
    assert first is not retry


def test_parsing_does_not_mutate_the_source_mapping() -> None:
    payload = load_payload("shop_order_physical.json")
    original = copy.deepcopy(payload)

    parse_webhook(json.dumps(payload), "fixture-token")

    assert payload == original


def test_handler_registry_orders_specific_handlers_before_all_handlers() -> None:
    registry = HandlerRegistry()

    def first(_: Donation) -> None:
        pass

    def second(_: Donation) -> None:
        pass

    def all_payments(_: object) -> None:
        pass

    registry.add(Donation, first)
    registry.add(Donation, second)
    registry.add_all(all_payments)
    event = parse_webhook(encoded_payload("donation.json"), "fixture-token")

    assert registry.handlers_for(event) == (first, second, all_payments)


def test_unknown_payments_select_only_all_payment_handlers() -> None:
    registry = HandlerRegistry()

    def donation(_: Donation) -> None:
        pass

    def all_payments(_: object) -> None:
        pass

    registry.add(Donation, donation)
    registry.add_all(all_payments)
    event = parse_webhook(encoded_payload("unknown_payment.json"), "fixture-token")

    assert registry.handlers_for(event) == (all_payments,)
