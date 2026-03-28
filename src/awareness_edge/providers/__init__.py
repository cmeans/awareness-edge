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
