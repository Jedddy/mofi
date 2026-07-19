"""Secret-safe errors raised by the framework-neutral webhook core."""


class WebhookError(Exception):
    """Base class for webhook parsing and verification failures."""


class InvalidPayload(WebhookError):
    """The form value is not a JSON object."""

    def __init__(self) -> None:
        super().__init__("Invalid Ko-fi webhook payload.")


class InvalidEvent(WebhookError):
    """The decoded object is not a valid payment event."""

    def __init__(self) -> None:
        super().__init__("Invalid Ko-fi payment event.")


class VerificationFailed(WebhookError):
    """The payload token does not match the configured shared token."""

    def __init__(self) -> None:
        super().__init__("Ko-fi webhook verification failed.")


__all__ = ["InvalidEvent", "InvalidPayload", "VerificationFailed", "WebhookError"]
