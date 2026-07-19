"""FastAPI router integration for Ko-fi payment webhooks."""

from __future__ import annotations

import inspect
from typing import Any, Callable, TypeVar

from ._dependencies import missing_dependency

try:
    from fastapi import APIRouter, HTTPException, Request, Response, status
except ModuleNotFoundError as error:
    raise missing_dependency("FastAPI", "fastapi") from error

from mofi.exceptions import InvalidEvent, InvalidPayload, VerificationFailed
from mofi.schemas import PaymentEvent
from mofi.webhook import HandlerRegistry, parse_webhook


EventT = TypeVar("EventT", bound=PaymentEvent)


class KoFiRouter(APIRouter):
    """An ``APIRouter`` that receives Ko-fi payment webhooks.

    Include the instance directly in an existing FastAPI application. Handler
    state and the verification token belong to this router instance, allowing
    one application to host multiple independent Ko-fi endpoints.
    """

    def __init__(
        self,
        verification_token: str,
        *,
        path: str = "/",
        **router_options: Any,
    ) -> None:
        super().__init__(**router_options)
        self.verification_token = verification_token
        self._handlers = HandlerRegistry()
        self.add_api_route(
            path,
            self._receive,
            methods=["POST"],
            name="kofi_webhook",
            response_class=Response,
            status_code=status.HTTP_200_OK,
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

    async def _receive(self, request: Request) -> Response:
        form = await request.form()
        values = form.getlist("data")
        if len(values) != 1 or not isinstance(values[0], str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Ko-fi webhook payload.",
            )

        try:
            event = parse_webhook(values[0], self.verification_token)
        except VerificationFailed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ko-fi webhook verification failed.",
            ) from None
        except (InvalidPayload, InvalidEvent):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Ko-fi webhook payload.",
            ) from None

        for handler in self._handlers.handlers_for(event):
            result = handler(event)
            if inspect.isawaitable(result):
                await result

        return Response(status_code=status.HTTP_200_OK)


__all__ = ["KoFiRouter"]
