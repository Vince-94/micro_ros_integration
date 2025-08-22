#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Copyright (c) 2025 Ruotolo Vincenzo. All rights reserved.
#
# This software is proprietary and licensed, not sold. See the LICENSE.md file
# in the project root for the full license terms.
#
# Unauthorized copying, distribution, modification, or resale of this file,
# via any medium, is strictly prohibited without prior written permission.
# -----------------------------------------------------------------------------
import click


@click.group()
def cli():
    """Robotics Container Tool Command Line Interface"""


@cli.command()
@click.option("--platform", required=True, type=click.Choice(["rp2040", "esp32", "stm32"]), help="Target platform")
def install(platform: str):
    """Install dependencies"""
    pass


@cli.command()
@click.option("--platform", required=True, type=click.Choice(["rp2040", "esp32", "stm32"]), help="Target platform")
def build(platform: str):
    """Build firmware"""
    pass


@cli.command()
@click.option("--platform", required=True, type=click.Choice(["rp2040", "esp32", "stm32"]), help="Target platform")
def flash(platform: str):
    """Falash firmware"""
    pass


@cli.command()
@click.option("--platform", required=True, type=click.Choice(["rp2040", "esp32", "stm32"]), help="Target platform")
def verify(platform: str):
    """Verify firmware"""
    pass


@cli.command()
@click.option("--platform", required=True, type=click.Choice(["rp2040", "esp32", "stm32"]), help="Target platform")
def clean(platform: str):
    """Clean build artifats"""
    pass


@cli.command(name="helpme")
def help_command():
    """Display this help message"""
    click.echo(cli.get_help())


if __name__ == "__main__":
    cli()
