# Migrating from Mofi 0.2 to 0.3

Mofi 0.3 is a pre-1.0 breaking release. It stops owning a FastAPI application
and server, adds Flask and Django integrations, and moves payment parsing into a
framework-independent core.

## Install the framework extra

FastAPI is no longer a base dependency. Replace the old installation with the
extra for your application:

```bash
uv add "mofi[fastapi]"
```

Flask and Django applications use `mofi[flask]` and `mofi[django]`. A base
`mofi` install exposes event models without installing a web framework. Uvicorn
is no longer a Mofi runtime dependency; keep using the server chosen by your
application.

## API mapping

| Mofi 0.2 | Mofi 0.3 |
| --- | --- |
| `Mofi(...)` | `KoFiRouter(...)`, `KoFiBlueprint(...)`, or `KoFiWebhook(...)` |
| `.callback(...)` | `.on(EventClass)` for a known type, or `.on_payment` for every payment |
| `.as_router()` | Include the `KoFiRouter` instance with `app.include_router(...)` |
| `.run()` | Run the containing FastAPI, Flask, or Django application normally |
| `GlobalType` | `PaymentEvent` for all-payment handlers |
| `Donation`, `Subscription`, `ShopOrder` | Same root imports; `Commission` and `UnknownPayment` are new |

There is no compatibility shim for the removed `Mofi` class. This keeps server
lifecycle, routing, configuration, and errors under the host framework.

## FastAPI migration

Mofi 0.2 created an application or returned an internal router:

```python
from mofi import Donation, Mofi

webhook = Mofi("token")


@webhook.callback("donation")
async def donation(event: Donation) -> None:
    ...


app.include_router(webhook.as_router())
```

Mofi 0.3 is itself an `APIRouter`:

```python
from fastapi import FastAPI

from mofi import Donation, PaymentEvent
from mofi.integrations.fastapi import KoFiRouter

app = FastAPI()
webhook = KoFiRouter("token", prefix="/webhooks/kofi")


@webhook.on(Donation)
async def donation(event: Donation) -> None:
    ...


@webhook.on_payment
async def every_payment(event: PaymentEvent) -> None:
    ...


app.include_router(webhook)
```

## Behavior changes

- Known-type handlers run first, followed by all-payment handlers. Mofi 0.2
  treated the global callback as a fallback and skipped it when a specific
  callback existed.
- `UnknownPayment` reaches all-payment handlers with the decoded payload in
  `event.raw`. Unknown types are no longer rejected.
- Added fields are retained, and nullable supporter, shop, tier, shipping, and
  telephone data no longer invalidate a payment.
- `message_id` is never deduplicated. Ko-fi retries are delivered again so the
  application can apply durable idempotency.
- Invalid payloads use the framework's bad-request response. A mismatched token
  uses its forbidden response.
- A handler exception stops dispatch and prevents HTTP 200, allowing Ko-fi to
  retry. Sync and async handlers both complete inside the request lifecycle.

## Security and payload handling

The Ko-fi verification token is a shared value inside the payload, not a
cryptographic signature. Keep the endpoint behind HTTPS and store the token in
normal application secret configuration. The complete `raw` mapping may contain
the token and supporter personal data; do not log it or return it from the
endpoint.
