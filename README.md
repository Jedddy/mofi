# Mofi

Mofi turns Ko-fi payment webhooks into typed Python events inside an existing
FastAPI, Flask, or Django application. It validates Ko-fi's shared verification
token, preserves the complete payload, and runs application handlers before
acknowledging the delivery.

Mofi covers payment notifications only: donations, subscriptions, commissions,
and shop orders. Ko-fi does not expose account management, posts, messages,
membership cancellations, refunds, or fulfillment operations through this API.

## Install

Install only the integration your application uses:

```bash
uv add "mofi[fastapi]"
uv add "mofi[flask]"
uv add "mofi[django]"
```

Use `mofi[all]` for all three integrations. The equivalent `pip install`
commands also work. A base `mofi` install includes only Pydantic and the shared
event models.

Mofi requires Python 3.10 or newer.

## FastAPI

```python
import os

from fastapi import FastAPI

from mofi import Donation, PaymentEvent
from mofi.integrations.fastapi import KoFiRouter

app = FastAPI()
webhook = KoFiRouter(
    os.environ["KOFI_VERIFICATION_TOKEN"],
    prefix="/webhooks/kofi",
)


@webhook.on(Donation)
async def donation(event: Donation) -> None:
    await record_donation(event.message_id, event.amount)


@webhook.on_payment
def every_payment(event: PaymentEvent) -> None:
    audit_payment(event.message_id, event.type)


app.include_router(webhook)
```

Run this application with your normal ASGI server. Mofi does not create or run
one.

## Flask

```python
import os

from flask import Flask

from mofi import Donation, PaymentEvent
from mofi.integrations.flask import KoFiBlueprint

app = Flask(__name__)
webhook = KoFiBlueprint(
    "kofi",
    __name__,
    verification_token=os.environ["KOFI_VERIFICATION_TOKEN"],
    url_prefix="/webhooks/kofi",
)


@webhook.on(Donation)
def donation(event: Donation) -> None:
    record_donation(event.message_id, event.amount)


@webhook.on_payment
def every_payment(event: PaymentEvent) -> None:
    audit_payment(event.message_id, event.type)


app.register_blueprint(webhook)
```

If `verification_token` is omitted, the Blueprint reads
`app.config["MOFI_VERIFICATION_TOKEN"]`. Explicit configuration takes
precedence. Flask's async extra is installed by `mofi[flask]`, so handlers may
also be `async def` and still finish during the request.

## Django

```python
import os

from django.urls import path

from mofi import Donation, PaymentEvent
from mofi.integrations.django import KoFiWebhook

webhook = KoFiWebhook(
    verification_token=os.environ["KOFI_VERIFICATION_TOKEN"]
)


@webhook.on(Donation)
def donation(event: Donation) -> None:
    record_donation(event.message_id, event.amount)


@webhook.on_payment
def every_payment(event: PaymentEvent) -> None:
    audit_payment(event.message_id, event.type)


urlpatterns = [
    path("webhooks/kofi/", webhook.view, name="kofi_webhook"),
]
```

If `verification_token` is omitted, the view reads the
`MOFI_VERIFICATION_TOKEN` Django setting. The generated external webhook view
alone is CSRF-exempt; Mofi adds no application, middleware, model, or migration.

Runnable versions live in [`examples/`](examples/).

## Events and handler behavior

Known payments use these event classes:

| Ko-fi type | Mofi class |
| --- | --- |
| Donation | `Donation` |
| Subscription | `Subscription` |
| Commission | `Commission` |
| Shop Order | `ShopOrder` |

Every event extends `PaymentEvent`. A future type becomes `UnknownPayment`
instead of being rejected. The complete decoded object is available as
`event.raw`, and newly added fields are also retained by the Pydantic model.
Optional supporter messages, tier data, shop fields, shipping, and telephone
details may be absent. The Commission model intentionally exposes confirmed
common payment fields plus `raw`; it does not guess undocumented
Commission-only fields.

For a known event, Mofi calls handlers registered with `.on(...)` in
registration order, then handlers registered with `.on_payment`. Unknown events
call only `.on_payment` handlers. Dispatch is sequential. A valid event with no
handler is acknowledged with an empty HTTP 200 response.

Mofi returns HTTP 200 only after every selected handler finishes. Parsing and
validation failures return a native bad-request response, token mismatch returns
a forbidden response, and handler exceptions remain visible to the framework.
This lets Ko-fi retry unsuccessful deliveries.

## Retries and privacy

Ko-fi can retry a non-200 delivery with the same `message_id`. Mofi deliberately
delivers every attempt; it does not keep state or suppress duplicates. Use
`event.message_id` with your application's durable data store when an operation
must be idempotent.

Respect `event.is_public` before displaying supporter activity. `event.raw` can
contain the verification token, email, supporter message, transaction details,
shipping address, and telephone number. Do not log it or return it in responses;
apply your application's normal retention and access policies.

## Configure Ko-fi securely

1. Create a high-entropy token in Ko-fi's [Webhook settings](https://ko-fi.com/manage/webhooks).
2. Store the same token in your application's secret configuration.
3. Set the webhook URL to the HTTPS route mounted above.
4. Configure request-body limits in your framework or reverse proxy; Mofi keeps
   that policy with the host application.

Ko-fi puts the token inside the request body. It is a shared-secret check, not a
cryptographic request signature, and it cannot prevent replay if the token is
compromised. Rotate it in both Ko-fi and your application when exposure is
suspected.

## Upgrade from 0.2

Version 0.3 removes Mofi's server-owning `Mofi` class and `GlobalType`. See the
[0.3 migration guide](docs/migration-0.3.md) for direct FastAPI replacements and
the new Flask and Django integrations.

## Development

```bash
uv sync --all-extras
uv run pytest
uv run python -m compileall mofi examples
uv build
uv run python tests/verify_distribution.py
```
