"""Django view integration for Ko-fi payment webhooks."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from asgiref.sync import async_to_sync, iscoroutinefunction
from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
)
from django.views.decorators.csrf import csrf_exempt

from mofi.exceptions import InvalidEvent, InvalidPayload, VerificationFailed
from mofi.schemas import PaymentEvent
from mofi.webhook import HandlerRegistry, parse_webhook


EventT = TypeVar("EventT", bound=PaymentEvent)


class KoFiWebhook:
    """A configured, CSRF-exempt Django webhook view.

    Mount :attr:`view` with ``django.urls.path``. Supply a token directly or
    store it in the Django setting named by ``setting_name``; an explicit token
    takes precedence. No Django application or database setup is required.
    """

    def __init__(
        self,
        verification_token: str | None = None,
        *,
        setting_name: str = "MOFI_VERIFICATION_TOKEN",
    ) -> None:
        self.verification_token = verification_token
        self.setting_name = setting_name
        self._handlers = HandlerRegistry()
        self.view = csrf_exempt(self._receive)

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

    def _receive(self, request: HttpRequest) -> HttpResponse:
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        values = request.POST.getlist("data")
        if len(values) != 1:
            return HttpResponseBadRequest()

        token = self.verification_token
        if token is None:
            token = getattr(settings, self.setting_name)

        try:
            event = parse_webhook(values[0], token)
        except VerificationFailed:
            return HttpResponseForbidden()
        except (InvalidPayload, InvalidEvent):
            return HttpResponseBadRequest()

        for handler in self._handlers.handlers_for(event):
            if iscoroutinefunction(handler):
                async_to_sync(handler)(event)
            else:
                handler(event)

        return HttpResponse(status=200)


__all__ = ["KoFiWebhook"]
