# =============================================================================
# FILE PATH: src/goes_processor/main.py
# Version: 0.1.8 (Master CLI Entry Point - Satpy & Cache Integrated)
# =============================================================================

MY_NAME = "main.py"

# 1. CAPA DE SISTEMA
try:
    import click
    import os
    import satpy
    from pathlib import Path
except ImportError as e:
    print(f"\n [SYSTEM LIB ERROR] - In {MY_NAME}: {e}\n")
    raise SystemExit(1)

# --- GLOBAL SATPY & CACHE CONFIGURATION ---
BASE_DIR = Path(__file__).parent.resolve()
CUSTOM_CONFIG = BASE_DIR / "satpy_config"
CACHE_DIR = BASE_DIR / "satpy_cache"

# Aseguramos que existan los directorios de configuración y caché
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Inyectamos la configuración de Satpy
current_paths = satpy.config.get("config_path", [])
if str(CUSTOM_CONFIG) not in current_paths:
    satpy.config.set(config_path=[str(CUSTOM_CONFIG)] + current_paths)

satpy.config.set(cache_dir=str(CACHE_DIR))
os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)

# 2. CAPA DE PROYECTO (Lazy Imports para evitar lentitud en el CLI)
try:
    # Importamos los grupos de comandos desde las acciones
    from .actions.a02_planning.a02_planning_cli import planning_group
    # from .actions.a03_download.a03_download_cli import download_group 
except ImportError as e:
    print("\n" + "="*80)
    print(f" [PROJECT LIB ERROR] - In {MY_NAME}")
    print(f" Failed to link Action Groups: {e}")
    print("="*80 + "\n")
    # No salimos aquí para permitir que Click muestre ayuda si es posible
    planning_group = None 

# =============================================================================
# ROOT CLI GROUP
# =============================================================================

@click.group()
@click.version_option(version="0.1.8", prog_name="GOES Processor Tool")
def cli():
    """
    🛰️ GOES-PROCESSOR v.0.1.8: Legion Edition.
    
    Herramienta integral para:
    1. Planificación (Planning JSON)
    2. Descarga (AWS S3)
    3. Procesamiento (Satpy / NetCDF)
    """
    pass

# --- REGISTRO DE GRUPOS DE COMANDOS ---

if planning_group:
    cli.add_command(planning_group, name="planning")

# Descomentar cuando a03_download esté listo
# if download_group:
#     cli.add_command(download_group, name="download")

# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    cli()
