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

"""Tests for the evaluator framework."""

from __future__ import annotations

import pytest

from awareness_edge.evaluator import EvaluationResult, get_evaluator
from awareness_edge.evaluator.threshold import ThresholdEvaluator


@pytest.mark.asyncio
async def test_threshold_no_alert() -> None:
    evaluator = ThresholdEvaluator()
    result = await evaluator.evaluate("test", {"cpu_percent": 50.0, "memory_percent": 60.0})
    assert result is None


@pytest.mark.asyncio
async def test_threshold_warning() -> None:
    evaluator = ThresholdEvaluator()
    result = await evaluator.evaluate("test", {"cpu_percent": 92.0})

    assert result is not None
    assert isinstance(result, EvaluationResult)
    assert result.level == "warning"
    assert "cpu_percent" in result.message


@pytest.mark.asyncio
async def test_threshold_critical() -> None:
    evaluator = ThresholdEvaluator()
    result = await evaluator.evaluate("test", {"cpu_percent": 99.0})

    assert result is not None
    assert result.level == "critical"


@pytest.mark.asyncio
async def test_threshold_ignores_non_numeric() -> None:
    evaluator = ThresholdEvaluator()
    result = await evaluator.evaluate("test", {"cpu_percent": "high"})
    assert result is None


def test_get_evaluator_threshold() -> None:
    evaluator = get_evaluator("threshold")
    assert isinstance(evaluator, ThresholdEvaluator)


def test_get_evaluator_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown evaluator type"):
        get_evaluator("nonexistent")
