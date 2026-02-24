import click
# Import the function directly from the submodule
from .cli_core01_p01_download import run_planner_download_cmd

@click.group(name="planner")
def cli():
    """GOES-R Planning Commands (v.0.4.0)"""
    pass

# Attach the command to this group
cli.add_command(run_planner_download_cmd)
