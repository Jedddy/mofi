"""Smoke-test an installed Mofi wheel in an isolated environment."""

from __future__ import annotations

import importlib
import importlib.util
import sys


EXTRAS = {
    "base": None,
    "fastapi": "mofi.integrations.fastapi",
    "flask": "mofi.integrations.flask",
    "django": "mofi.integrations.django",
}


def main(extra: str) -> None:
    import mofi

    assert mofi.PaymentEvent
    assert not {"fastapi", "flask", "django"} & set(sys.modules)

    adapter = EXTRAS[extra]
    if adapter is not None:
        importlib.import_module(adapter)

    for framework in {"fastapi", "flask", "django"} - {extra}:
        assert importlib.util.find_spec(framework) is None


if __name__ == "__main__":
    main(sys.argv[1])
