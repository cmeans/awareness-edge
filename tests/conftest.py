"""Shared test fixtures."""

from __future__ import annotations

import pytest

from awareness_edge.core.config import EdgeConfig, ProviderEntry


@pytest.fixture
def edge_config() -> EdgeConfig:
    """Minimal config with the demo provider enabled."""
    return EdgeConfig(
        providers=[
            ProviderEntry(name="demo", type="demo"),
        ],
    )
