"""Sink registry and factory."""

from __future__ import annotations

from typing import Any

from awareness_edge.sinks.base import BaseSink, SinkResult
from awareness_edge.sinks.demo import DemoSink

__all__ = ["BaseSink", "SinkResult", "get_sink", "register_sink"]

_SINK_REGISTRY: dict[str, type[BaseSink]] = {}


def register_sink(name: str, cls: type[BaseSink]) -> None:
    """Register a sink class by name."""
    _SINK_REGISTRY[name] = cls


def get_sink(name: str, config: dict[str, Any] | None = None) -> BaseSink:
    """Instantiate a registered sink by name."""
    cls = _SINK_REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_SINK_REGISTRY)) or "(none)"
        msg = f"Unknown sink {name!r}. Available: {available}"
        raise KeyError(msg)
    return cls(config or {})


# Built-in sinks
register_sink("demo", DemoSink)
