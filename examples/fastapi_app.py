"""Minimal FastAPI application with a Mofi webhook router."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI

from mofi import Donation, PaymentEvent
from mofi.integrations.fastapi import KoFiRouter


logger = logging.getLogger(__name__)
app = FastAPI()
webhook = KoFiRouter(
    os.environ["KOFI_VERIFICATION_TOKEN"],
    prefix="/webhooks/kofi",
)


@webhook.on(Donation)
async def donation(_: Donation) -> None:
    logger.info("Received a Ko-fi donation")


@webhook.on_payment
def every_payment(_: PaymentEvent) -> None:
    logger.info("Finished handling a Ko-fi payment")


app.include_router(webhook)
