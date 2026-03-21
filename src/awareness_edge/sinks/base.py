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

    @property
    @abstractmethod
    def sink_name(self) -> str:
        """Unique identifier for this sink."""

    @abstractmethod
    async def push(self, client: AwarenessClient) -> SinkResult:
        """Read from awareness and push to the external target."""
