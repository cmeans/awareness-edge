"""Tests for the awareness MCP client."""

from __future__ import annotations

from awareness_edge.core.client import AwarenessClient


def test_client_init() -> None:
    client = AwarenessClient(url="http://localhost:8420", source="test")
    assert client.url == "http://localhost:8420"
    assert client.source == "test"
    assert client._session is None


def test_client_url_trailing_slash() -> None:
    client = AwarenessClient(url="http://localhost:8420/", source="test")
    assert client.url == "http://localhost:8420"
