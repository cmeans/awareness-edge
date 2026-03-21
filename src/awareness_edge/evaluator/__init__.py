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
