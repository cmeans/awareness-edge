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

    def _parse_list_result(self, data: Any) -> list[dict[str, Any]]:
        """Parse a tool result that returns a JSON list."""
        if isinstance(data, dict) and "result" in data:
            raw = data["result"]
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            return parsed if isinstance(parsed, list) else []
        if isinstance(data, list):
            return data
        return []

    async def _call_list_tool(self, tool: str, args: dict[str, Any]) -> list[dict[str, Any]]:
        """Call a tool and parse the result as a list."""
        session = await self._ensure_session()
        try:
            result = await session.call_tool(tool, args)
            data = self._extract_result(result)
            return self._parse_list_result(data)
        except Exception:
            logger.exception("Failed to call %s", tool)
            return []

    async def get_knowledge(
        self,
        tags: list[str] | None = None,
        source: str | None = None,
        entry_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read knowledge entries from mcp-awareness."""
        args: dict[str, Any] = {}
        if tags is not None:
            args["tags"] = tags
        if source is not None:
            args["source"] = source
        if entry_type is not None:
            args["entry_type"] = entry_type
        return await self._call_list_tool("get_knowledge", args)

    async def get_status(
        self,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read status entries from mcp-awareness."""
        args: dict[str, Any] = {}
        if source is not None:
            args["source"] = source
        return await self._call_list_tool("get_status", args)

    async def get_stats(self) -> dict[str, Any]:
        """Get store statistics from mcp-awareness."""
        session = await self._ensure_session()
        try:
            result = await session.call_tool("get_stats", {})
            data = self._extract_result(result)
            if isinstance(data, dict):
                if "result" in data:
                    raw = data["result"]
                    return json.loads(raw) if isinstance(raw, str) else raw  # type: ignore[no-any-return]
                return data
        except Exception:
            logger.exception("Failed to get stats")
        return {}

    async def get_tags(self) -> list[dict[str, Any]]:
        """Get all tags with usage counts from mcp-awareness."""
        return await self._call_list_tool("get_tags", {})

    async def add_context(
        self,
        source: str,
        tags: list[str],
        description: str,
        expires_days: int = 30,
    ) -> dict[str, Any]:
        """Add a time-limited context entry to mcp-awareness."""
        session = await self._ensure_session()
        try:
            result = await session.call_tool(
                "add_context",
                {
                    "source": source,
                    "tags": tags,
                    "description": description,
                    "expires_days": expires_days,
                },
            )
            data = self._extract_result(result)
            return data if isinstance(data, dict) else {}
        except Exception:
            logger.exception("Failed to add context")
            return {}

    async def remember(
        self,
        source: str,
        tags: list[str],
        description: str,
        content: str | None = None,
        learned_from: str = "awareness-edge",
    ) -> dict[str, Any]:
        """Store a general-purpose note in mcp-awareness."""
        session = await self._ensure_session()
        args: dict[str, Any] = {
            "source": source,
            "tags": tags,
            "description": description,
            "learned_from": learned_from,
        }
        if content is not None:
            args["content"] = content
        try:
            result = await session.call_tool("remember", args)
            data = self._extract_result(result)
            return data if isinstance(data, dict) else {}
        except Exception:
            logger.exception("Failed to store note")
            return {}

    async def update_entry(
        self,
        entry_id: str,
        description: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing entry in mcp-awareness."""
        session = await self._ensure_session()
        args: dict[str, Any] = {"entry_id": entry_id}
        if description is not None:
            args["description"] = description
        if content is not None:
            args["content"] = content
        try:
            result = await session.call_tool("update_entry", args)
            data = self._extract_result(result)
            return data if isinstance(data, dict) else {}
        except Exception:
            logger.exception("Failed to update entry")
            return {}

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
