"""Tests for the GitHub prompt sync sink."""

from __future__ import annotations

import pytest

from awareness_edge.sinks.github import GitHubSink


@pytest.fixture
def sample_entries() -> list[dict[str, object]]:
    return [
        {
            "id": "abc-123",
            "type": "note",
            "source": "personal",
            "tags": ["memory-prompt"],
            "created": "2026-03-21T12:00:00Z",
            "updated": "2026-03-21T14:00:00Z",
            "data": {
                "description": "Test prompt entry",
                "content": "This is the prompt content.",
            },
        },
        {
            "id": "def-456",
            "type": "note",
            "source": "mcp-awareness-project",
            "tags": ["memory-prompt", "project"],
            "created": "2026-03-20T10:00:00Z",
            "updated": "2026-03-21T10:00:00Z",
            "data": {
                "description": "Another prompt",
            },
        },
    ]


def test_github_sink_name() -> None:
    sink = GitHubSink({"repo": "test/repo", "path": "docs/test.md"})
    assert sink.sink_name == "github"


def test_github_sink_config() -> None:
    sink = GitHubSink(
        {
            "repo": "cmeans/mcp-awareness",
            "path": "docs/memory-prompts.md",
            "branch": "dev",
            "tags": ["custom-tag"],
        }
    )
    assert sink.repo == "cmeans/mcp-awareness"
    assert sink.path == "docs/memory-prompts.md"
    assert sink.branch == "dev"
    assert sink.tags == ["custom-tag"]


def test_github_sink_defaults() -> None:
    sink = GitHubSink({"repo": "test/repo", "path": "test.md"})
    assert sink.branch == "main"
    assert sink.tags == ["memory-prompt"]


def test_format_entries(sample_entries: list[dict[str, object]]) -> None:
    sink = GitHubSink({"repo": "test/repo", "path": "test.md"})
    content = sink._format_entries(sample_entries)

    assert "# Memory Prompts" in content
    assert "## Test prompt entry" in content
    assert "This is the prompt content." in content
    assert "## Another prompt" in content
    assert "_(no content)_" in content
    assert "Source: `personal`" in content
    assert "Source: `mcp-awareness-project`" in content


def test_format_entries_empty() -> None:
    sink = GitHubSink({"repo": "test/repo", "path": "test.md"})
    content = sink._format_entries([])

    assert "# Memory Prompts" in content
    assert "---\n" in content


@pytest.mark.asyncio
async def test_push_no_token() -> None:
    sink = GitHubSink({"repo": "test/repo", "path": "test.md"})
    sink._token = None

    from unittest.mock import AsyncMock

    client = AsyncMock()
    result = await sink.push(client)

    assert result.items_pushed == 0
    client.get_knowledge.assert_not_called()


def test_sink_registry_github() -> None:
    from awareness_edge.sinks import get_sink

    sink = get_sink("github", {"repo": "test/repo", "path": "test.md"})
    assert isinstance(sink, GitHubSink)
