# src/goes_processor/config_satpy.py
"""
Archivo centralizado para configuraciones globales de Satpy.
v.0.0.1 - Configuración de Caché centralizada en /data
"""

import satpy
from pathlib import Path
import os

# 1. Definir rutas ABSOLUTAS
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent

# Definición única de la ruta de caché
CACHE_DIR = ROOT_DIR / "data" / "cache_resampling"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Carpeta de configuraciones YAML
custom_config_dir = BASE_DIR / "satpy_configs"

# 2. Configuración global de Satpy
# Forzamos el uso de str(CACHE_DIR) para evitar conflictos de tipos
satpy.config.set(
    cache_dir=str(CACHE_DIR),
    log_level="WARNING",
    default_resampler="kd_tree", # El mejor para aprovechar el caché
    config_path=[str(custom_config_dir)] 
)

# 3. FORZAR VARIABLE DE ENTORNO PARA PYRESAMPLE
# Vital para que el motor de remuestreo escriba los archivos .nc en la carpeta correcta
os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)

# 4. Verificación de inicio
print(f"--- Configuración SatPy (v.0.0.1) ---")
print(f"✅ Cache vinculado a: {CACHE_DIR}")
print(f"  - Resampler: {satpy.config.get('default_resampler')}")
print(f"---------------------------------------")
