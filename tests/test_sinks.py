"""Tests for the sink framework."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from awareness_edge.sinks import get_sink
from awareness_edge.sinks.base import SinkResult
from awareness_edge.sinks.demo import DemoSink


@pytest.mark.asyncio
async def test_demo_sink_push() -> None:
    sink = DemoSink()
    client = AsyncMock()
    result = await sink.push(client)

    assert isinstance(result, SinkResult)
    assert result.sink_name == "demo"
    assert result.items_pushed == 0


def test_demo_sink_name() -> None:
    sink = DemoSink()
    assert sink.sink_name == "demo"


def test_sink_registry_demo() -> None:
    sink = get_sink("demo")
    assert isinstance(sink, DemoSink)


def test_sink_registry_unknown() -> None:
    with pytest.raises(KeyError, match="Unknown sink"):
        get_sink("nonexistent")
