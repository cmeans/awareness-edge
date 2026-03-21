"""Provider registry and factory."""

from __future__ import annotations

from typing import Any

from awareness_edge.providers.base import BaseProvider, CollectionResult
from awareness_edge.providers.demo import DemoProvider

__all__ = ["BaseProvider", "CollectionResult", "get_provider", "register_provider"]

_REGISTRY: dict[str, type[BaseProvider]] = {}


def register_provider(name: str, cls: type[BaseProvider]) -> None:
    """Register a provider class by name."""
    _REGISTRY[name] = cls


def get_provider(name: str, config: dict[str, Any] | None = None) -> BaseProvider:
    """Instantiate a registered provider by name."""
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        msg = f"Unknown provider {name!r}. Available: {available}"
        raise KeyError(msg)
    return cls(config or {})


# Built-in providers
register_provider("demo", DemoProvider)
