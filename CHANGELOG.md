# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Outbound sink framework — `BaseSink` ABC, separate registry, `sinks:` config section
- Demo sink for testing the outbound pipeline
- **GitHub prompt sync sink** — reads awareness entries by tag, formats as markdown, commits to a configurable GitHub repo. Skips commits when content is unchanged.
- **Real MCP client transport** — `AwarenessClient` now connects to mcp-awareness via streamable HTTP (MCP SDK). Replaces logging stubs with actual tool calls.
- Awareness client read methods (`get_knowledge`, `get_status`) for sinks to query awareness
- `--dry-run` flag on `run` command — sinks output what they would write to stderr without touching external systems
- `check-config` now displays configured sinks
- **Data hygiene audit script** (`examples/audit_store.py`) — audits awareness store for tag drift, mistyped patterns, source naming issues, low-quality entries, singleton tags. Stores full report in awareness (tagged `hygiene-audit`, `data-quality`, `actionable`) for later retrieval. Fingerprinted to skip redundant updates. `--dry-run` prints to stdout without storing.
- Awareness client: `get_stats()`, `get_tags()`, `add_context()` methods; `get_knowledge()` gains `entry_type` filter

### Changed

- Default awareness URL updated to `http://localhost:8420` (matches mcp-awareness default port)
- Added `mcp[cli]>=1.0.0` as a dependency

### Fixed

- Audit tag drift: replaced edit-distance matching with prefix matching to eliminate false positives (`docker`↔`soccer`, `admin`↔`garmin`, etc.)
- Audit singleton tags: collapsed 173 individual findings into a single summary line

## [0.1.0] - 2026-03-21

### Added

- Project scaffolding with hatchling build, src/ layout, Apache 2.0 license
- CLI entry point (`awareness-edge`) with `run` and `check-config` subcommands
- Pluggable provider framework with registry and `BaseProvider` ABC
- Demo provider returning static fake metrics for testing
- Pluggable evaluator framework with `BaseEvaluator` ABC
- Threshold evaluator — configurable metric thresholds, deterministic, no external dependencies
- Pydantic config with YAML file support and environment variable overrides
- Awareness MCP client stub (`report_status`, `report_alert`)
- Async scheduler with per-provider error isolation and `--once` mode
- CI pipeline: ruff (lint + format), mypy (strict), pytest (3.11/3.12/3.13 matrix)
- Publish pipeline: PyPI on tag push, TestPyPI on manual dispatch, GitHub Release

[Unreleased]: https://github.com/cmeans/awareness-edge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cmeans/awareness-edge/releases/tag/v0.1.0
