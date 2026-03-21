"""Demo provider returning static fake metrics for testing."""

from __future__ import annotations

from typing import Any

from awareness_edge.providers.base import BaseProvider, CollectionResult


class DemoProvider(BaseProvider):
    """Returns static fake metrics — useful for testing the pipeline."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config or {})

    @property
    def source_name(self) -> str:
        return "demo"

    async def collect(self) -> CollectionResult:
        return CollectionResult(
            source="demo",
            tags=["demo"],
            metrics={
                "cpu_percent": 42.0,
                "memory_percent": 65.3,
                "uptime_hours": 1234,
            },
        )
