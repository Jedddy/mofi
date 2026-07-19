"""Django URLconf with a Mofi webhook view."""

from __future__ import annotations

import logging
import os

from django.urls import path

from mofi import Donation, PaymentEvent
from mofi.integrations.django import KoFiWebhook


logger = logging.getLogger(__name__)
webhook = KoFiWebhook(
    verification_token=os.environ["KOFI_VERIFICATION_TOKEN"]
)


@webhook.on(Donation)
def donation(_: Donation) -> None:
    logger.info("Received a Ko-fi donation")


@webhook.on_payment
def every_payment(_: PaymentEvent) -> None:
    logger.info("Finished handling a Ko-fi payment")


urlpatterns = [
    path("webhooks/kofi/", webhook.view, name="kofi_webhook"),
]
