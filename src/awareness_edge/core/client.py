"""Awareness MCP client — reports status and alerts to mcp-awareness."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AwarenessClient:
    """Client for writing to the mcp-awareness service.

    Currently uses httpx to call the mcp-awareness HTTP endpoint.
    The transport layer (SSE, streamable-http) will be wired when
    the first real provider integration lands.
    """

    def __init__(self, url: str, source: str) -> None:
        self.url = url.rstrip("/")
        self.source = source
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.url, timeout=30.0)
        return self._client

    async def report_status(
        self,
        source: str,
        tags: list[str],
        metrics: dict[str, Any],
        inventory: dict[str, Any] | None = None,
        ttl_sec: int = 120,
    ) -> None:
        """Report current metrics to mcp-awareness."""
        # TODO: Wire to real MCP tool call transport (SSE/streamable-http)
        logger.info(
            "report_status: source=%s tags=%s metrics_keys=%s ttl=%d",
            source,
            tags,
            list(metrics.keys()),
            ttl_sec,
        )
        logger.debug("report_status payload: %s", metrics)

    async def report_alert(
        self,
        source: str,
        tags: list[str],
        alert_id: str,
        level: str,
        alert_type: str,
        message: str,
        details: dict[str, Any] | None = None,
        diagnostics: dict[str, Any] | None = None,
        *,
        resolved: bool = False,
    ) -> None:
        """Report an alert (or resolution) to mcp-awareness."""
        # TODO: Wire to real MCP tool call transport (SSE/streamable-http)
        logger.info(
            "report_alert: source=%s alert_id=%s level=%s resolved=%s message=%s",
            source,
            alert_id,
            level,
            resolved,
            message,
        )

    async def get_knowledge(
        self,
        tags: list[str] | None = None,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read knowledge entries from mcp-awareness."""
        # TODO: Wire to real MCP tool call transport (SSE/streamable-http)
        logger.info("get_knowledge: tags=%s source=%s", tags, source)
        return []

    async def get_status(
        self,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read status entries from mcp-awareness."""
        # TODO: Wire to real MCP tool call transport (SSE/streamable-http)
        logger.info("get_status: source=%s", source)
        return []

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
