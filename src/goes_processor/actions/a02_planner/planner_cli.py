# src/goes_processor/actions/a02_planner/planner_cli.py
import click
# Importamos los comandos de descarga y procesamiento
from .cli_core01_p01_download import run_planner_download_cmd
from .cli_core02_p02_processing import run_planner_processing_cmd

@click.group(name="planner")
def cli():
    """GOES-R Planning Commands (v.0.8.5)"""
    pass

# Comando de Descarga (p01)
cli.add_command(run_planner_download_cmd)

# Comando de Procesamiento (p02)
cli.add_command(run_planner_processing_cmd)
