"""Documentation examples remain importable and migration guidance complete."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize(
    ("module", "attribute"),
    [
        ("examples.fastapi_app", "app"),
        ("examples.flask_app", "app"),
        ("examples.django_app.urls", "urlpatterns"),
    ],
)
def test_framework_examples_import(module: str, attribute: str) -> None:
    environment = {
        **os.environ,
        "KOFI_VERIFICATION_TOKEN": "example-token",
        "DJANGO_SECRET_KEY": "example-secret-key",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import {module} as example; assert example.{attribute}",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=environment,
    )

    assert result.returncode == 0, result.stderr


def test_examples_do_not_own_servers_or_databases() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "examples").rglob("*.py")
    )

    assert "Mofi(" not in source
    assert "uvicorn.run" not in source
    assert "app.run(" not in source
    assert "django.db" not in source


def test_migration_guide_maps_every_removed_entry_point() -> None:
    guide = (ROOT / "docs" / "migration-0.3.md").read_text(encoding="utf-8")

    for old_api in ["`Mofi(...)`", "`.callback(...)`", "`.as_router()`", "`.run()`", "`GlobalType`"]:
        assert old_api in guide

    assert 'uv add "mofi[fastapi]"' in guide
    assert "PaymentEvent" in guide
