"""Base provider interface for data collection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CollectionResult:
    """Data returned by a provider's collect() call."""

    source: str
    tags: list[str]
    metrics: dict[str, Any]
    inventory: dict[str, Any] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract base class for awareness-edge data providers.

    Each provider connects to a source system (MCP server, API, etc.),
    collects metrics, and returns a CollectionResult.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this provider's data source."""

    @abstractmethod
    async def collect(self) -> CollectionResult:
        """Collect metrics from the source system."""
