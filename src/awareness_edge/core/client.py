"""Awareness MCP client — reads from and writes to mcp-awareness."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class AwarenessClient:
    """Client for the mcp-awareness service via streamable HTTP transport.

    Connects to the mcp-awareness MCP server and calls its tools
    for reporting status/alerts and reading knowledge/status entries.
    """

    def __init__(self, url: str, source: str) -> None:
        self.url = url.rstrip("/")
        self.source = source
        self._session: ClientSession | None = None
        self._streams: Any = None
        self._cm: Any = None

    async def _ensure_session(self) -> ClientSession:
        """Lazily connect and initialize the MCP session."""
        if self._session is not None:
            return self._session

        mcp_url = f"{self.url}/mcp"
        logger.info("Connecting to mcp-awareness at %s", mcp_url)

        self._cm = streamablehttp_client(url=mcp_url)
        read_stream, write_stream, _ = await self._cm.__aenter__()

        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()

        logger.info("MCP session established with mcp-awareness")
        return self._session

    def _extract_result(self, result: Any) -> Any:
        """Extract JSON data from a CallToolResult."""
        if result.isError:
            text = result.content[0].text if result.content else "unknown error"
            logger.warning("MCP tool returned error: %s", text)
            return None

        if not result.content:
            return None

        text = result.content[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    async def report_status(
        self,
        source: str,
        tags: list[str],
        metrics: dict[str, Any],
        inventory: dict[str, Any] | None = None,
        ttl_sec: int = 120,
    ) -> None:
        """Report current metrics to mcp-awareness."""
        session = await self._ensure_session()
        args: dict[str, Any] = {
            "source": source,
            "tags": tags,
            "metrics": metrics,
            "ttl_sec": ttl_sec,
        }
        if inventory is not None:
            args["inventory"] = inventory

        result = await session.call_tool("report_status", args)
        data = self._extract_result(result)
        logger.debug("report_status result: %s", data)

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
        session = await self._ensure_session()
        args: dict[str, Any] = {
            "source": source,
            "tags": tags,
            "alert_id": alert_id,
            "level": level,
            "alert_type": alert_type,
            "message": message,
            "resolved": resolved,
        }
        if details is not None:
            args["details"] = details
        if diagnostics is not None:
            args["diagnostics"] = diagnostics

        result = await session.call_tool("report_alert", args)
        data = self._extract_result(result)
        logger.debug("report_alert result: %s", data)

    async def get_knowledge(
        self,
        tags: list[str] | None = None,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read knowledge entries from mcp-awareness."""
        session = await self._ensure_session()
        args: dict[str, Any] = {}
        if tags is not None:
            args["tags"] = tags
        if source is not None:
            args["source"] = source

        try:
            result = await session.call_tool("get_knowledge", args)
            data = self._extract_result(result)
            if isinstance(data, dict) and "result" in data:
                raw = data["result"]
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                return parsed if isinstance(parsed, list) else []
            if isinstance(data, list):
                return data
        except Exception:
            logger.exception("Failed to get knowledge from awareness")

        return []

    async def get_status(
        self,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read status entries from mcp-awareness."""
        session = await self._ensure_session()
        args: dict[str, Any] = {}
        if source is not None:
            args["source"] = source

        try:
            result = await session.call_tool("get_status", args)
            data = self._extract_result(result)
            if isinstance(data, dict) and "result" in data:
                raw = data["result"]
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                return parsed if isinstance(parsed, list) else []
            if isinstance(data, list):
                return data
        except Exception:
            logger.exception("Failed to get status from awareness")

        return []

    async def close(self) -> None:
        """Close the MCP session and transport."""
        if self._session is not None:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:
                logger.debug("Error closing MCP session", exc_info=True)
            self._session = None

        if self._cm is not None:
            try:
                await self._cm.__aexit__(None, None, None)
            except Exception:
                logger.debug("Error closing MCP transport", exc_info=True)
            self._cm = None
