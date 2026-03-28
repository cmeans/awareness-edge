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

"""CLI entry point for awareness-edge."""

from __future__ import annotations

import asyncio
import logging
import sys

import click

from awareness_edge import __version__


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(__version__, "-v", "--version", prog_name="awareness-edge")
@click.pass_context
def main(ctx: click.Context) -> None:
    """awareness-edge — MCP-to-MCP bridge agent for system awareness."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=False),
    default=None,
    help="Path to config YAML file.",
)
@click.option(
    "--once",
    is_flag=True,
    default=False,
    help="Run a single collection cycle and exit.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be done without writing to external systems.",
)
def run(config_path: str | None, *, once: bool, dry_run: bool) -> None:
    """Start the edge collection loop."""
    from awareness_edge.core.config import load_config
    from awareness_edge.core.scheduler import run_loop

    config = load_config(config_path)
    logging.basicConfig(
        level=getattr(logging, config.logging_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        stream=sys.stderr,
    )
    asyncio.run(run_loop(config, once=once, dry_run=dry_run))


@main.command("check-config")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=False),
    default=None,
    help="Path to config YAML file.",
)
def check_config(config_path: str | None) -> None:
    """Validate config and print a summary."""
    from awareness_edge.core.config import load_config

    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"Config error: {exc}", err=True)
        raise SystemExit(1) from exc

    click.echo(f"Awareness URL:  {config.awareness.url}")
    click.echo(f"Source:         {config.awareness.source}")
    click.echo(f"Evaluator:      {config.evaluator.type}")
    click.echo(f"Poll interval:  {config.poll_interval_sec}s")
    click.echo(f"Providers:      {len(config.providers)}")
    for p in config.providers:
        status = "enabled" if p.enabled else "disabled"
        click.echo(f"  - {p.name} (type={p.type}, {status})")
    click.echo(f"Sinks:          {len(config.sinks)}")
    for s in config.sinks:
        status = "enabled" if s.enabled else "disabled"
        click.echo(f"  - {s.name} (type={s.type}, {status})")
    click.echo("Config OK.")
