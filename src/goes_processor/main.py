# src/goes_processor/main.py
import click
import os
import satpy
from pathlib import Path

# --- ENVIRONMENT INITIALIZATION ---
BASE_DIR = Path(__file__).parent
# Based on your 'tree' command:
CUSTOM_CONFIG = BASE_DIR / "satpy_config"
CACHE_DIR = BASE_DIR / "satpy_cache"

# Robust way to register custom YAML paths
current_paths = satpy.config.get("config_path", [])
if str(CUSTOM_CONFIG) not in current_paths:
    # We put your folder at the beginning to give it priority
    satpy.config.set(config_path=[str(CUSTOM_CONFIG)] + current_paths)

# Set global cache for Satpy and Pyresample
satpy.config.set(cache_dir=str(CACHE_DIR))
os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)

@click.group()
@click.version_option(version="0.3.4", prog_name="Satellite Processor Tool")
def cli():
    """
    SAT-PROC v.0.3.4: Legion Edition - Thesis Audit Version.
    """
    pass

# --- COMMAND REGISTRATION ---
# Make sure these match your physical folder names exactly
from .actions.download.download_cli import download
from .actions.processing.processing_cli import processing_group 

cli.add_command(download)
cli.add_command(processing_group)

if __name__ == "__main__":
    cli()
