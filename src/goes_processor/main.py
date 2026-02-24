# src/goes_processor/main.py
import click
import os
import satpy
from pathlib import Path

# --- ENVIRONMENT INITIALIZATION ---
BASE_DIR = Path(__file__).parent
CUSTOM_CONFIG = BASE_DIR / "satpy_config"
CACHE_DIR = BASE_DIR / "satpy_cache"

current_paths = satpy.config.get("config_path", [])
if str(CUSTOM_CONFIG) not in current_paths:
    satpy.config.set(config_path=[str(CUSTOM_CONFIG)] + current_paths)

satpy.config.set(cache_dir=str(CACHE_DIR))
os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)

@click.group()
@click.version_option(version="0.5.6", prog_name="Satellite Processor Tool")
def cli():
    """
    SAT-PROC v.0.5.6: Legion Edition - Thesis Audit Version.
    """
    pass

# --- COMMAND REGISTRATION ---

# 1. Planner
from .actions.a02_planner.planner_cli import cli as planner_group
# 2. Download (Corregido: Importando el grupo de descarga correcto)
from .actions.a03_download.download_cli import cli as download_group
# 3. Processing
from .actions.processing.processing_cli import processing_group 

cli.add_command(planner_group)
cli.add_command(download_group) # Ahora coincide con el import
cli.add_command(processing_group)

if __name__ == "__main__":
    cli()
