"""Smoke tests — verify the package is importable."""

from __future__ import annotations


def test_version() -> None:
    from awareness_edge import __version__

    assert isinstance(__version__, str)
    assert __version__


def test_import_cli() -> None:
    from awareness_edge.cli import main

    assert callable(main)


def test_import_providers() -> None:
    from awareness_edge.providers import get_provider

    assert callable(get_provider)


def test_import_evaluators() -> None:
    from awareness_edge.evaluator import get_evaluator

    assert callable(get_evaluator)
