# src/goes_processor/satpy_config/my_config_satpy.py
import satpy
from pathlib import Path
import os

# 1. Rutas basadas en tu estructura real (satpy_config)
BASE_DIR = Path(__file__).resolve().parent  
PROJ_DIR = BASE_DIR.parent                 

# Sincronizamos con el nombre de carpeta de tu tree: satpy_cache
CACHE_DIR = PROJ_DIR / "satpy_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 2. Configuración Global
# Usamos el método recomendado para añadir rutas sin romper las existentes
satpy.register_config_path(str(BASE_DIR))

satpy.config.set(
    cache_dir=str(CACHE_DIR),
    log_level="WARNING",
    default_resampler="kd_tree"
)

os.environ['PYRESAMPLE_CACHE_DIR'] = str(CACHE_DIR)

# Audit log para tu tesis
print(f"--- SatPy Configuration (v.0.3.1) ---")
print(f"✅ Cache: {CACHE_DIR}")
print(f"✅ Configs: {BASE_DIR}")
print(f"---------------------------------------")
