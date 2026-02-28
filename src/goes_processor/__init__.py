# =============================================================================
# FILE PATH: src/goes_processor/__init__.py
# Version: 0.1.8 (Root Package - Full SoT Integration)
# =============================================================================

# Identificador para reportes de error en la inicialización del paquete
MY_NAME = "goes_processor/__init__.py"

# Versión oficial del proyecto (Sincronizada con el desarrollo en Legion)
__version__ = "0.1.8"
__author__ = "Legion User"

# 1. CAPA DE SISTEMA
try:
    import sys
    from pathlib import Path
except ImportError as e:
    print(f"\n [SYSTEM ERROR] - Critical Python core failure in {MY_NAME}: {e}\n")
    raise SystemExit(1)

# 2. CAPA DE PROYECTO (Inicialización y Seguridad)
try:
    # Aquí es donde el paquete se asegura de que sus piezas básicas están presentes.
    # Por ahora, nos aseguramos de que SoT sea accesible.
    from .SoT.goes_hardcoded_folders import get_my_path
    
    # --- LOGGING INITIALIZATION (Reserved for future activation) ---
    # from .utils.logger import setup_legion_logger
    # setup_legion_logger()

except ImportError as e:
    print("\n" + "!"*80)
    print(f" [PROJECT INIT ERROR] - File: {MY_NAME}")
    print(f" Essential sub-module missing or broken: {e}")
    print(" Check if all __init__.py files exist in subfolders.")
    print("!"*80 + "\n")
    # No matamos el proceso con SystemExit para permitir tracebacks detallados
    # si esto es importado por main.py
    raise

def get_version():
    """Retorna la versión actual del procesador."""
    return f"GOES-Processor Tool v.{__version__}"
