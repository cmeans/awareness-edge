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
