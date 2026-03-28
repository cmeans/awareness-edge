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

"""Demo sink — logs what it would push, useful for testing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from awareness_edge.sinks.base import BaseSink, SinkResult

if TYPE_CHECKING:
    from awareness_edge.core.client import AwarenessClient

logger = logging.getLogger(__name__)


class DemoSink(BaseSink):
    """Logs a push action without writing to any external system."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config or {})

    @property
    def sink_name(self) -> str:
        return "demo"

    async def push(self, client: AwarenessClient) -> SinkResult:
        logger.info("DemoSink: would push data (no-op)")
        return SinkResult(sink_name="demo", items_pushed=0)
