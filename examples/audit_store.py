#!/usr/bin/env python3
"""Audit the mcp-awareness store for data hygiene issues.

Connects to mcp-awareness, runs quality checks, and optionally
creates/updates a GitHub issue with findings. Uses a fingerprint
stored in awareness to skip redundant GitHub updates.

Usage:
    # Dry-run (print report to stdout)
    uv run python examples/audit_store.py --dry-run

    # Create/update GitHub issue
    GITHUB_TOKEN=... uv run python examples/audit_store.py --repo cmeans/mcp-awareness
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime

import click
import httpx

from awareness_edge.core.client import AwarenessClient

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
ISSUE_LABEL = "hygiene-audit"
ISSUE_TITLE = "Awareness store hygiene report"
FINGERPRINT_TAG = "hygiene-audit"
FINGERPRINT_SOURCE = "awareness-edge"


# --- Finding types ---


@dataclass
class Finding:
    """A single hygiene issue."""

    category: str
    message: str
    entry_id: str | None = None


@dataclass
class AuditReport:
    """Complete audit results."""

    stats: dict[str, object] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    tag_count: int = 0
    source_count: int = 0
    entry_count: int = 0

    @property
    def has_findings(self) -> bool:
        return len(self.findings) > 0


# --- Checks ---


def check_tag_drift(tags: list[dict[str, object]]) -> list[Finding]:
    """Flag similar tags that may be duplicates."""
    findings: list[Finding] = []
    tag_names = [t["tag"] for t in tags if isinstance(t.get("tag"), str)]
    counts: dict[str, int] = {
        t["tag"]: t["count"]  # type: ignore[assignment]
        for t in tags
        if isinstance(t.get("tag"), str) and isinstance(t.get("count"), int)
    }

    checked: set[tuple[str, str]] = set()
    for a in tag_names:
        for b in tag_names:
            if a >= b:
                continue
            pair = (a, b)
            if pair in checked:
                continue
            checked.add(pair)

            if _tags_similar(a, b):
                findings.append(
                    Finding(
                        category="Tag Drift",
                        message=(
                            f"`{a}` ({counts.get(a, 0)} uses) "
                            f"↔ `{b}` ({counts.get(b, 0)} uses) "
                            "— consider consolidating"
                        ),
                    )
                )
    return findings


def _tags_similar(a: str, b: str) -> bool:
    """Check if two tags are suspiciously similar."""
    if a == b:
        return False
    # Simple plural check (project/projects, skill/skills)
    if a + "s" == b or b + "s" == a:
        return True
    # One is an exact suffix of the other with a hyphen separator
    # (e.g., sleep/deep-sleep, cycling/indoor-cycling)
    # These are intentional sub-tags — skip them
    if a.endswith(f"-{b}") or b.endswith(f"-{a}"):
        return False
    # One is a substring AND shares at least 5 chars AND the longer
    # tag starts with the shorter (prefix match, not arbitrary substring)
    if len(a) >= 5 and len(b) >= 5:
        shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
        if longer.startswith(shorter):
            return True
    return False


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance."""
    if len(a) < len(b):
        return _edit_distance(b, a)
    if len(b) == 0:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[len(b)]


def check_mistyped_patterns(entries: list[dict[str, object]]) -> list[Finding]:
    """Flag patterns missing conditions or effect fields."""
    findings: list[Finding] = []
    for entry in entries:
        data = entry.get("data", {})
        if not isinstance(data, dict):
            continue
        has_conditions = bool(data.get("conditions"))
        has_effect = bool(data.get("effect"))
        if not has_conditions or not has_effect:
            missing = []
            if not has_conditions:
                missing.append("conditions")
            if not has_effect:
                missing.append("effect")
            desc = data.get("description", "(no description)")
            findings.append(
                Finding(
                    category="Mistyped Patterns",
                    message=(
                        f'`{entry.get("id", "?")}`: "{desc}" '
                        f"— missing {', '.join(missing)}, should probably be a note"
                    ),
                    entry_id=str(entry.get("id", "")),
                )
            )
    return findings


