"""Optional framework dependencies stay outside Mofi's base import."""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest


def run_python(source: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", source],
        check=False,
        capture_output=True,
        text=True,
    )


def test_root_import_does_not_load_frameworks() -> None:
    result = run_python(
        "import sys, mofi; "
        "assert not {'fastapi', 'flask', 'django'} & set(sys.modules)"
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("module", "framework", "extra"),
    [
        ("mofi.integrations.fastapi", "fastapi", "fastapi"),
        ("mofi.integrations.flask", "flask", "flask"),
        ("mofi.integrations.django", "django", "django"),
    ],
)
def test_missing_adapter_dependency_has_an_installation_hint(
    module: str,
    framework: str,
    extra: str,
) -> None:
    source = textwrap.dedent(
        f"""
        import importlib
        import importlib.abc
        import sys

        class BlockFramework(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == {framework!r} or fullname.startswith({framework!r} + "."):
                    raise ModuleNotFoundError(name={framework!r})
                return None

        sys.meta_path.insert(0, BlockFramework())

        try:
            importlib.import_module({module!r})
        except ModuleNotFoundError as error:
            assert "mofi[{extra}]" in str(error)
        else:
            raise AssertionError("adapter import unexpectedly succeeded")
        """
    )

    result = run_python(source)

    assert result.returncode == 0, result.stderr
