# src/goes_processor/main.py

# =============================================================================
# FILE PATH:
# src/goes_processor/main.py
#
# Purpose: Main entry point for the GOES Processor CLI tool.
# This is the root command that groups all top-level subcommands.
# It initializes global SatPy configuration (custom YAMLs, cache) and registers
# all main command groups (planning, download, processing).
#
# Features:
#   - Root CLI group with version
#   - SatPy global configuration (cache directory, custom composites/enhancements)
#   - Registers top-level groups: planning, download, processing
#   - Clean and minimal: only imports, config, and command registration
#
# Usage examples:
#   goes-processor --help
#   goes-processor planning --help
#   goes-processor download --help
#   goes-processor processing --help
# =============================================================================

import click
import os
import satpy
from pathlib import Path

# --- GLOBAL SATPY CONFIGURATION ---
# This runs once when the CLI is invoked
BASE_DIR = Path(__file__).parent
CUSTOM_CONFIG = BASE_DIR / "satpy_config"
CACHE_DIR = BASE_DIR / "satpy_cache"

# Add custom config path if not already present
current_paths = satpy.config.get("config_path", [])
if str(CUSTOM_CONFIG) not in current_paths:
    satpy.config.set(config_path=[str(CUSTOM_CONFIG)] + current_paths)

# Set cache directory
satpy.config.set(cache_dir=str(CACHE_DIR))
os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)


# --- ROOT CLI GROUP ---
@click.group()
@click.version_option(version="0.5.1", prog_name="Satellite Processor Tool")
def cli():
    """
    SAT-PROC v.0.5.1: Legion Edition - Thesis Audit Version.
    
    GOES data processing tool for downloading, planning, and processing L2 products.
    """
    pass


# --- COMMAND GROUP REGISTRATION ---

# 1. Planning group (gen-plan-download, check-plan-download, etc.)
from .actions.a02_planning.a02_planning_cli import planning as planning_group
cli.add_command(planning_group, name="planning")  # Invoked as: goes-processor planning ...

# 2. Download group (commented - enable when ready)
# from .actions.a03_download.download_cli import download as download_group
# cli.add_command(download_group, name="download")  # Invoked as: goes-processor download ...

# 3. Processing group (commented - enable when ready)
# from .actions.a04_processing.processing_cli import processing as processing_group
# cli.add_command(processing_group, name="processing")  # Invoked as: goes-processor processing ...


# Run the CLI if executed directly
if __name__ == "__main__":
    cli()
