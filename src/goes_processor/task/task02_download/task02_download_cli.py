"""
Path: src/goes_processor/task/task02_download/task02_download_cli.py
Version: 1.6.0 (Explicit Command Mapping)
"""
import click
from .cli01_gen_plan_download import gen_plan_command
from .cli02_check_plan_download import check_plan_command
from .cli03_run_download_plan import download_s3_command

@click.group()
def task02_group():
    """Acciones de adquisición de datos satelitales."""
    pass

# Mapeo exacto de los nombres de comandos que solicitaste
task02_group.add_command(gen_plan_command, name="gen-plan-download")
task02_group.add_command(check_plan_command, name="check-plan-download")
task02_group.add_command(download_s3_command, name="run-plan-download")
