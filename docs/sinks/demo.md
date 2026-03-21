# Demo Sink

Logs what it would push without writing to any external system. Useful for testing the sink pipeline.

## Setup

No setup required — the demo sink is built in and has no dependencies.

## Configuration

```yaml
sinks:
  - name: demo
    type: demo
    enabled: true
```

No `config` block needed — there are no options.

## Behavior

Each cycle, logs `DemoSink: would push data (no-op)` at INFO level and returns `items_pushed: 0`.

## When to use

- Verifying that the scheduler runs the sink phase correctly
- Testing config loading and sink registration
- Template for building new sinks
