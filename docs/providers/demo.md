# Demo Provider

Returns static fake metrics. Useful for testing the collection pipeline without connecting to any real system.

## Setup

No setup required — the demo provider is built in and has no dependencies.

## Configuration

```yaml
providers:
  - name: demo
    type: demo
    enabled: true
```

No `config` block needed — there are no options.

## Metrics returned

| Metric | Value | Type |
|--------|-------|------|
| `cpu_percent` | 42.0 | float |
| `memory_percent` | 65.3 | float |
| `uptime_hours` | 1234 | int |

These are static values that never change. The demo provider is meant to verify that the scheduler, evaluator, and awareness client are wired correctly.

## When to use

- Testing a new config before connecting real sources
- CI/CD pipeline validation
- Verifying the threshold evaluator triggers at expected levels (customize thresholds, not the demo)
