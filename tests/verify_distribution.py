"""Verify that uv's wheel and source distribution contain the package."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path


def main() -> None:
    wheel = next(Path("dist").glob("*.whl"))
    source_distribution = next(Path("dist").glob("*.tar.gz"))

    with zipfile.ZipFile(wheel) as archive:
        wheel_files = {
            entry.filename
            for entry in archive.infolist()
            if entry.filename.startswith("mofi/") and not entry.is_dir()
        }

    with tarfile.open(source_distribution) as archive:
        source_files = {
            entry.name[entry.name.index("mofi/") :]
            for entry in archive.getmembers()
            if "/mofi/" in entry.name and entry.isfile()
        }

    expected_adapters = {
        "mofi/integrations/fastapi.py",
        "mofi/integrations/flask.py",
        "mofi/integrations/django.py",
    }
    assert expected_adapters <= wheel_files
    assert wheel_files == source_files
    assert not any(name.startswith("tests/") for name in wheel_files)


if __name__ == "__main__":
    main()
