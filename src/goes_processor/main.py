"""
Path: src/goes_processor/main.py
Version: 0.1.9 (v0.0.2 - Full CLI Integration)
"""

# 1. SYSTEM LAYER
try:
    import click
    import os
    import satpy
    from pathlib import Path
except ImportError as e:
    print(f"\n [SYSTEM LIB ERROR] - In main.py: {e}\n")
    raise SystemExit(1)

# --- GLOBAL SATPY & CACHE CONFIGURATION ---
BASE_DIR = Path(__file__).parent.resolve()
CUSTOM_CONFIG = BASE_DIR / "satpy_config"
CACHE_DIR = BASE_DIR / "satpy_cache"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

current_paths = satpy.config.get("config_path", [])
if str(CUSTOM_CONFIG) not in current_paths:
    satpy.config.set(config_path=[str(CUSTOM_CONFIG)] + current_paths)

satpy.config.set(cache_dir=str(CACHE_DIR))
os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)

# 2. PROJECT LAYER
try:
    # IMPORTANTE: Descomentados para v0.0.2
    from .actions.a02_planning.a02_planning_cli import planning_group
    from .actions.a03_download.a03_download_cli import download_group 
except ImportError as e:
    print("\n" + "="*80)
    print(f" [PROJECT LIB ERROR] - In main.py")
    print(f" Failed to link Action Groups: {e}")
    print("="*80 + "\n")
    planning_group = None 
    download_group = None

# =============================================================================
# ROOT CLI GROUP
# =============================================================================

@click.group()
@click.version_option(version="0.1.9", prog_name="GOES Processor Tool")
def cli():
    """
    🛰️ GOES-PROCESSOR v.0.1.9: Legion Edition. (Tesis 2026)
    
    Integrated tool for:
    1. Planning (JSON inventory)
    2. Download (AWS S3)
    3. Processing (Satpy)
    """
    pass

# --- REGISTRATION ---

if planning_group:
    cli.add_command(planning_group, name="planning")

if download_group:
    cli.add_command(download_group, name="download")

if __name__ == "__main__":
    cli()
