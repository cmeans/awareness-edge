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

"""GitHub sink — syncs awareness entries to a file in a GitHub repo."""

from __future__ import annotations

import base64
import logging
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import click
import httpx

from awareness_edge.sinks.base import BaseSink, SinkResult

if TYPE_CHECKING:
    from awareness_edge.core.client import AwarenessClient

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubSink(BaseSink):
    """Reads awareness entries by tag and syncs them to a GitHub file.

    On each push cycle:
    1. Queries awareness for entries matching configured tags
    2. Formats them as markdown
    3. Compares with the current file in GitHub
    4. Commits an update only if content changed
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.repo: str = config["repo"]
        self.path: str = config["path"]
        self.branch: str = config.get("branch", "main")
        self.tags: list[str] = config.get("tags", ["memory-prompt"])
        token_env: str = config.get("token_env", "GITHUB_TOKEN")
        self._token: str | None = os.environ.get(token_env)

    @property
    def sink_name(self) -> str:
        return "github"

    async def push(self, client: AwarenessClient) -> SinkResult:
        if not self._token:
            logger.warning("GitHub sink: no token configured, skipping")
            return SinkResult(sink_name="github", items_pushed=0)

        entries = await client.get_knowledge(tags=self.tags)
        if not entries:
            logger.debug("GitHub sink: no entries found for tags %s", self.tags)
            return SinkResult(sink_name="github", items_pushed=0)

        new_content = self._format_entries(entries)
        current_sha, current_content = await self._get_current_file()

        if current_content == new_content:
            logger.debug("GitHub sink: content unchanged, skipping commit")
            return SinkResult(sink_name="github", items_pushed=0)

        if self.dry_run:
            click.echo(f"--- dry-run: {self.repo}/{self.path} ---", err=True)
            click.echo(new_content, err=True)
            click.echo("--- end dry-run ---", err=True)
            return SinkResult(
                sink_name="github",
                items_pushed=len(entries),
                details={"repo": self.repo, "path": self.path, "dry_run": True},
            )

        await self._update_file(new_content, current_sha)
        return SinkResult(
            sink_name="github",
            items_pushed=len(entries),
            details={"repo": self.repo, "path": self.path},
        )

    def _format_entries(self, entries: list[dict[str, Any]]) -> str:
        """Format awareness entries as a markdown document."""
        now = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        lines = [
            "# Memory Prompts",
            "",
            "> Auto-synced from [mcp-awareness]"
            "(https://github.com/cmeans/mcp-awareness) by awareness-edge.",
            f"> Last updated: {now}",
            "",
        ]

        for entry in entries:
            data = entry.get("data", {})
            description = data.get("description", "(no description)")
            content = data.get("content", "")
            source = entry.get("source", "unknown")
            tags = ", ".join(f"`{t}`" for t in entry.get("tags", []))
            updated = entry.get("updated", "unknown")

            lines.append("---")
            lines.append("")
            lines.append(f"## {description}")
            lines.append("")
            lines.append(f"Source: `{source}` | Tags: {tags} | Updated: {updated}")
            lines.append("")
            if content:
                lines.append(content)
            else:
                lines.append("_(no content)_")
            lines.append("")

        lines.append("---")
        lines.append("")
        return "\n".join(lines)

    async def _get_current_file(self) -> tuple[str | None, str | None]:
        """Fetch current file SHA and content from GitHub."""
        url = f"{GITHUB_API}/repos/{self.repo}/contents/{self.path}"
        headers = self._headers()
        params = {"ref": self.branch}

        try:
            async with httpx.AsyncClient() as http:
                resp = await http.get(url, headers=headers, params=params)

            if resp.status_code == 404:
                return None, None

            resp.raise_for_status()
            body = resp.json()
            sha = body["sha"]
            content = base64.b64decode(body["content"]).decode("utf-8")
            return sha, content

        except httpx.HTTPError as exc:
            logger.warning("GitHub sink: failed to fetch current file: %s", exc)
            return None, None

    async def _update_file(self, content: str, current_sha: str | None) -> None:
        """Create or update the file in GitHub."""
        url = f"{GITHUB_API}/repos/{self.repo}/contents/{self.path}"
        headers = self._headers()

        payload: dict[str, Any] = {
            "message": "Sync memory prompts from mcp-awareness",
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": self.branch,
        }
        if current_sha is not None:
            payload["sha"] = current_sha

        try:
            async with httpx.AsyncClient() as http:
                resp = await http.put(url, headers=headers, json=payload)
            resp.raise_for_status()
            logger.info(
                "GitHub sink: updated %s/%s (%d bytes)",
                self.repo,
                self.path,
                len(content),
            )
        except httpx.HTTPError as exc:
            logger.warning("GitHub sink: failed to update file: %s", exc)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
