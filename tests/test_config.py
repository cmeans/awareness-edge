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
