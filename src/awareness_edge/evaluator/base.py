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

"""Base evaluator interface for metric classification."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from awareness_edge.evaluator import EvaluationResult


class BaseEvaluator(ABC):
    """Abstract base class for metric evaluators.

    Evaluators examine collected metrics and decide whether
    anything warrants an alert. Return None for "nothing to report".
    """

    @abstractmethod
    async def evaluate(self, source: str, metrics: dict[str, Any]) -> EvaluationResult | None:
        """Evaluate metrics and optionally return an alert."""
