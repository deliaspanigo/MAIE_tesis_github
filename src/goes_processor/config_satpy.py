# src/goes19_processor/config_satpy.py
"""
Archivo centralizado para configuraciones globales de Satpy.
Se importa una sola vez en main.py para aplicar a todo el proyecto.
"""

import satpy
from pathlib import Path
import os

# 1. Definir rutas ABSOLUTAS para evitar errores en el CLI
# Buscamos la carpeta satpy_configs que está al lado de este archivo
BASE_DIR = Path(__file__).resolve().parent
custom_config_dir = BASE_DIR / "satpy_configs"

# Carpeta de cache para remuestreos (en la raíz del proyecto)
CACHE_DIR = Path(os.getenv("SATPY_CACHE_DIR", BASE_DIR.parent.parent / "resample_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 2. Configuración global de Satpy
satpy.config.set(
    cache_dir=str(CACHE_DIR),
    log_level="WARNING",
    default_resampler="kd_tree",
    # REGISTRO CRÍTICO: Pasamos la carpeta raíz de nuestras configuraciones
    # Satpy buscará automáticamente dentro de /composites y /enhancements
    config_path=[str(custom_config_dir)] 
)

# 3. Verificación mejorada para el log de consola
# Nota: Satpy espera que los archivos se llamen como el sensor (abi.yaml)
expected_files = [
    custom_config_dir / "composites" / "abi.yaml",
    custom_config_dir / "enhancements" / "abi.yaml", # O abi_enhancements.yaml según tu carpeta
]

print(f"--- Configuración SatPy (v.0.0.1) ---")
if custom_config_dir.exists():
    print(f"✅ Carpeta de configuración detectada: {custom_config_dir}")
    # Listamos lo que realmente hay para debug
    found_any = False
    for subfolder in ["composites", "enhancements"]:
        folder_path = custom_config_dir / subfolder
        if folder_path.exists():
            files = list(folder_path.glob("*.yaml"))
            for f in files:
                print(f"  - [{subfolder}] {f.name}: Encontrado")
                found_any = True
    if not found_any:
        print("  ⚠️ Advertencia: No se encontraron archivos .yaml en las subcarpetas.")
else:
    print(f"❌ ERROR: No se encontró la carpeta de configuración en: {custom_config_dir}")

print(f"  - Cache: {CACHE_DIR}")
print(f"  - Log: {satpy.config.get('log_level')}")
print(f"---------------------------------------")
