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

"""Demo provider returning static fake metrics for testing."""

from __future__ import annotations

from typing import Any

from awareness_edge.providers.base import BaseProvider, CollectionResult


class DemoProvider(BaseProvider):
    """Returns static fake metrics — useful for testing the pipeline."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config or {})

    @property
    def source_name(self) -> str:
        return "demo"

    async def collect(self) -> CollectionResult:
        return CollectionResult(
            source="demo",
            tags=["demo"],
            metrics={
                "cpu_percent": 42.0,
                "memory_percent": 65.3,
                "uptime_hours": 1234,
            },
        )
