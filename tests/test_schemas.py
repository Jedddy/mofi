"""Event-model behavior shared by every framework integration."""

from __future__ import annotations

from mofi import Commission, Donation, PaymentEvent, ShopOrder, Subscription
from mofi.schemas import Shipping


def test_known_event_classes_share_the_payment_base() -> None:
    assert issubclass(Donation, PaymentEvent)
    assert issubclass(Subscription, PaymentEvent)
    assert issubclass(Commission, PaymentEvent)
    assert issubclass(ShopOrder, PaymentEvent)


def test_optional_supporter_fields_may_be_absent() -> None:
    donation = Donation(
        verification_token="fixture-token",
        message_id="message-id",
        type="Donation",
        raw={"type": "Donation"},
    )

    assert donation.message is None
    assert donation.email is None
    assert donation.is_public is None


def test_shipping_telephone_is_optional() -> None:
    shipping = Shipping(
        full_name="Sample Recipient",
        street_address="100 Example Street",
        city="Sample City",
        country="United States",
        country_code="US",
    )

    assert shipping.telephone is None


def test_models_retain_added_fields() -> None:
    event = Donation(
        verification_token="fixture-token",
        message_id="message-id",
        type="Donation",
        raw={"future_payment_field": "preserved"},
        future_payment_field="preserved",
    )

    assert event.model_extra == {"future_payment_field": "preserved"}
