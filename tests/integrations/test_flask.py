"""Flask-native Ko-fi webhook integration behavior."""

from __future__ import annotations

import json
from urllib.parse import urlencode

import pytest
from flask import Flask

from mofi import Donation, PaymentEvent, Subscription
from mofi.integrations.flask import KoFiBlueprint
from tests.support import FIXTURE_TOKEN, PAYMENT_CASES, encoded_payload, load_payload


TOKEN = FIXTURE_TOKEN


def create_app(webhook: KoFiBlueprint) -> Flask:
    app = Flask(__name__)
    app.config.update(TESTING=True)
    app.register_blueprint(webhook)
    return app


@pytest.mark.parametrize(
    ("fixture_name", "event_class"),
    PAYMENT_CASES,
)
def test_known_and_unknown_payments_reach_all_payment_handlers(
    fixture_name: str,
    event_class: type[PaymentEvent],
) -> None:
    webhook = KoFiBlueprint("kofi", __name__, verification_token=TOKEN)
    received: list[PaymentEvent] = []

    @webhook.on_payment
    def receive(event: PaymentEvent) -> None:
        received.append(event)

    client = create_app(webhook).test_client()

    response = client.post("/", data={"data": encoded_payload(fixture_name)})

    assert response.status_code == 200
    assert response.data == b""
    assert len(received) == 1
    assert isinstance(received[0], event_class)
    assert received[0].raw == load_payload(fixture_name)


def test_specific_handlers_finish_before_all_payment_handlers() -> None:
    webhook = KoFiBlueprint("kofi", __name__, verification_token=TOKEN)
    calls: list[str] = []

    @webhook.on(Donation)
    def first(_: Donation) -> None:
        calls.append("specific-first")

    @webhook.on(Donation)
    def second(_: Donation) -> None:
        calls.append("specific-second")

    @webhook.on_payment
    def all_payments(_: PaymentEvent) -> None:
        calls.append("all")

    response = create_app(webhook).test_client().post(
        "/",
        data={"data": encoded_payload("donation.json")},
    )

    assert response.status_code == 200
    assert calls == ["specific-first", "specific-second", "all"]


def test_async_handlers_finish_inside_the_request() -> None:
    webhook = KoFiBlueprint("kofi", __name__, verification_token=TOKEN)
    calls: list[str] = []

    @webhook.on(Subscription)
    async def receive(_: Subscription) -> None:
        calls.append("async-complete")

    response = create_app(webhook).test_client().post(
        "/",
        data={"data": encoded_payload("subscription.json")},
    )

    assert response.status_code == 200
    assert calls == ["async-complete"]


def test_application_config_supplies_the_token() -> None:
    webhook = KoFiBlueprint("kofi", __name__)
    received: list[str] = []
    webhook.on_payment(lambda event: received.append(event.message_id))
    app = Flask(__name__)
    app.config.update(TESTING=True, MOFI_VERIFICATION_TOKEN=TOKEN)
    app.register_blueprint(webhook, url_prefix="/payments/kofi")

    response = app.test_client().post(
        "/payments/kofi/",
        data={"data": encoded_payload("donation.json")},
    )

    assert response.status_code == 200
    assert received == ["00000000-0000-4000-8000-000000000001"]


def test_explicit_token_takes_precedence_over_application_config() -> None:
    webhook = KoFiBlueprint("kofi", __name__, verification_token=TOKEN)
    app = Flask(__name__)
    app.config.update(TESTING=True, MOFI_VERIFICATION_TOKEN="wrong-token")
    app.register_blueprint(webhook)

    response = app.test_client().post(
        "/",
        data={"data": encoded_payload("donation.json")},
    )

    assert response.status_code == 200


def test_handler_failure_stops_dispatch_and_prevents_acknowledgement() -> None:
    webhook = KoFiBlueprint("kofi", __name__, verification_token=TOKEN)
    calls: list[str] = []

    @webhook.on(Donation)
    def fail(_: Donation) -> None:
        calls.append("specific")
        raise RuntimeError("application failure")

    @webhook.on_payment
    def must_not_run(_: PaymentEvent) -> None:
        calls.append("all")

    app = create_app(webhook)
    app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)

    response = app.test_client().post(
        "/",
        data={"data": encoded_payload("donation.json")},
    )

    assert response.status_code == 500
    assert calls == ["specific"]


@pytest.mark.parametrize(
    ("data", "expected_status"),
    [
        (load_payload("invalid_token.json"), 403),
        ("not json", 400),
        ([], 400),
    ],
)
def test_invalid_requests_do_not_reach_handlers(
    data: object,
    expected_status: int,
) -> None:
    webhook = KoFiBlueprint("kofi", __name__, verification_token=TOKEN)
    received: list[PaymentEvent] = []
    webhook.on_payment(received.append)
    encoded = data if isinstance(data, str) else json.dumps(data)

    response = create_app(webhook).test_client().post("/", data={"data": encoded})

    assert response.status_code == expected_status
    assert received == []
    assert TOKEN not in response.text
    assert "Invalid Supporter" not in response.text


def test_duplicate_ids_are_dispatched_twice() -> None:
    webhook = KoFiBlueprint("kofi", __name__, verification_token=TOKEN)
    received: list[str] = []
    webhook.on_payment(lambda event: received.append(event.message_id))
    client = create_app(webhook).test_client()

    first = client.post("/", data={"data": encoded_payload("duplicate_first.json")})
    retry = client.post("/", data={"data": encoded_payload("duplicate_retry.json")})

    assert first.status_code == retry.status_code == 200
    assert received == [
        "00000000-0000-4000-8000-000000000009",
        "00000000-0000-4000-8000-000000000009",
    ]


def test_blueprint_instances_keep_tokens_and_handlers_isolated() -> None:
    app = Flask(__name__)
    app.config.update(TESTING=True)
    first = KoFiBlueprint("first_kofi", __name__, verification_token="first-token")
    second = KoFiBlueprint("second_kofi", __name__, verification_token="second-token")
    calls: list[str] = []
    first.on_payment(lambda _: calls.append("first"))
    second.on_payment(lambda _: calls.append("second"))
    app.register_blueprint(first, url_prefix="/first")
    app.register_blueprint(second, url_prefix="/second")
    first_payload = load_payload("donation.json")
    first_payload["verification_token"] = "first-token"
    second_payload = load_payload("donation.json")
    second_payload["verification_token"] = "second-token"
    client = app.test_client()

    first_response = client.post("/first/", data={"data": json.dumps(first_payload)})
    second_response = client.post("/second/", data={"data": json.dumps(second_payload)})
    wrong_response = client.post("/first/", data={"data": json.dumps(second_payload)})

    assert first_response.status_code == second_response.status_code == 200
    assert wrong_response.status_code == 403
    assert calls == ["first", "second"]


def test_missing_or_repeated_data_fields_are_bad_requests() -> None:
    client = create_app(
        KoFiBlueprint("kofi", __name__, verification_token=TOKEN)
    ).test_client()

    missing = client.post("/", data={})
    repeated = client.post(
        "/",
        data=urlencode(
            [("data", encoded_payload("donation.json")), ("data", "duplicate")]
        ),
        content_type="application/x-www-form-urlencoded",
    )

    assert missing.status_code == 400
    assert repeated.status_code == 400


def test_non_post_methods_use_flask_routing_behavior() -> None:
    response = create_app(
        KoFiBlueprint("kofi", __name__, verification_token=TOKEN)
    ).test_client().get("/")

    assert response.status_code == 405
