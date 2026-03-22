"""Tests for the data hygiene audit checks."""

from __future__ import annotations

from examples.audit_store import (
    AuditReport,
    Finding,
    check_low_quality,
    check_mistyped_patterns,
    check_source_naming,
    check_tag_drift,
    check_tag_outliers,
    fingerprint,
    format_report,
)

# --- Tag drift ---


def test_tag_drift_prefix_match() -> None:
    tags = [
        {"tag": "synology", "count": 7},
        {"tag": "synology-mcp", "count": 2},
    ]
    findings = check_tag_drift(tags)
    assert len(findings) == 1
    assert "synology" in findings[0].message


def test_tag_drift_plural() -> None:
    tags = [
        {"tag": "project", "count": 5},
        {"tag": "projects", "count": 2},
    ]
    findings = check_tag_drift(tags)
    assert len(findings) == 1


def test_tag_drift_no_false_positive_edit_distance() -> None:
    """Unrelated words that happen to be close in edit distance should not match."""
    tags = [
        {"tag": "docker", "count": 6},
        {"tag": "soccer", "count": 1},
    ]
    findings = check_tag_drift(tags)
    assert len(findings) == 0


def test_tag_drift_no_false_positive_unrelated() -> None:
    tags = [
        {"tag": "garmin", "count": 5},
        {"tag": "admin", "count": 1},
    ]
    findings = check_tag_drift(tags)
    assert len(findings) == 0


def test_tag_drift_hyphen_subtag_not_flagged() -> None:
    """Intentional sub-tags like sleep/deep-sleep should not be flagged."""
    tags = [
        {"tag": "sleep", "count": 3},
        {"tag": "deep-sleep", "count": 1},
    ]
    findings = check_tag_drift(tags)
    assert len(findings) == 0


def test_tag_drift_short_prefix_not_flagged() -> None:
    tags = [
        {"tag": "mcp", "count": 5},
        {"tag": "mcp-awareness", "count": 3},
    ]
    # "mcp" is only 3 chars, prefix check requires >= 5
    findings = check_tag_drift(tags)
    assert len(findings) == 0


# --- Mistyped patterns ---


def test_mistyped_pattern_missing_conditions() -> None:
    entries = [
        {
            "id": "abc-123",
            "type": "pattern",
            "data": {
                "description": "Complete pattern",
                "conditions": {"day": "Monday"},
                "effect": "something",
            },
        },
        {
            "id": "def-456",
            "type": "pattern",
            "data": {"description": "Bad pattern"},
        },
    ]
    findings = check_mistyped_patterns(entries)
    assert len(findings) == 1
    assert "def-456" in findings[0].message
    assert "conditions" in findings[0].message


def test_mistyped_pattern_complete() -> None:
    entries = [
        {
            "id": "abc-123",
            "type": "pattern",
            "data": {
                "description": "Good pattern",
                "conditions": {"day_of_week": "Monday"},
                "effect": "high CPU expected",
            },
        },
    ]
    findings = check_mistyped_patterns(entries)
    assert len(findings) == 0


# --- Source naming ---


def test_source_naming_prefix_pattern() -> None:
    stats = {"sources": ["chris-personal", "personal", "nas"]}
    findings = check_source_naming(stats)
    assert len(findings) == 1
    assert "chris-personal" in findings[0].message
    assert "personal" in findings[0].message


def test_source_naming_clean() -> None:
    stats = {"sources": ["personal", "nas", "mcp-awareness-project"]}
    findings = check_source_naming(stats)
    assert len(findings) == 0


# --- Low quality ---


def test_low_quality_short_description() -> None:
    entries = [
        {"id": "abc", "type": "note", "data": {"description": "hi"}},
        {"id": "def", "type": "note", "data": {"description": "A proper description of something"}},
    ]
    findings = check_low_quality(entries)
    assert len(findings) == 1
    assert "abc" in findings[0].message


# --- Tag outliers ---


def test_singleton_tags_summary() -> None:
    tags = [
        {"tag": "garmin", "count": 5},
        {"tag": "typo-tag", "count": 1},
        {"tag": "another-single", "count": 1},
    ]
    findings = check_tag_outliers(tags)
    assert len(findings) == 1
    assert "2 tags used only once" in findings[0].message
    assert "another-single" in findings[0].message
    assert "typo-tag" in findings[0].message


def test_singleton_tags_none() -> None:
    tags = [
        {"tag": "garmin", "count": 5},
        {"tag": "health", "count": 3},
    ]
    findings = check_tag_outliers(tags)
    assert len(findings) == 0


# --- Report formatting ---


def test_format_report_with_findings() -> None:
    report = AuditReport(
        entry_count=100,
        source_count=5,
        tag_count=20,
        findings=[
            Finding(category="Tag Drift", message="test finding 1"),
            Finding(category="Tag Drift", message="test finding 2"),
            Finding(category="Low Quality", message="test finding 3"),
        ],
    )
    text = format_report(report)
    assert "## Awareness Store Hygiene Report" in text
    assert "100 entries" in text
    assert "Tag Drift (2 issues)" in text
    assert "Low Quality (1 issue)" in text
    assert "3 issues found across 2 categories" in text


def test_format_report_no_findings() -> None:
    report = AuditReport(entry_count=50, source_count=3, tag_count=10)
    text = format_report(report)
    assert "All Clear" in text
    assert "No hygiene issues found" in text


# --- Fingerprint ---


def test_fingerprint_ignores_timestamp() -> None:
    report_a = "Generated: 2026-03-21T10:00:00Z\nSome content\n"
    report_b = "Generated: 2026-03-22T15:00:00Z\nSome content\n"
    assert fingerprint(report_a) == fingerprint(report_b)


def test_fingerprint_changes_with_content() -> None:
    report_a = "Generated: 2026-03-21T10:00:00Z\nContent A\n"
    report_b = "Generated: 2026-03-21T10:00:00Z\nContent B\n"
    assert fingerprint(report_a) != fingerprint(report_b)
