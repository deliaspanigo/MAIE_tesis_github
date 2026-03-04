"""
Path: src/goes_processor/actions/a02_planning/a02_planning_cli.py
Description: Planning orchestrator. Action ID: a02
"""
import click
import sys

# Import Gen Plan
try:
    from goes_processor.actions.a02_planning.core01_planner_download.cli01_gen_plan_download import gen_plan_download_command
except ImportError as e:
    print(f"❌ Error importing gen-plan: {e}")
    gen_plan_download_command = None

# Import Check Plan
try:
    from goes_processor.actions.a02_planning.core01_planner_download.cli02_check_plan import check_plan_command
except ImportError as e:
    print(f"❌ Error importing check-plan: {e}")
    check_plan_command = None

@click.group(name="planning")
def planning_group():
    """Actions for data planning and verification."""
    pass

# Registration
if gen_plan_download_command:
    planning_group.add_command(gen_plan_download_command)

if check_plan_command:
    # This MUST match the @click.command(name="check-plan-download") in cli02
    planning_group.add_command(check_plan_command)
