"""FastAPI-native Ko-fi webhook integration behavior."""

from __future__ import annotations

import json
from urllib.parse import urlencode

import httpx
import pytest
from fastapi import FastAPI

from mofi import Donation, PaymentEvent, Subscription
from mofi.integrations.fastapi import KoFiRouter
from tests.support import FIXTURE_TOKEN, PAYMENT_CASES, encoded_payload, load_payload


TOKEN = FIXTURE_TOKEN


async def post(app: FastAPI, path: str, data: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        return await client.post(path, data={"data": data})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fixture_name", "event_class"),
    PAYMENT_CASES,
)
async def test_known_and_unknown_payments_reach_all_payment_handlers(
    fixture_name: str,
    event_class: type[PaymentEvent],
) -> None:
    app = FastAPI()
    webhook = KoFiRouter(TOKEN, prefix="/webhooks/kofi")
    received: list[PaymentEvent] = []

    @webhook.on_payment
    async def receive(event: PaymentEvent) -> None:
        received.append(event)

    app.include_router(webhook)

    response = await post(app, "/webhooks/kofi/", encoded_payload(fixture_name))

    assert response.status_code == 200
    assert response.content == b""
    assert len(received) == 1
    assert isinstance(received[0], event_class)
    assert received[0].raw == load_payload(fixture_name)


@pytest.mark.asyncio
async def test_specific_handlers_finish_before_all_payment_handlers() -> None:
    app = FastAPI()
    webhook = KoFiRouter(TOKEN)
    calls: list[str] = []

    @webhook.on(Donation)
    def first(_: Donation) -> None:
        calls.append("specific-sync")

    @webhook.on(Donation)
    async def second(_: Donation) -> None:
        calls.append("specific-async")

    @webhook.on_payment
    def all_payments(_: PaymentEvent) -> None:
        calls.append("all")

    app.include_router(webhook)

    response = await post(app, "/", encoded_payload("donation.json"))

    assert response.status_code == 200
    assert calls == ["specific-sync", "specific-async", "all"]


@pytest.mark.asyncio
async def test_global_only_and_no_handler_configurations_are_acknowledged() -> None:
    global_app = FastAPI()
    global_webhook = KoFiRouter(TOKEN)
    received: list[str] = []

    @global_webhook.on_payment
    def receive(event: PaymentEvent) -> None:
        received.append(event.type)

    global_app.include_router(global_webhook)
    empty_app = FastAPI()
    empty_app.include_router(KoFiRouter(TOKEN))

    global_response = await post(global_app, "/", encoded_payload("subscription.json"))
    empty_response = await post(empty_app, "/", encoded_payload("donation.json"))

    assert global_response.status_code == 200
    assert empty_response.status_code == 200
    assert received == ["Subscription"]


@pytest.mark.asyncio
async def test_handler_failure_stops_dispatch_and_prevents_acknowledgement() -> None:
    app = FastAPI()
    webhook = KoFiRouter(TOKEN)
    calls: list[str] = []

    @webhook.on(Donation)
    def fail(_: Donation) -> None:
        calls.append("specific")
        raise RuntimeError("application failure")

    @webhook.on_payment
    def must_not_run(_: PaymentEvent) -> None:
        calls.append("all")

    app.include_router(webhook)

    response = await post(app, "/", encoded_payload("donation.json"))

    assert response.status_code == 500
    assert calls == ["specific"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("data", "expected_status"),
    [
        ((load_payload("invalid_token.json")), 403),
        ("not json", 400),
        ([], 400),
    ],
)
async def test_invalid_requests_do_not_reach_handlers(
    data: object,
    expected_status: int,
) -> None:
    app = FastAPI()
    webhook = KoFiRouter(TOKEN)
    received: list[PaymentEvent] = []
    webhook.on_payment(received.append)
    app.include_router(webhook)
    encoded = data if isinstance(data, str) else json.dumps(data)

    response = await post(app, "/", encoded)

    assert response.status_code == expected_status
    assert received == []
    assert TOKEN not in response.text
    assert "Invalid Supporter" not in response.text


@pytest.mark.asyncio
async def test_duplicate_ids_are_dispatched_twice() -> None:
    app = FastAPI()
    webhook = KoFiRouter(TOKEN)
    received: list[str] = []
    webhook.on_payment(lambda event: received.append(event.message_id))
    app.include_router(webhook)

    first = await post(app, "/", encoded_payload("duplicate_first.json"))
    retry = await post(app, "/", encoded_payload("duplicate_retry.json"))

    assert first.status_code == retry.status_code == 200
    assert received == [
        "00000000-0000-4000-8000-000000000009",
        "00000000-0000-4000-8000-000000000009",
    ]


@pytest.mark.asyncio
async def test_router_instances_keep_tokens_and_handlers_isolated() -> None:
    app = FastAPI()
    first = KoFiRouter("first-token", prefix="/first")
    second = KoFiRouter("second-token", prefix="/second")
    calls: list[str] = []
    first.on_payment(lambda _: calls.append("first"))
    second.on_payment(lambda _: calls.append("second"))
    app.include_router(first)
    app.include_router(second)
    first_payload = load_payload("donation.json")
    first_payload["verification_token"] = "first-token"
    second_payload = load_payload("donation.json")
    second_payload["verification_token"] = "second-token"

    first_response = await post(app, "/first/", json.dumps(first_payload))
    second_response = await post(app, "/second/", json.dumps(second_payload))
    wrong_response = await post(app, "/first/", json.dumps(second_payload))

    assert first_response.status_code == second_response.status_code == 200
    assert wrong_response.status_code == 403
    assert calls == ["first", "second"]


@pytest.mark.asyncio
async def test_missing_or_repeated_data_fields_are_bad_requests() -> None:
    app = FastAPI()
    webhook = KoFiRouter(TOKEN)
    app.include_router(webhook)
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        missing = await client.post("/", data={})
        repeated = await client.post(
            "/",
            content=urlencode(
                [("data", encoded_payload("donation.json")), ("data", "duplicate")]
            ),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert missing.status_code == 400
    assert repeated.status_code == 400


@pytest.mark.asyncio
async def test_non_post_methods_use_fastapi_routing_behavior() -> None:
    app = FastAPI()
    app.include_router(KoFiRouter(TOKEN))
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.get("/")

    assert response.status_code == 405