def check_source_naming(stats: dict[str, object]) -> list[Finding]:
    """Flag sources with potential naming inconsistencies."""
    findings: list[Finding] = []
    sources = stats.get("sources", [])
    if not isinstance(sources, list):
        return findings

    for i, a in enumerate(sources):
        if not isinstance(a, str):
            continue
        for b in sources[i + 1 :]:
            if not isinstance(b, str):
                continue
            # Check for prefix patterns (e.g., chris-personal vs personal)
            a_parts = a.split("-")
            b_parts = b.split("-")
            if len(a_parts) > 1 and a_parts[-1] == b:
                findings.append(
                    Finding(
                        category="Source Naming",
                        message=f"Sources `{a}` and `{b}` may be duplicates (prefix pattern)",
                    )
                )
            elif len(b_parts) > 1 and b_parts[-1] == a:
                findings.append(
                    Finding(
                        category="Source Naming",
                        message=f"Sources `{b}` and `{a}` may be duplicates (prefix pattern)",
                    )
                )
    return findings


def check_low_quality(entries: list[dict[str, object]]) -> list[Finding]:
    """Flag entries with very short descriptions or no content."""
    findings: list[Finding] = []
    for entry in entries:
        data = entry.get("data", {})
        if not isinstance(data, dict):
            continue
        desc = data.get("description", "")
        if isinstance(desc, str) and len(desc) < 10:
            findings.append(
                Finding(
                    category="Low Quality",
                    message=(
                        f"`{entry.get('id', '?')}` ({entry.get('type', '?')}): "
                        f'description too short ({len(desc)} chars): "{desc}"'
                    ),
                    entry_id=str(entry.get("id", "")),
                )
            )
    return findings


def check_tag_outliers(tags: list[dict[str, object]]) -> list[Finding]:
    """Summarize tags used only once (may indicate low-value tags)."""
    singletons = [
        str(t["tag"])
        for t in tags
        if isinstance(t.get("count"), int) and t["count"] == 1 and isinstance(t.get("tag"), str)
    ]
    if not singletons:
        return []
    # Report as a single finding with count, not one per tag
    tag_list = ", ".join(f"`{t}`" for t in sorted(singletons)[:20])
    suffix = f" ... and {len(singletons) - 20} more" if len(singletons) > 20 else ""
    return [
        Finding(
            category="Singleton Tags",
            message=f"{len(singletons)} tags used only once: {tag_list}{suffix}",
        )
    ]


# --- Report formatting ---


def format_report(report: AuditReport) -> str:
    """Format the audit report as markdown."""
    now = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "## Awareness Store Hygiene Report",
        "",
        f"Generated: {now}",
        f"Store stats: {report.entry_count} entries across "
        f"{report.source_count} sources, {report.tag_count} tags",
        "",
    ]

    if not report.has_findings:
        lines.append("### All Clear")
        lines.append("")
        lines.append("No hygiene issues found.")
        lines.append("")
        return "\n".join(lines)

    lines.append("### Findings")
    lines.append("")

    # Group by category
    categories: dict[str, list[Finding]] = {}
    for f in report.findings:
        categories.setdefault(f.category, []).append(f)

    for category, category_findings in sorted(categories.items()):
        n = len(category_findings)
        lines.append(f"#### {category} ({n} issue{'s' if n != 1 else ''})")
        lines.append("")
        for f in category_findings:
            lines.append(f"- {f.message}")
        lines.append("")

    total = len(report.findings)
    cat_count = len(categories)
    lines.append("### Summary")
    lines.append("")
    lines.append(
        f"{total} issue{'s' if total != 1 else ''} found "
        f"across {cat_count} categor{'ies' if cat_count != 1 else 'y'}."
    )
    lines.append("")

    return "\n".join(lines)


def fingerprint(report_text: str) -> str:
    """Hash the report content (excluding the timestamp line)."""
    # Strip the Generated: line so timestamps don't invalidate the fingerprint
    lines = [line for line in report_text.splitlines() if not line.startswith("Generated:")]
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()[:16]


# --- GitHub issue management ---


