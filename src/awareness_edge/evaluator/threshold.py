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

"""Threshold-based evaluator — no LLM dependency, always available."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from awareness_edge.evaluator import EvaluationResult
from awareness_edge.evaluator.base import BaseEvaluator

logger = logging.getLogger(__name__)


@dataclass
class Threshold:
    """A single metric threshold definition."""

    metric: str
    warning: float
    critical: float


DEFAULT_THRESHOLDS: list[Threshold] = [
    Threshold(metric="cpu_percent", warning=90.0, critical=98.0),
    Threshold(metric="memory_percent", warning=85.0, critical=95.0),
    Threshold(metric="disk_percent", warning=85.0, critical=95.0),
]


class ThresholdEvaluator(BaseEvaluator):
    """Evaluates metrics against configurable thresholds.

    Returns the highest-severity alert found, or None.
    """

    def __init__(self, thresholds: list[Threshold] | None = None, **_kwargs: Any) -> None:
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    async def evaluate(self, source: str, metrics: dict[str, Any]) -> EvaluationResult | None:
        worst: EvaluationResult | None = None
        worst_value = 0.0

        for threshold in self.thresholds:
            value = metrics.get(threshold.metric)
            if value is None or not isinstance(value, (int, float)):
                continue

            if value >= threshold.critical:
                level: Literal["warning", "critical"] = "critical"
            elif value >= threshold.warning:
                level = "warning"
            else:
                continue

            if value > worst_value:
                worst_value = value
                worst = EvaluationResult(
                    alert_id=f"{source}:{threshold.metric}",
                    level=level,
                    alert_type="threshold",
                    message=f"{threshold.metric} is {value:.1f}% on {source} ({level})",
                    details={
                        "metric": threshold.metric,
                        "value": value,
                        "threshold": (
                            threshold.critical if level == "critical" else threshold.warning
                        ),
                    },
                )

        return worst
