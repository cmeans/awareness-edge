# GitHub Sink

Syncs awareness entries to a file in a GitHub repository. Reads entries by tag from mcp-awareness, formats them as markdown, and commits to the configured repo. Skips commits when the content hasn't changed.

## Setup

### 1. Create a GitHub personal access token

Go to [Settings → Developer settings → Fine-grained tokens](https://github.com/settings/tokens?type=beta) and create a new token:

- **Token name**: `awareness-edge-sync` (or similar)
- **Repository access**: select only the target repo (e.g., `cmeans/mcp-awareness`)
- **Permissions**:
  - **Contents**: Read and write (required to read/update files)

Copy the token — you'll only see it once.

### 2. Set the environment variable

```bash
export GITHUB_TOKEN="github_pat_..."
```

For persistent use, add it to your shell profile, a `.env` file, or a systemd service environment.

By default the sink reads from `GITHUB_TOKEN`. To use a different variable name, set `token_env` in the config (see below).

### 3. Configure the sink

Add to your `~/.config/awareness-edge/config.yaml`:

```yaml
sinks:
  - name: prompt-sync
    type: github
    enabled: true
    config:
      repo: "cmeans/mcp-awareness"        # owner/repo
      path: "docs/memory-prompts.md"       # file path in the repo
      branch: "main"                       # target branch (default: main)
      tags: ["memory-prompt"]              # awareness tags to filter (default: memory-prompt)
      token_env: "GITHUB_TOKEN"            # env var for the token (default: GITHUB_TOKEN)
```

### 4. Test with dry-run

```bash
awareness-edge run --once --dry-run --config config.yaml
```

This prints the formatted markdown to stderr without committing to GitHub. Verify the output looks right before running for real.

### 5. Run for real

```bash
# Single shot
awareness-edge run --once --config config.yaml

# Long-lived (syncs every poll_interval_sec)
awareness-edge run --config config.yaml
```

## Config reference

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `repo` | yes | — | GitHub repository in `owner/repo` format |
| `path` | yes | — | File path within the repo to create/update |
| `branch` | no | `main` | Target branch for commits |
| `tags` | no | `["memory-prompt"]` | Awareness tags to filter entries by |
| `token_env` | no | `GITHUB_TOKEN` | Name of the environment variable holding the token |

## Behavior

- **First run**: creates the file if it doesn't exist
- **Subsequent runs**: updates the file only if content changed (compares with current GitHub content)
- **No entries found**: skips update (doesn't write an empty file)
- **No token set**: logs a warning and skips (doesn't error)
- **Commit message**: `Sync memory prompts from mcp-awareness`

## Output format

The generated markdown file looks like:

```markdown
# Memory Prompts

> Auto-synced from mcp-awareness by awareness-edge.
> Last updated: 2026-03-21T16:50:28Z

---

## Entry description here

Source: `source-name` | Tags: `tag1`, `tag2` | Updated: 2026-03-21T14:00:00Z

Entry content goes here.

---
```

## Troubleshooting

**"GitHub sink: no token configured, skipping"**
- Set the `GITHUB_TOKEN` environment variable, or configure `token_env` to point to the correct variable name.

**"GitHub sink: failed to update file"**
- Check that the token has `contents: write` permission on the target repo.
- Verify the `repo` and `branch` values are correct.
- If the file is in a protected branch, ensure the token has permission to push.

**"GitHub sink: content unchanged, skipping commit"**
- Normal behavior — means the awareness entries haven't changed since the last sync.
