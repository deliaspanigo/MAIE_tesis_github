# =============================================================================
# FILE PATH:
# src/goes_processor/actions/a03_download/download_cli.py
#
# Purpose: CLI group for GOES-R Download Commands.
# This is the top-level entry point for all download-related operations.
# It registers subcommands for running actual downloads based on generated plans.
#
# Features:
#   - Group command: download
#   - Subcommand: run-download (from cli_run_plan_download)
#   - Clean and minimal: only imports and registers subcommands
#   - Easy to extend with new download-related commands in the future
#
# Usage examples:
#   goes-processor download run-download --plan-file path/to/plan.json
#   goes-processor download run-download --help
# =============================================================================

import click

# Import subcommands
from .cli_run_plan_download import run_download_cmd


@click.group(name="download")
def download():
    """GOES-R Download Commands (v.0.5.2)"""
    pass


# Register subcommands
download.add_command(run_download_cmd, name="run-download")


# Optional: Allow direct execution for testing
if __name__ == "__main__":
    download()
