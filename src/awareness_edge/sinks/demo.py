"""Demo sink — logs what it would push, useful for testing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from awareness_edge.sinks.base import BaseSink, SinkResult

if TYPE_CHECKING:
    from awareness_edge.core.client import AwarenessClient

logger = logging.getLogger(__name__)


class DemoSink(BaseSink):
    """Logs a push action without writing to any external system."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config or {})

    @property
    def sink_name(self) -> str:
        return "demo"

    async def push(self, client: AwarenessClient) -> SinkResult:
        logger.info("DemoSink: would push data (no-op)")
        return SinkResult(sink_name="demo", items_pushed=0)
