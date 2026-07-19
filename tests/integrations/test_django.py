"""Django-native Ko-fi webhook integration behavior."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterator
from urllib.parse import urlencode

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django_settings")

import django

django.setup()

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import Client, override_settings
from django.urls import clear_url_caches, path, reverse

from mofi import Donation, PaymentEvent, Subscription
from mofi.integrations.django import KoFiWebhook
from tests import django_urls
from tests.support import FIXTURE_TOKEN, PAYMENT_CASES, encoded_payload, load_payload


TOKEN = FIXTURE_TOKEN


@pytest.fixture
def install_urls() -> Iterator[Callable[..., None]]:
    previous = django_urls.urlpatterns

    def install(*patterns: object) -> None:
        django_urls.urlpatterns = list(patterns)
        clear_url_caches()

    yield install
    django_urls.urlpatterns = previous
    clear_url_caches()


@pytest.mark.parametrize(
    ("fixture_name", "event_class"),
    PAYMENT_CASES,
)
def test_known_and_unknown_payments_reach_all_payment_handlers(
    install_urls: Callable[..., None],
    fixture_name: str,
    event_class: type[PaymentEvent],
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)
    received: list[PaymentEvent] = []

    @webhook.on_payment
    def receive(event: PaymentEvent) -> None:
        received.append(event)

    install_urls(path("webhooks/kofi/", webhook.view, name="kofi_webhook"))

    response = Client().post(
        "/webhooks/kofi/",
        data={"data": encoded_payload(fixture_name)},
    )

    assert response.status_code == 200
    assert response.content == b""
    assert len(received) == 1
    assert isinstance(received[0], event_class)
    assert received[0].raw == load_payload(fixture_name)
    assert reverse("kofi_webhook") == "/webhooks/kofi/"


def test_specific_handlers_finish_before_all_payment_handlers(
    install_urls: Callable[..., None],
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)
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

    install_urls(path("", webhook.view))

    response = Client().post("/", data={"data": encoded_payload("donation.json")})

    assert response.status_code == 200
    assert calls == ["specific-first", "specific-second", "all"]


def test_async_handlers_finish_inside_the_request(
    install_urls: Callable[..., None],
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)
    calls: list[str] = []

    @webhook.on(Subscription)
    async def receive(_: Subscription) -> None:
        calls.append("async-complete")

    install_urls(path("", webhook.view))

    response = Client().post("/", data={"data": encoded_payload("subscription.json")})

    assert response.status_code == 200
    assert calls == ["async-complete"]


@override_settings(MOFI_VERIFICATION_TOKEN=TOKEN)
def test_django_settings_supply_the_token(install_urls: Callable[..., None]) -> None:
    webhook = KoFiWebhook()
    received: list[str] = []
    webhook.on_payment(lambda event: received.append(event.message_id))
    install_urls(path("", webhook.view))

    response = Client().post("/", data={"data": encoded_payload("donation.json")})

    assert response.status_code == 200
    assert received == ["00000000-0000-4000-8000-000000000001"]


@override_settings(MOFI_VERIFICATION_TOKEN="wrong-token")
def test_explicit_token_takes_precedence_over_django_settings(
    install_urls: Callable[..., None],
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)
    install_urls(path("", webhook.view))

    response = Client().post("/", data={"data": encoded_payload("donation.json")})

    assert response.status_code == 200


def test_only_the_generated_webhook_view_is_csrf_exempt(
    install_urls: Callable[..., None],
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)

    def protected(_: HttpRequest) -> HttpResponse:
        return HttpResponse()

    install_urls(path("webhook/", webhook.view), path("protected/", protected))
    client = Client(enforce_csrf_checks=True)

    webhook_response = client.post(
        "/webhook/",
        data={"data": encoded_payload("donation.json")},
    )
    protected_response = client.post("/protected/")

    assert webhook_response.status_code == 200
    assert protected_response.status_code == 403


def test_handler_failure_stops_dispatch_and_prevents_acknowledgement(
    install_urls: Callable[..., None],
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)
    calls: list[str] = []

    @webhook.on(Donation)
    def fail(_: Donation) -> None:
        calls.append("specific")
        raise RuntimeError("application failure")

    @webhook.on_payment
    def must_not_run(_: PaymentEvent) -> None:
        calls.append("all")

    install_urls(path("", webhook.view))

    response = Client(raise_request_exception=False).post(
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
    install_urls: Callable[..., None],
    data: object,
    expected_status: int,
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)
    received: list[PaymentEvent] = []
    webhook.on_payment(received.append)
    install_urls(path("", webhook.view))
    encoded = data if isinstance(data, str) else json.dumps(data)

    response = Client().post("/", data={"data": encoded})

    assert response.status_code == expected_status
    assert received == []
    assert TOKEN not in response.content.decode()
    assert "Invalid Supporter" not in response.content.decode()


def test_duplicate_ids_are_dispatched_twice(
    install_urls: Callable[..., None],
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)
    received: list[str] = []
    webhook.on_payment(lambda event: received.append(event.message_id))
    install_urls(path("", webhook.view))
    client = Client()

    first = client.post("/", data={"data": encoded_payload("duplicate_first.json")})
    retry = client.post("/", data={"data": encoded_payload("duplicate_retry.json")})

    assert first.status_code == retry.status_code == 200
    assert received == [
        "00000000-0000-4000-8000-000000000009",
        "00000000-0000-4000-8000-000000000009",
    ]


def test_webhook_instances_keep_tokens_and_handlers_isolated(
    install_urls: Callable[..., None],
) -> None:
    first = KoFiWebhook(verification_token="first-token")
    second = KoFiWebhook(verification_token="second-token")
    calls: list[str] = []
    first.on_payment(lambda _: calls.append("first"))
    second.on_payment(lambda _: calls.append("second"))
    install_urls(path("first/", first.view), path("second/", second.view))
    first_payload = load_payload("donation.json")
    first_payload["verification_token"] = "first-token"
    second_payload = load_payload("donation.json")
    second_payload["verification_token"] = "second-token"
    client = Client()

    first_response = client.post("/first/", data={"data": json.dumps(first_payload)})
    second_response = client.post("/second/", data={"data": json.dumps(second_payload)})
    wrong_response = client.post("/first/", data={"data": json.dumps(second_payload)})

    assert first_response.status_code == second_response.status_code == 200
    assert wrong_response.status_code == 403
    assert calls == ["first", "second"]


def test_missing_or_repeated_data_fields_are_bad_requests(
    install_urls: Callable[..., None],
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)
    install_urls(path("", webhook.view))
    client = Client()

    missing = client.post("/", data={})
    repeated = client.generic(
        "POST",
        "/",
        data=urlencode(
            [("data", encoded_payload("donation.json")), ("data", "duplicate")]
        ),
        content_type="application/x-www-form-urlencoded",
    )

    assert missing.status_code == 400
    assert repeated.status_code == 400


def test_non_post_methods_use_django_response_conventions(
    install_urls: Callable[..., None],
) -> None:
    webhook = KoFiWebhook(verification_token=TOKEN)
    install_urls(path("", webhook.view))

    response = Client().get("/")

    assert response.status_code == 405
