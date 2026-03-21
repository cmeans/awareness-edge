"""Async polling loop — collect from providers, evaluate, report."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from awareness_edge.core.client import AwarenessClient
from awareness_edge.evaluator import get_evaluator
from awareness_edge.providers import get_provider

if TYPE_CHECKING:
    from awareness_edge.core.config import EdgeConfig
    from awareness_edge.evaluator.base import BaseEvaluator
    from awareness_edge.providers.base import BaseProvider

logger = logging.getLogger(__name__)


def _build_providers(config: EdgeConfig) -> list[BaseProvider]:
    """Instantiate all enabled providers from config."""
    providers: list[BaseProvider] = []
    for entry in config.providers:
        if not entry.enabled:
            logger.debug("Provider %s is disabled, skipping", entry.name)
            continue
        try:
            provider = get_provider(entry.type, entry.config)
            providers.append(provider)
            logger.info("Loaded provider: %s (type=%s)", entry.name, entry.type)
        except KeyError:
            logger.error("Unknown provider type %r for %s — skipping", entry.type, entry.name)
    return providers


def _build_evaluator(config: EdgeConfig) -> BaseEvaluator:
    """Instantiate the configured evaluator."""
    return get_evaluator(config.evaluator.type)


async def run_loop(config: EdgeConfig, *, once: bool = False) -> None:
    """Main polling loop.

    For each enabled provider: collect metrics, report status,
    evaluate for alerts. Errors in one provider don't stop others.
    """
    providers = _build_providers(config)
    if not providers:
        logger.warning("No providers configured — nothing to do")
        return

    evaluator = _build_evaluator(config)
    client = AwarenessClient(
        url=config.awareness.url,
        source=config.awareness.source,
    )

    logger.info(
        "Starting edge loop: %d provider(s), evaluator=%s, interval=%ds",
        len(providers),
        config.evaluator.type,
        config.poll_interval_sec,
    )

    try:
        while True:
            await _run_cycle(providers, evaluator, client)
            if once:
                break
            await asyncio.sleep(config.poll_interval_sec)
    finally:
        await client.close()


async def _run_cycle(
    providers: list[BaseProvider],
    evaluator: BaseEvaluator,
    client: AwarenessClient,
) -> None:
    """Execute one collection+evaluation cycle across all providers."""
    for provider in providers:
        try:
            result = await provider.collect()

            await client.report_status(
                source=result.source,
                tags=result.tags,
                metrics=result.metrics,
                inventory=result.inventory,
            )

            alert = await evaluator.evaluate(result.source, result.metrics)
            if alert:
                await client.report_alert(
                    source=result.source,
                    tags=result.tags,
                    alert_id=alert.alert_id,
                    level=alert.level,
                    alert_type=alert.alert_type,
                    message=alert.message,
                    details=alert.details,
                )

        except Exception:
            logger.exception("Error collecting from provider %s", provider.source_name)
