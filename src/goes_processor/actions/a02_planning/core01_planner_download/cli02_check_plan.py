"""
Path: src/goes_processor/actions/a02_planning/core01_planner_download/cli02_check_plan.py
Description: CLI Interface to verify the existence and status of a download plan.
"""

import click
import sys

# Import logic
try:
    from goes_processor.actions.a02_planning.core01_planner_download.code02_check_plan_download import execute_check_plan
except ImportError as e:
    print(f"❌ Critical Import Error in 'cli02_check_plan.py': {e}")
    execute_check_plan = None

@click.command(name="check-plan-download") # Nombre exacto que buscabas
@click.option('--sat-position', required=True, type=click.Choice(['east', 'west']))
@click.option('--product', required=True)
@click.option('--year', required=True, type=int)
@click.option('--day', required=True, type=str)
def check_plan_command(sat_position, product, year, day):
    """
    Check if a download plan exists and verify its internal status.
    """
    if execute_check_plan is None:
        click.echo("🚫 Logic engine (code02) is unavailable.", err=True)
        return

    click.echo(f"🔍 Checking plan status for {product} ({sat_position})...")
    execute_check_plan(sat_position, product, year, day)
