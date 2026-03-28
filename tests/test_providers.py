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

"""Tests for the provider framework."""

from __future__ import annotations

import pytest

from awareness_edge.providers import get_provider
from awareness_edge.providers.base import CollectionResult
from awareness_edge.providers.demo import DemoProvider


@pytest.mark.asyncio
async def test_demo_provider_collect() -> None:
    provider = DemoProvider()
    result = await provider.collect()

    assert isinstance(result, CollectionResult)
    assert result.source == "demo"
    assert result.tags == ["demo"]
    assert "cpu_percent" in result.metrics
    assert "memory_percent" in result.metrics
    assert "uptime_hours" in result.metrics


def test_demo_provider_source_name() -> None:
    provider = DemoProvider()
    assert provider.source_name == "demo"


def test_provider_registry_demo() -> None:
    provider = get_provider("demo")
    assert isinstance(provider, DemoProvider)


def test_provider_registry_unknown() -> None:
    with pytest.raises(KeyError, match="Unknown provider"):
        get_provider("nonexistent")
