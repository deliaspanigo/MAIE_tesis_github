# src/goes_processor/actions/processing/processing_cli.py
import click
# IMPORTANTE: El nombre de la carpeta debe ser idéntico al del tree
from .core_01_proc_one_file_cli import proc_single_file_cmd

@click.group(name="processing")
def processing_group():
    """
    GOES-R Processing Commands (v.0.3.1)
    """
    pass

# Registramos el comando 'one-file'
processing_group.add_command(proc_single_file_cmd)