async def manage_github_issue(repo: str, report_text: str, has_findings: bool, token: str) -> None:
    """Create, update, or close the hygiene audit GitHub issue."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as http:
        # Find existing issue
        resp = await http.get(
            f"{GITHUB_API}/repos/{repo}/issues",
            params={"labels": ISSUE_LABEL, "state": "all", "per_page": 1},
        )
        resp.raise_for_status()
        issues = resp.json()
        existing = issues[0] if issues else None

        if has_findings:
            if existing:
                # Update existing issue
                update: dict[str, object] = {"body": report_text}
                if existing["state"] == "closed":
                    update["state"] = "open"
                await http.patch(
                    f"{GITHUB_API}/repos/{repo}/issues/{existing['number']}",
                    json=update,
                )
                logger.info("Updated issue #%d", existing["number"])
            else:
                # Create new issue
                resp = await http.post(
                    f"{GITHUB_API}/repos/{repo}/issues",
                    json={
                        "title": ISSUE_TITLE,
                        "body": report_text,
                        "labels": [ISSUE_LABEL],
                    },
                )
                resp.raise_for_status()
                logger.info("Created issue #%d", resp.json()["number"])
        elif existing and existing["state"] == "open":
            # Close issue — all clean
            await http.post(
                f"{GITHUB_API}/repos/{repo}/issues/{existing['number']}/comments",
                json={"body": "All clean — no hygiene issues found. Closing."},
            )
            await http.patch(
                f"{GITHUB_API}/repos/{repo}/issues/{existing['number']}",
                json={"state": "closed"},
            )
            logger.info("Closed issue #%d — all clean", existing["number"])


# --- Main ---


async def run_audit(
    url: str,
    repo: str | None,
    dry_run: bool,
    token: str | None,
) -> None:
    """Run the full audit pipeline."""
    client = AwarenessClient(url=url, source=FINGERPRINT_SOURCE)

    try:
        stats = await client.get_stats()
        tags = await client.get_tags()
        patterns = await client.get_knowledge(entry_type="pattern")
        all_knowledge = await client.get_knowledge()

        report = AuditReport(
            stats=stats,
            tag_count=len(tags),
            source_count=len(stats.get("sources", [])),
            entry_count=stats.get("total", 0),  # type: ignore[arg-type]
        )

        # Run checks
        report.findings.extend(check_tag_drift(tags))
        report.findings.extend(check_mistyped_patterns(patterns))
        report.findings.extend(check_source_naming(stats))
        report.findings.extend(check_low_quality(all_knowledge))
        report.findings.extend(check_tag_outliers(tags))

        report_text = format_report(report)
        fp = fingerprint(report_text)

        if dry_run or not repo:
            click.echo(report_text)
            click.echo(f"Fingerprint: {fp}", err=True)
            return

        # Check fingerprint — skip if unchanged
        existing_fp = await client.get_knowledge(tags=[FINGERPRINT_TAG])
        for entry in existing_fp:
            data = entry.get("data", {})
            if isinstance(data, dict) and data.get("description", "").endswith(fp):
                logger.info("Fingerprint unchanged (%s), skipping GitHub update", fp)
                return

        if not token:
            click.echo("Error: GITHUB_TOKEN not set", err=True)
            raise SystemExit(1)

        await manage_github_issue(repo, report_text, report.has_findings, token)

        # Store new fingerprint
        await client.add_context(
            source=FINGERPRINT_SOURCE,
            tags=[FINGERPRINT_TAG],
            description=f"Audit fingerprint: {fp}",
            expires_days=7,
        )
        logger.info("Stored fingerprint: %s", fp)

    finally:
        await client.close()


@click.command()
@click.option("--url", default="http://localhost:8420", help="Awareness server URL.")
@click.option("--repo", default=None, help="GitHub repo for issue (owner/repo).")
@click.option("--dry-run", is_flag=True, help="Print report to stdout, don't touch GitHub.")
@click.option("--token-env", default="GITHUB_TOKEN", help="Env var for GitHub token.")
def main(url: str, repo: str | None, dry_run: bool, token_env: str) -> None:
    """Audit the mcp-awareness store for data hygiene issues."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        stream=sys.stderr,
    )
    token = os.environ.get(token_env)
    if repo and not token and not dry_run:
        click.echo(f"Error: {token_env} not set", err=True)
        raise SystemExit(1)
    asyncio.run(run_audit(url, repo, dry_run, token))


if __name__ == "__main__":
    main()
