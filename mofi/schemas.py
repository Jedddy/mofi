from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel


class _Base(BaseModel):
    verification_token: str
    message_id: str
    timestamp: datetime
    is_public: bool
    from_name: str
    amount: str
    url: str
    email: str
    currency: str
    kofi_transaction_id: str


class ShopItem(BaseModel):
    """Represents a shop item.

    Attributes:
        direct_link_code (str): The direct link code of the item.
        variation_name (str): The name of the variation.
        quantity (int): The quantity of the item.
    """

    direct_link_code: str
    variation_name: str
    quantity: int


class Shipping(BaseModel):
    """Represents shipping information.

    Attributes:
        full_name (str): The full name of the recipient.
        street_address (str): The street address of the recipient.
        city (str): The city of the recipient.
        state_or_province (str): The state or province of the recipient.
        postal_code (str): The postal code of the recipient.
        country (str): The country of the recipient.
        country_code (str): The country code of the recipient.
        telephone (str): The telephone number of the recipient.
    """

    full_name: str
    street_address: str
    city: str
    state_or_province: str
    postal_code: str
    country: str
    country_code: str
    telephone: str


class GlobalType(_Base):
    """Represents a global type.

    Attributes:
        verification_token (str): The verification token.
        message_id (str): The message ID.
        timestamp (datetime): The timestamp.
        type (str): The type.
        is_public (bool): Whether the donation is public.
        from_name (str): The name of the donor.
        message (str): The message of the donor.
        amount (str): The amount of the donation.
        url (str): The URL of the donation.
        email (str): The email of the donor.
        currency (str): The currency of the donation.
        is_subscription_payment (bool): Whether the donation is a subscription payment.
        is_first_subscription_payment (bool): Whether the donation is
            the first subscription payment.
        kofi_transaction_id (str): The transaction ID of the donation.
        shop_items (list[ShopItem]): The shop items of the donation.
        tier_name (str): The name of the tier.
        shipping (Shipping): The shipping information.
    """

    type: str
    message: Union[str, None] = None
    is_subscription_payment: bool
    is_first_subscription_payment: bool
    shop_items: Union[list[ShopItem], None] = None
    tier_name: Union[str, None] = None
    shipping: Union[Shipping, None] = None


class Donation(_Base):
    """Represents a donation.

    Attributes:
        verification_token (str): The verification token.
        message_id (str): The message ID.
        timestamp (datetime): The timestamp.
        type (str): The type.
        is_public (bool): Whether the donation is public.
        from_name (str): The name of the donor.
        message (str): The message of the donor.
        amount (str): The amount of the donation.
        url (str): The URL of the donation.
        email (str): The email of the donor.
        currency (str): The currency of the donation.
        kofi_transaction_id (str): The transaction ID of the donation.
    """

    type: Literal["Donation"]
    message: str


class Subscription(_Base):
    """Represents a subscription.

    Attributes:
        verification_token (str): The verification token.
        message_id (str): The message ID.
        timestamp (datetime): The timestamp.
        type (str): The type.
        is_public (bool): Whether the donation is public.
        from_name (str): The name of the donor.
        message (str): The message of the donor.
        amount (str): The amount of the donation.
        url (str): The URL of the donation.
        email (str): The email of the donor.
        currency (str): The currency of the donation.
        is_subscription_payment (bool): Whether the donation is a subscription payment.
        is_first_subscription_payment (bool): Whether the donation is
            the first subscription payment.
        kofi_transaction_id (str): The transaction ID of the donation.
        tier_name (str): The name of the tier.
    """

    type: Literal["Subscription"]
    message: Union[str, None] = None
    is_subscription_payment: bool
    is_first_subscription_payment: bool
    tier_name: Union[str, None] = None


class ShopOrder(_Base):
    """Represents a shop order.

    Attributes:
        verification_token (str): The verification token.
        message_id (str): The message ID.
        timestamp (datetime): The timestamp.
        type (str): The type.
        is_public (bool): Whether the donation is public.
        from_name (str): The name of the donor.
        amount (str): The amount of the donation.
        url (str): The URL of the donation.
        email (str): The email of the donor.
        currency (str): The currency of the donation.
        kofi_transaction_id (str): The transaction ID of the donation.
        shop_items (list[ShopItem]): The shop items of the donation.
        shipping (Shipping): The shipping information.
    """

    type: Literal["Shop Order"]
    shop_items: list[ShopItem]
    shipping: Shipping
