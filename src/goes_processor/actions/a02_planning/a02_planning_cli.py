# src/goes_processor/actions/a02_planning/a02_planning_cli.py

# =============================================================================
# FILE PATH:
# src/goes_processor/actions/a02_planning/a02_planning_cli.py
#
# Purpose: Main CLI group for GOES-R Planning Commands.
# This is the top-level entry point for all planning-related operations.
# It registers subcommands for generating and checking download plans.
#
# Features:
#   - Group command: planning
#   - Subcommands: gen-plan, check-plan
#   - Easy to extend with new planning commands in the future
#   - Clean and minimal: only imports and registers subcommands
#
# Usage examples:
#   goes-processor planning gen-plan --product ALL --year 2026 --day 003 --sat-position ALL
#   goes-processor planning check-plan --product ALL --year 2026 --day 003 --sat-position ALL
# =============================================================================

import click

# Import subcommands
from .core01_planner_download.gen_plan_cli import gen_plan_cmd
from .core01_planner_download.check_plan_cli import check_plan_cmd


@click.group(name="planning")
def planning():
    """GOES-R Planning Commands (v.0.8.5)"""
    pass


# Register subcommands
planning.add_command(gen_plan_cmd, name="gen-plan-download")
planning.add_command(check_plan_cmd, name="check-plan-download")


# Optional: Allow direct execution for testing
if __name__ == "__main__":
    planning()
