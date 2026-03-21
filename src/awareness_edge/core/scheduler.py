"""Async polling loop — collect from providers, evaluate, report."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from awareness_edge.core.client import AwarenessClient
from awareness_edge.evaluator import get_evaluator
from awareness_edge.providers import get_provider
from awareness_edge.sinks import get_sink

if TYPE_CHECKING:
    from awareness_edge.core.config import EdgeConfig
    from awareness_edge.evaluator.base import BaseEvaluator
    from awareness_edge.providers.base import BaseProvider
    from awareness_edge.sinks.base import BaseSink

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


def _build_sinks(config: EdgeConfig) -> list[BaseSink]:
    """Instantiate all enabled sinks from config."""
    sinks: list[BaseSink] = []
    for entry in config.sinks:
        if not entry.enabled:
            logger.debug("Sink %s is disabled, skipping", entry.name)
            continue
        try:
            sink = get_sink(entry.type, entry.config)
            sinks.append(sink)
            logger.info("Loaded sink: %s (type=%s)", entry.name, entry.type)
        except KeyError:
            logger.error("Unknown sink type %r for %s — skipping", entry.type, entry.name)
    return sinks


def _build_evaluator(config: EdgeConfig) -> BaseEvaluator:
    """Instantiate the configured evaluator."""
    return get_evaluator(config.evaluator.type)


async def run_loop(config: EdgeConfig, *, once: bool = False, dry_run: bool = False) -> None:
    """Main polling loop.

    For each enabled provider: collect metrics, report status,
    evaluate for alerts. Errors in one provider don't stop others.
    """
    providers = _build_providers(config)
    sinks = _build_sinks(config)

    if not providers and not sinks:
        logger.warning("No providers or sinks configured — nothing to do")
        return

    if dry_run:
        for sink in sinks:
            sink.dry_run = True
        logger.info("Dry-run mode — no writes to external systems")

    evaluator = _build_evaluator(config)
    client = AwarenessClient(
        url=config.awareness.url,
        source=config.awareness.source,
    )

    logger.info(
        "Starting edge loop: %d provider(s), %d sink(s), evaluator=%s, interval=%ds",
        len(providers),
        len(sinks),
        config.evaluator.type,
        config.poll_interval_sec,
    )

    try:
        while True:
            await _run_cycle(providers, sinks, evaluator, client)
            if once:
                break
            await asyncio.sleep(config.poll_interval_sec)
    finally:
        await client.close()


async def _run_cycle(
    providers: list[BaseProvider],
    sinks: list[BaseSink],
    evaluator: BaseEvaluator,
    client: AwarenessClient,
) -> None:
    """Execute one collection+evaluation+sink cycle."""
    # Phase 1: Inbound — collect from providers, evaluate, report
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

    # Phase 2: Outbound — push from awareness to external systems
    for sink in sinks:
        try:
            sink_result = await sink.push(client)
            logger.info(
                "Sink %s pushed %d item(s)", sink_result.sink_name, sink_result.items_pushed
            )
        except Exception:
            logger.exception("Error in sink %s", sink.sink_name)
