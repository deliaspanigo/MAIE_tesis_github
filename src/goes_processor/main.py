"""
Path: src/goes_processor/main.py
"""
import click

# Cambia esta línea:
# DE: from .task.task02_download.zzz_task02_download_cli import task02_group
# A: (Asegúrate de que el archivo en la carpeta se llame task02_download_cli.py)
from .task.task02_download.task02_download_cli import task02_group

@click.group()
@click.version_option(version="0.2.1", prog_name="GOES Processor")
def cli():
    """🛰️ GOES-PROCESSOR: Herramienta de adquisición y procesamiento (Tesis 2026)"""
    pass

cli.add_command(task02_group, name="download")

if __name__ == "__main__":
    cli()
