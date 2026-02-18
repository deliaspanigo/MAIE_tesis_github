import click
# Importamos desde el nuevo nombre de archivo
from .cli_core01 import proc_single_file_cmd

@click.group(name="processing")
def processing_group():
    """GOES-R Processing Commands (v.0.3.1)"""
    pass

processing_group.add_command(proc_single_file_cmd)
