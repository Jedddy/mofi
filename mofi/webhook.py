"""Parsing and handler selection shared by Mofi's framework integrations."""

from __future__ import annotations

import hmac
import json
from collections import defaultdict
from copy import deepcopy
from typing import Any, Callable, TypeVar

from pydantic import ValidationError

from .exceptions import InvalidEvent, InvalidPayload, VerificationFailed
from .schemas import (
    Commission,
    Donation,
    PaymentEvent,
    ShopOrder,
    Subscription,
    UnknownPayment,
)


_EVENT_TYPES: dict[str, type[PaymentEvent]] = {
    "donation": Donation,
    "subscription": Subscription,
    "commission": Commission,
    "shop order": ShopOrder,
}
_KNOWN_EVENT_TYPES = frozenset(_EVENT_TYPES.values())

EventT = TypeVar("EventT", bound=PaymentEvent)
Handler = Callable[[EventT], Any]
StoredHandler = Callable[..., Any]


def parse_webhook(data: str, verification_token: str) -> PaymentEvent:
    """Decode, verify, and classify one Ko-fi webhook form value.

    The returned event owns its decoded data. Error messages intentionally omit
    both the configured token and payment payload.
    """

    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        raise InvalidPayload() from None

    if not isinstance(payload, dict):
        raise InvalidPayload()

    identity = (
        payload.get("verification_token"),
        payload.get("message_id"),
        payload.get("type"),
    )
    if any(not isinstance(value, str) or not value.strip() for value in identity):
        raise InvalidEvent()

    received_token, _, event_type = identity
    if not hmac.compare_digest(
        received_token.encode("utf-8"),
        verification_token.encode("utf-8"),
    ):
        raise VerificationFailed()

    model = _EVENT_TYPES.get(_normalize_type(event_type), UnknownPayment)
    try:
        return model.model_validate({**payload, "raw": deepcopy(payload)})
    except ValidationError:
        raise InvalidEvent() from None


def _normalize_type(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


class HandlerRegistry:
    """Instance-local event handlers with deterministic selection order."""

    def __init__(self) -> None:
        self._specific: dict[type[PaymentEvent], list[StoredHandler]] = defaultdict(list)
        self._all: list[StoredHandler] = []

    def add(self, event_type: type[EventT], handler: Handler[EventT]) -> Handler[EventT]:
        """Register a handler for one known payment class."""

        if event_type not in _KNOWN_EVENT_TYPES:
            raise ValueError("Specific handlers require a known payment event class.")
        self._specific[event_type].append(handler)
        return handler

    def add_all(self, handler: Handler[PaymentEvent]) -> Handler[PaymentEvent]:
        """Register a handler that receives every valid payment."""

        self._all.append(handler)
        return handler

    def handlers_for(self, event: PaymentEvent) -> tuple[StoredHandler, ...]:
        """Select specific handlers first, followed by all-payment handlers."""

        return (*self._specific.get(type(event), ()), *self._all)


__all__ = ["HandlerRegistry", "parse_webhook"]
