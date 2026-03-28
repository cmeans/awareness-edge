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

"""Tests for configuration loading and validation."""

from __future__ import annotations

import pytest

from awareness_edge.core.config import EdgeConfig, ProviderEntry, SinkEntry


def test_default_config() -> None:
    config = EdgeConfig()
    assert config.awareness.url == "http://localhost:8420"
    assert config.awareness.source == "awareness-edge"
    assert config.evaluator.type == "threshold"
    assert config.poll_interval_sec == 60
    assert config.providers == []


def test_config_with_provider() -> None:
    config = EdgeConfig(
        providers=[ProviderEntry(name="test", type="demo")],
    )
    assert len(config.providers) == 1
    assert config.providers[0].name == "test"
    assert config.providers[0].enabled is True


def test_config_validation_bad_evaluator() -> None:
    with pytest.raises(ValueError):
        EdgeConfig.model_validate({"evaluator": {"type": "nonexistent"}})


def test_config_evaluator_default() -> None:
    config = EdgeConfig()
    assert config.evaluator.type == "threshold"


def test_config_with_sink() -> None:
    config = EdgeConfig(
        sinks=[SinkEntry(name="test-sink", type="demo")],
    )
    assert len(config.sinks) == 1
    assert config.sinks[0].name == "test-sink"
    assert config.sinks[0].enabled is True


def test_config_default_no_sinks() -> None:
    config = EdgeConfig()
    assert config.sinks == []
