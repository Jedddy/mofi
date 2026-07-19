"""Minimal Flask application with a Mofi webhook Blueprint."""

from __future__ import annotations

import logging
import os

from flask import Flask

from mofi import Donation, PaymentEvent
from mofi.integrations.flask import KoFiBlueprint


logger = logging.getLogger(__name__)
app = Flask(__name__)
webhook = KoFiBlueprint(
    "kofi",
    __name__,
    verification_token=os.environ["KOFI_VERIFICATION_TOKEN"],
    url_prefix="/webhooks/kofi",
)


@webhook.on(Donation)
def donation(_: Donation) -> None:
    logger.info("Received a Ko-fi donation")


@webhook.on_payment
def every_payment(_: PaymentEvent) -> None:
    logger.info("Finished handling a Ko-fi payment")


app.register_blueprint(webhook)
