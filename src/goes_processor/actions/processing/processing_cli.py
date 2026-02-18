import click
from .cli_core01 import proc_single_file_cmd
from .cli_core02 import proc_accumulation_cmd  # <--- Nuevo import

@click.group(name="processing")
def processing_group():
    """GOES-R Processing Commands (v.0.4.0)"""
    pass

processing_group.add_command(proc_single_file_cmd)
processing_group.add_command(proc_accumulation_cmd) # <--- Registro del comando
