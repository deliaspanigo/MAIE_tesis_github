import click
from .bulk_cli import bulk_cmd 

@click.group(name="processing")
def processing_group():
    """Módulo de procesamiento de imágenes satelitales."""
    pass

processing_group.add_command(bulk_cmd)
