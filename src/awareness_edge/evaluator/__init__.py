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

"""Evaluation layer: classify metrics and decide whether to alert."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from awareness_edge.evaluator.base import BaseEvaluator


@dataclass
class EvaluationResult:
    """Result of metric evaluation — represents a potential alert."""

    alert_id: str
    level: Literal["info", "warning", "critical"]
    alert_type: str
    message: str
    details: dict[str, Any] | None = None


def get_evaluator(evaluator_type: str, **kwargs: Any) -> BaseEvaluator:
    """Instantiate an evaluator by type name."""
    if evaluator_type == "threshold":
        from awareness_edge.evaluator.threshold import ThresholdEvaluator

        return ThresholdEvaluator(**kwargs)

    msg = f"Unknown evaluator type: {evaluator_type!r}"
    raise ValueError(msg)
