"""
Path: src/goes_processor/actions/a02_planning/core01_planner_download/cli01_gen_plan_download.py
Description: CLI Interface for generating GOES download plans.
This module defines the 'gen-plan-download' command and its arguments.
"""

import sys

# 1. Try to import external dependencies
try:
    import click
except ImportError as e:
    print(f"❌ Dependency Error: 'click' library not found. {e}")
    sys.exit(1)

# 2. Try to import internal logic engine
try:
    # This must match the function name in code01_gen_plan_download.py
    from goes_processor.actions.a02_planning.core01_planner_download.code01_gen_plan_download import execute_gen_plan
except ImportError as e:
    print(f"❌ Critical Import Error in 'cli01_gen_plan_download.py': {e}")
    execute_gen_plan = None

@click.command(name="gen-plan-download")
@click.option('--sat-position', required=True, type=click.Choice(['east', 'west']), help='Satellite position (east/west)')
@click.option('--product', required=True, help='GOES Product (e.g., ABI-L2-LSTF)')
@click.option('--year', required=True, type=int, help='Year YYYY')
@click.option('--day', required=True, type=str, help='Julian Day DDD (e.g., 003)')
@click.option('--overwrite', default=False, type=bool, help='Overwrite existing JSON plan')
@click.option('--check-local', default=True, type=bool, help='Check if files already exist in local storage')
def gen_plan_download_command(sat_position, product, year, day, overwrite, check_local):
    """
    Generate a JSON download plan for GOES data.
    This command creates a roadmap of files to be downloaded from S3.
    """
    if execute_gen_plan is None:
        click.echo("🚫 Logic engine (code01) is unavailable. Check import errors above.", err=True)
        sys.exit(1)

    click.echo(f"📋 Task: Generating download plan...")
    click.echo(f"📍 Satellite: {sat_position} | Product: {product} | Date: {year}-{day}")
    
    # 3. Call the core logic engine
    try:
        execute_gen_plan(
            sat_position=sat_position,
            product=product,
            year=year,
            day=day,
            overwrite=overwrite,
            check_local=check_local
        )
        click.echo("✅ Plan generation process finished.")
    except Exception as e:
        click.echo(f"💥 Runtime Error during plan generation: {e}", err=True)

if __name__ == "__main__":
    gen_plan_download_command()
