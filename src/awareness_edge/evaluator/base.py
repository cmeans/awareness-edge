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
