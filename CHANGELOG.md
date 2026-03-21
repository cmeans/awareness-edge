# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
