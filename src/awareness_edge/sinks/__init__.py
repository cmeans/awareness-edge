# awareness-edge — bridge between your systems and AI awareness
# Copyright (C) 2026 Chris Means
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Sink registry and factory."""

from __future__ import annotations

from typing import Any

from awareness_edge.sinks.base import BaseSink, SinkResult
from awareness_edge.sinks.demo import DemoSink
from awareness_edge.sinks.github import GitHubSink

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
register_sink("github", GitHubSink)
