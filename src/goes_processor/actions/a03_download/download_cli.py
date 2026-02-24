# src/goes_processor/actions/a03_download/download_cli.py
import click
from .cli_run_plan_download import run_download_cmd

@click.group(name="download")
def cli():
    """GOES-R Download Commands (v.0.5.2)"""
    pass

# Adjuntamos el comando de descarga, NO el de planner
cli.add_command(run_download_cmd)
