# awareness-edge

> Collect. Evaluate. Report. The bridge between your systems and your AI assistant's awareness.

> [!NOTE]
> This project is under active development. It is the companion service to [mcp-awareness](https://github.com/cmeans/mcp-awareness).

## What it does

`awareness-edge` is a polling service that collects system metrics from source MCP servers (Synology NAS, Garmin, Home Assistant, etc.), evaluates them against configurable thresholds, and writes status and alerts to the [mcp-awareness](https://github.com/cmeans/mcp-awareness) service.

The result: your AI assistant knows about your systems without you having to ask.

## Architecture

```mermaid
flowchart TD
    subgraph Sources["Source MCP Servers"]
        direction LR
        S1["synology-mcp"]
        S2["Garmin MCP"]
        S3["Home Assistant"]
    end

    Sources --> Collector

    subgraph Edge["awareness-edge"]
        Collector["Collector · Python loop, 60s"]
        Evaluator["Evaluator · thresholds"]
        Collector --> Evaluator
    end

    Collector -- "report_status (always)" --> Store
    Evaluator -. "report_alert (when needed)" .-> Store

    subgraph Awareness["mcp-awareness"]
        Store["Store + Collator"]
    end
```

**Collection layer** (Python): scheduling, MCP connections, data collection, status reporting. Runs every cycle, deterministic, no external dependencies.

**Evaluation layer** (thresholds): "Is anything here worth alerting about?" Configurable metric thresholds with pluggable evaluator interface for future extension.

## First source: Synology NAS

Uses [synology-mcp](https://github.com/cmeans/synology-mcp) tools:
- `get_resource_usage` — CPU, memory, disk I/O, network
- `get_system_info` — model, firmware, temperature, uptime

The NAS is a seedbox — 80-90% disk I/O and high CPU from qBittorrent is normal. The evaluator focuses on structural changes (processes stopped, unexpected quiet) rather than high numbers.

## License

Apache 2.0

---

Copyright (c) 2026 Chris Means
