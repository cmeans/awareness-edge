# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

**awareness-edge** — an MCP-to-MCP bridge agent that collects system data from source MCP servers (synology-mcp, Garmin, Home Assistant, etc.), evaluates it using a local LLM (Ollama), and writes status/alerts to the mcp-awareness service.

Companion to [cmeans/mcp-awareness](https://github.com/cmeans/mcp-awareness) (the generic awareness store + collation server).

## Architecture

Hybrid: deterministic Python loop for reliability, local LLM (Ollama) for evaluation.

```
every 60 seconds (Python, no LLM):
  1. Authenticate to source MCPs
  2. Call source tools (get_resource_usage, get_system_info, etc.)
  3. Call mcp-awareness:report_status with raw metrics

when evaluating (LLM via Ollama):
  4. Pass metrics + context to local model
  5. "Is this worth alerting about?" → classification task
  6. If yes → mcp-awareness:report_alert
```

The LLM evaluation step is isolated — testable independently with saved snapshots, swappable models, fallback to threshold logic if model is unreliable.

## Related Repos

- [cmeans/mcp-awareness](https://github.com/cmeans/mcp-awareness) — the awareness service (store, collator, briefing)
- [cmeans/synology-mcp](https://github.com/cmeans/synology-mcp) — Synology NAS MCP server (first data source)

## Key Constraints

- Python script handles auth, scheduling, MCP connections — never depends on LLM for plumbing
- LLM handles evaluation only (classification, not orchestration)
- Model failures should default to no-alert, log the failure
- First source: synology-mcp (get_resource_usage, get_system_info)
- LLM: Ollama, starting with llama3.1:8b — will iterate on model selection
- Token efficiency: minimize what gets sent to the LLM evaluator
- Data privacy: system metrics transit to local Ollama only, never to cloud LLM providers
