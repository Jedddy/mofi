"""Flask Blueprint integration for Ko-fi payment webhooks."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from ._dependencies import missing_dependency

try:
    from flask import Blueprint, Response, abort, current_app, request
except ModuleNotFoundError as error:
    raise missing_dependency("Flask", "flask") from error

from mofi.exceptions import InvalidEvent, InvalidPayload, VerificationFailed
from mofi.schemas import PaymentEvent
from mofi.webhook import HandlerRegistry, parse_webhook


EventT = TypeVar("EventT", bound=PaymentEvent)


class KoFiBlueprint(Blueprint):
    """A ``Blueprint`` that receives Ko-fi payment webhooks.

    Supply ``verification_token`` directly or store it in the Flask application
    config under ``MOFI_VERIFICATION_TOKEN``. An explicit token takes precedence.
    """

    def __init__(
        self,
        name: str,
        import_name: str,
        *,
        verification_token: str | None = None,
        config_key: str = "MOFI_VERIFICATION_TOKEN",
        path: str = "/",
        **blueprint_options: Any,
    ) -> None:
        super().__init__(name, import_name, **blueprint_options)
        self.verification_token = verification_token
        self.config_key = config_key
        self._handlers = HandlerRegistry()
        self.add_url_rule(
            path,
            endpoint="kofi_webhook",
            view_func=self._receive,
            methods=["POST"],
        )

    def on(
        self,
        event_type: type[EventT],
    ) -> Callable[[Callable[[EventT], Any]], Callable[[EventT], Any]]:
        """Decorate a handler for one known payment event class."""

        def register(handler: Callable[[EventT], Any]) -> Callable[[EventT], Any]:
            return self._handlers.add(event_type, handler)

        return register

    def on_payment(
        self,
        handler: Callable[[PaymentEvent], Any],
    ) -> Callable[[PaymentEvent], Any]:
        """Decorate a handler that receives every valid payment."""

        return self._handlers.add_all(handler)

    def _receive(self) -> Response:
        values = request.form.getlist("data")
        if len(values) != 1:
            abort(400, description="Invalid Ko-fi webhook payload.")

        token = self.verification_token
        if token is None:
            token = current_app.config[self.config_key]

        try:
            event = parse_webhook(values[0], token)
        except VerificationFailed:
            abort(403, description="Ko-fi webhook verification failed.")
        except (InvalidPayload, InvalidEvent):
            abort(400, description="Invalid Ko-fi webhook payload.")

        for handler in self._handlers.handlers_for(event):
            current_app.ensure_sync(handler)(event)

        return current_app.response_class(status=200)


__all__ = ["KoFiBlueprint"]
