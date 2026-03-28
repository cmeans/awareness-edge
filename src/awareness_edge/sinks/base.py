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

"""Base sink interface for outbound data push."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from awareness_edge.core.client import AwarenessClient


@dataclass
class SinkResult:
    """Result of a sink's push() call."""

    sink_name: str
    items_pushed: int
    details: dict[str, Any] | None = None


class BaseSink(ABC):
    """Abstract base class for awareness-edge outbound sinks.

    Sinks read from awareness (via the client) and push data to
    external systems (GitHub, Slack, Notion, etc.).
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.dry_run: bool = False

    @property
    @abstractmethod
    def sink_name(self) -> str:
        """Unique identifier for this sink."""

    @abstractmethod
    async def push(self, client: AwarenessClient) -> SinkResult:
        """Read from awareness and push to the external target."""
