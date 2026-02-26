import click
# Importamos la función del comando desde el archivo cli_core01_...
from .cli_core01_proc_each_file import run_processor_each_file_cmd

@click.group(name="processing")
def cli():
    """Fase de Procesamiento: Generación de productos (v.0.5.1)"""
    pass

# REGISTRO CLAVE: Aquí es donde Click se entera de que el comando existe
cli.add_command(run_processor_each_file_cmd)
