"""Framework-independent models for Ko-fi payment webhooks."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _PayloadModel(BaseModel):
    """Base model that keeps fields added by Ko-fi in future payloads."""

    model_config = ConfigDict(extra="allow")


class ShopItem(_PayloadModel):
    """One item included in a Ko-fi Shop Order."""

    direct_link_code: str | None = None
    variation_name: str | None = None
    quantity: int | None = None


class Shipping(_PayloadModel):
    """Optional physical-delivery details for a Ko-fi Shop Order."""

    full_name: str | None = None
    street_address: str | None = None
    city: str | None = None
    state_or_province: str | None = None
    postal_code: str | None = None
    country: str | None = None
    country_code: str | None = None
    telephone: str | None = None


class PaymentEvent(_PayloadModel):
    """Fields shared by every Ko-fi payment notification.

    Ko-fi may add fields without versioning its webhook payload. Every event
    therefore retains the complete decoded mapping in :attr:`raw` and allows
    added fields to remain accessible on the model.
    """

    verification_token: str = Field(min_length=1, repr=False)
    message_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    raw: dict[str, Any] = Field(repr=False)
    timestamp: datetime | None = None
    is_public: bool | None = None
    from_name: str | None = None
    message: str | None = None
    amount: str | None = None
    url: str | None = None
    email: str | None = None
    currency: str | None = None
    kofi_transaction_id: str | None = None


class Donation(PaymentEvent):
    """A one-time Ko-fi donation or tip."""


class Subscription(PaymentEvent):
    """A Ko-fi membership or recurring-support payment."""

    is_subscription_payment: bool | None = None
    is_first_subscription_payment: bool | None = None
    tier_name: str | None = None


class Commission(PaymentEvent):
    """A Ko-fi Commission payment.

    Only confirmed common payment fields are modeled. Commission-specific
    values remain available through :attr:`PaymentEvent.raw` until an
    authenticated Ko-fi delivery provides evidence for additional fields.
    """


class ShopOrder(PaymentEvent):
    """A digital or physical Ko-fi Shop Order."""

    shop_items: list[ShopItem] | None = None
    shipping: Shipping | None = None


class UnknownPayment(PaymentEvent):
    """A valid payment type that this Mofi version does not know yet."""


KnownPayment = Donation | Subscription | Commission | ShopOrder


__all__ = [
    "Commission",
    "Donation",
    "KnownPayment",
    "PaymentEvent",
    "Shipping",
    "ShopItem",
    "ShopOrder",
    "Subscription",
    "UnknownPayment",
]
