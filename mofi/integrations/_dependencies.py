"""Consistent installation guidance for optional integration imports."""


def missing_dependency(framework: str, extra: str) -> ModuleNotFoundError:
    """Build an actionable error for an integration's missing dependency."""

    return ModuleNotFoundError(
        f"Mofi's {framework} integration is not installed. "
        f'Run `uv add "mofi[{extra}]"` or `pip install "mofi[{extra}]"`.'
    )
