#!/usr/bin/env python3
"""Audit the mcp-awareness store for data hygiene issues.

Connects to mcp-awareness, runs quality checks, and stores findings
back in awareness for later retrieval and analysis. Uses a fingerprint
to skip redundant updates when findings haven't changed.

Usage:
    # Dry-run (print report to stdout, don't store)
    uv run python examples/audit_store.py --dry-run

    # Store findings in awareness
    uv run python examples/audit_store.py --url http://localhost:8420/secret
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime

import click

from awareness_edge.core.client import AwarenessClient

logger = logging.getLogger(__name__)

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


# --- Main ---


REPORT_TAGS = ["hygiene-audit", "awareness-edge", "data-quality", "actionable"]


async def _store_report(client: AwarenessClient, report_text: str, fp: str) -> None:
    """Store the full report in awareness, updating in place if one exists."""
    description = f"Hygiene audit report (fingerprint: {fp})"

    # Check if a report entry already exists
    existing = await client.get_knowledge(tags=["hygiene-audit", "data-quality"])
    for entry in existing:
        data = entry.get("data", {})
        if isinstance(data, dict) and "Hygiene audit report" in data.get("description", ""):
            await client.update_entry(
                entry_id=str(entry["id"]),
                description=description,
                content=report_text,
            )
            logger.info("Updated existing audit report in awareness")
            return

    # No existing report — create new
    await client.remember(
        source=FINGERPRINT_SOURCE,
        tags=REPORT_TAGS,
        description=description,
        content=report_text,
        learned_from="awareness-edge",
    )
    logger.info("Stored new audit report in awareness")


async def run_audit(url: str, *, dry_run: bool) -> None:
    """Run the full audit pipeline."""
    client = AwarenessClient(url=url, source=FINGERPRINT_SOURCE)

    try:
        stats = await client.get_stats()
        tags = await client.get_tags()
        patterns = await client.get_knowledge(entry_type="pattern")
        all_knowledge_raw = await client.get_knowledge()

        # Exclude audit's own entries to avoid self-referential fingerprint drift
        all_knowledge = [e for e in all_knowledge_raw if FINGERPRINT_TAG not in e.get("tags", [])]

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

        if dry_run:
            click.echo(report_text)
            click.echo(f"Fingerprint: {fp}", err=True)
            return

        # Check fingerprint — skip if unchanged
        fp_description = f"Audit fingerprint: {fp}"
        existing_fp = await client.get_knowledge(tags=[FINGERPRINT_TAG])
        fp_entry_id: str | None = None
        for entry in existing_fp:
            data = entry.get("data", {})
            if not isinstance(data, dict):
                continue
            desc = data.get("description", "")
            if "Audit fingerprint:" not in desc:
                continue
            if desc == fp_description:
                logger.info("Fingerprint unchanged (%s), skipping", fp)
                return
            # Stale fingerprint — remember most recent one for update
            fp_entry_id = str(entry["id"])

        # Store full report in awareness (private, cross-platform accessible)
        await _store_report(client, report_text, fp)

        # Store/update fingerprint to skip redundant runs
        if fp_entry_id:
            await client.update_entry(entry_id=fp_entry_id, description=fp_description)
        else:
            await client.add_context(
                source=FINGERPRINT_SOURCE,
                tags=[FINGERPRINT_TAG],
                description=fp_description,
                expires_days=7,
            )
        logger.info("Stored fingerprint: %s", fp)

    finally:
        await client.close()


@click.command()
@click.option("--url", default="http://localhost:8420", help="Awareness server URL.")
@click.option("--dry-run", is_flag=True, help="Print report to stdout, don't store.")
def main(url: str, *, dry_run: bool) -> None:
    """Audit the mcp-awareness store for data hygiene issues."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        stream=sys.stderr,
    )
    asyncio.run(run_audit(url, dry_run=dry_run))


if __name__ == "__main__":
    main()
