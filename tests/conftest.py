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
