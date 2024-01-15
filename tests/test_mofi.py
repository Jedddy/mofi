import json

import pytest
import pytest_asyncio
from httpx import AsyncClient

from mofi import Mofi, GlobalType, Donation, Subscription, ShopOrder


app = Mofi("token")


@app.callback("global")
async def global_type(data: GlobalType):
    assert data.email == "jo.example@example.com"
    assert data.type in ["Donation", "Subscription", "Shop Order"]


@app.callback("donation")
async def donation_type(data: Donation):
    assert not hasattr(data, "shop_items")
    assert not hasattr(data, "tier_name")
    assert not hasattr(data, "shipping")


@app.callback("subscription")
async def subscription_type(data: Subscription):
    assert hasattr(data, "is_subscription_payment")
    assert hasattr(data, "is_first_subscription_payment")
    assert not hasattr(data, "shop_items")
    assert not hasattr(data, "shipping")


@app.callback("shop_order")
async def shop_order_type(data: ShopOrder):
    assert hasattr(data, "shop_items")
    assert hasattr(data, "shipping")
    assert not hasattr(data, "tier_name")


app._setup()
pytestmark = pytest.mark.asyncio(scope="module")


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(app=app._app) as client:
        yield client


donation = {
    "verification_token": "token",
    "message_id": "2b53017c-860e-47e1-86b4-599a28d4d098",
    "timestamp": "2024-01-14T03:56:47Z",
    "type": "Donation",
    "is_public": True,
    "from_name": "Jo Example",
    "message": "Good luck with the integration!",
    "amount": "3.00",
    "url": "https://ko-fi.com/Home/CoffeeShop?txid=00000000-1111-2222-3333-444444444444",
    "email": "jo.example@example.com",
    "currency": "USD",
    "is_subscription_payment": False,
    "is_first_subscription_payment": False,
    "kofi_transaction_id": "00000000-1111-2222-3333-444444444444",
    "shop_items": None,
    "tier_name": None,
    "shipping": None,
}

first_monthly = {
    "verification_token": "token",
    "message_id": "0361339f-4897-484f-ad30-d444651481db",
    "timestamp": "2024-01-14T03:56:47Z",
    "type": "Subscription",
    "is_public": True,
    "from_name": "Jo Example",
    "message": "Good luck with the integration!",
    "amount": "3.00",
    "url": "https://ko-fi.com/Home/CoffeeShop?txid=00000000-1111-2222-3333-444444444444",
    "email": "jo.example@example.com",
    "currency": "USD",
    "is_subscription_payment": True,
    "is_first_subscription_payment": True,
    "kofi_transaction_id": "00000000-1111-2222-3333-444444444444",
    "shop_items": None,
    "tier_name": None,
    "shipping": None,
}

subsequent_sub = {
    "verification_token": "token",
    "message_id": "f6441f3d-a76f-498f-ba59-6e258c8186ad",
    "timestamp": "2024-01-14T03:56:47Z",
    "type": "Subscription",
    "is_public": True,
    "from_name": "Jo Example",
    "message": None,
    "amount": "5.00",
    "url": "https://ko-fi.com/Home/CoffeeShop?txid=00000000-1111-2222-3333-444444444444",
    "email": "jo.example@example.com",
    "currency": "USD",
    "is_subscription_payment": True,
    "is_first_subscription_payment": False,
    "kofi_transaction_id": "00000000-1111-2222-3333-444444444444",
    "shop_items": None,
    "tier_name": "Bronze",
    "shipping": None,
}

shop_order = {
    "verification_token": "token",
    "message_id": "633a0988-55c9-48c7-b277-b810f61afd66",
    "timestamp": "2024-01-14T03:56:47Z",
    "type": "Shop Order",
    "is_public": True,
    "from_name": "Jo Example",
    "message": None,
    "amount": "27.95",
    "url": "https://ko-fi.com/Home/CoffeeShop?txid=00000000-1111-2222-3333-444444444444",
    "email": "jo.example@example.com",
    "currency": "USD",
    "is_subscription_payment": False,
    "is_first_subscription_payment": False,
    "kofi_transaction_id": "00000000-1111-2222-3333-444444444444",
    "shop_items": [
        {"direct_link_code": "1a2b3c4d5e", "variation_name": "Blue", "quantity": 1},
        {"direct_link_code": "a1b2c3d4e5", "variation_name": "Large", "quantity": 5},
    ],
    "tier_name": None,
    "shipping": {
        "full_name": "Ko-fi Mail Room",
        "street_address": "123 The Old Exchange, High Street",
        "city": "Bigville",
        "state_or_province": "Kansas",
        "postal_code": "12345",
        "country": "United States",
        "country_code": "US",
        "telephone": "+1-212-456-7890",
    },
}


async def test_global(client: AsyncClient):
    r = await client.post(
        "http://127.0.0.1:8000",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "data": json.dumps(donation),
        },
    )

    r2 = await client.post(
        "http://127.0.0.1:8000",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "data": json.dumps(subsequent_sub),
        },
    )

    r3 = await client.post(
        "http://127.0.0.1:8000",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "data": json.dumps(first_monthly),
        },
    )

    assert r.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200


async def test_donation(client: AsyncClient):
    r = await client.post(
        "http://127.0.0.1:8000",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "data": json.dumps(donation),
        },
    )

    assert r.status_code == 200


async def test_subsciption(client: AsyncClient):
    r = await client.post(
        "http://127.0.0.1:8000",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "data": json.dumps(first_monthly),
        },
    )

    assert r.status_code == 200


async def test_shop_order(client: AsyncClient):
    r = await client.post(
        "http://127.0.0.1:8000",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "data": json.dumps(shop_order),
        },
    )

    assert r.status_code == 200
