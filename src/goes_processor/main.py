# src/goes_processor/main.py

import click

# Importa y aplica la configuración global de Satpy (se ejecuta automáticamente)
from .my_config_satpy import *  # Esto ejecuta todo el código de config_satpy.py

# Importa el grupo principal (definido aquí)
@click.group()
@click.version_option(version="0.0.1", prog_name="Satellite Processor Tool")
def cli():
    """
    SAT-PROC: Herramienta profesional para el procesamiento de datos GOES.
    """
    pass

# Importa y registra el comando download (desde su archivo separado)
from .download.download_cli import download
cli.add_command(download)

# Importa y registra el comando processing_group (desde su archivo separado)
from .processing.processing_cli import processing_group 
cli.add_command(processing_group)

if __name__ == "__main__":
    cli()
