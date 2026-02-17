# src/goes_processor/main.py
import click
from .my_satpy_config_folder.my_config_satpy import *

@click.group()
@click.version_option(version="0.0.1", prog_name="Satellite Processor Tool")
def cli():
    """
    SAT-PROC: Herramienta profesional para el procesamiento de datos GOES.
    """
    pass

# Registro de comandos usando la ruta de la carpeta 'actions'
from .actions.download.download_cli import download
cli.add_command(download)

# Registro del grupo de procesamiento
from .actions.processing.processing_cli import processing_group 
cli.add_command(processing_group)

if __name__ == "__main__":
    cli()
