# awareness-edge — bridge between your systems and AI awareness
# Copyright (C) 2026 Chris Means
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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


def test_import_sinks() -> None:
    from awareness_edge.sinks import get_sink

    assert callable(get_sink)
