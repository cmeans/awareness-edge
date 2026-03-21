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
