# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

**awareness-edge** — a bidirectional polling service that bridges source MCP servers and the [mcp-awareness](https://github.com/cmeans/mcp-awareness) knowledge store.

- **Inbound** (providers): collect metrics from source MCPs (Synology, Garmin, Home Assistant), evaluate against thresholds, report status/alerts to awareness
- **Outbound** (sinks): read from awareness, push to external systems (GitHub, Slack, Notion)

## Architecture

Deterministic Python loop — no LLM dependency.

```
every 60 seconds:
  Phase 1 — Inbound (providers):
    1. Call source MCP tools (get_resource_usage, get_system_info, etc.)
    2. report_status to mcp-awareness with raw metrics
    3. Evaluate metrics against thresholds
    4. If threshold exceeded → report_alert

  Phase 2 — Outbound (sinks):
    5. Read from mcp-awareness (get_knowledge, get_status)
    6. Push to external targets (GitHub, Slack, etc.)
```

Per-provider and per-sink error isolation — one failure doesn't stop others.

## Project Structure

```
src/awareness_edge/
├── __init__.py          # version from importlib.metadata
├── __main__.py          # python -m entry point
├── cli.py               # Click CLI: run, check-config
├── core/
│   ├── config.py        # Pydantic models, YAML + env var loader
│   ├── client.py        # Awareness MCP client (report + read, StreamableHTTP transport)
│   └── scheduler.py     # Async polling loop
├── evaluator/
│   ├── base.py          # BaseEvaluator ABC
│   └── threshold.py     # ThresholdEvaluator (default)
├── providers/
│   ├── base.py          # BaseProvider ABC + CollectionResult
│   ├── demo.py          # Static fake metrics for testing
│   └── __init__.py      # Provider registry
└── sinks/
    ├── base.py          # BaseSink ABC + SinkResult
    ├── demo.py          # Logging no-op for testing
    ├── github.py        # GitHub prompt sync sink
    └── __init__.py      # Sink registry

examples/
└── audit_store.py       # Data hygiene audit with GitHub issue reporting
```

## Build & Test

```bash
uv sync --extra dev          # install deps
uv run ruff check src/ tests/    # lint
uv run ruff format --check src/ tests/  # format check
uv run mypy src/             # type check (strict)
uv run pytest -v             # run tests
uv run awareness-edge --version  # verify CLI
```

## Related Repos

- [cmeans/mcp-awareness](https://github.com/cmeans/mcp-awareness) — the awareness service (store, collator, briefing)
- [cmeans/synology-mcp](https://github.com/cmeans/synology-mcp) — Synology NAS MCP server (first data source)

## Key Constraints

- Deterministic Python loop — no LLM dependencies
- Threshold evaluator for alerting (evaluator interface is pluggable for future extension)
- Evaluator failures default to no-alert, log the failure
- Per-provider and per-sink error isolation
- Awareness client uses MCP SDK StreamableHTTPTransport — URL must include mount path if server uses `AWARENESS_MOUNT_PATH`
- First planned sources: Synology NAS (get_resource_usage, get_system_info), Garmin health data
