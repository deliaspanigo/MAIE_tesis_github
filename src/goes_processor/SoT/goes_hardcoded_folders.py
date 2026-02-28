# =============================================================================
# FILE PATH: src/goes_processor/SoT/goes_hardcoded_folders.py
# Version: 0.1.8 (Path Anchor & Environment Guard)
# =============================================================================

try:
    from pathlib import Path
    from types import MappingProxyType
except ImportError as e:
    print("\n" + "="*80)
    print(f" [CRITICAL ERROR] - [SoT - goes_hardcoded_folders.py]")
    print("="*80)
    print(f" Failed to load base libraries: {e}")
    print(" Please verify that your virtual environment (venv) is active.")
    print(" Ensure that 'pathlib' and 'types' are available.")
    print("="*80 + "\n")
    raise SystemExit(1)

# ===================================================================
# PROJECT ROOT DETECTION
# ===================================================================
# Estructura esperada: MAIE_tesis_github/src/goes_processor/SoT/
# Subimos 4 niveles para llegar a la raíz del repositorio.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# ===================================================================
# PRIVATE SOURCE OF TRUTH (Fixed Paths)
# ===================================================================
_FOLDERS = {
    "root": BASE_DIR,
    "data_raw": BASE_DIR / "data_raw",
    "data_plan": BASE_DIR / "data_plan",
    
    # Procesamiento (Estructura data_processed)
    "proc_core01": BASE_DIR / "data_processed" / "a02_processing" / "core01_proc_one_file",
    "proc_core02": BASE_DIR / "data_processed" / "a02_processing" / "core02_proc_accumulate",
    
    # Soporte y Cache
    "reports": BASE_DIR / "src" / "goes_processor" / "reports",
    "satpy_cache": BASE_DIR / "src" / "goes_processor" / "satpy_cache",
}

# Interfaz pública de solo lectura
GOES_FOLDERS = MappingProxyType(_FOLDERS)

# ===================================================================
# PUBLIC INTERFACE
# ===================================================================

def get_my_path(key: str) -> Path:
    """
    Returns the absolute path from GOES_FOLDERS, 
    creates it if it doesn't exist, and returns the Path object.
    """
    ctx = "[SoT - goes_hardcoded_folders.py - get_my_path()]"
    
    try:
        path = GOES_FOLDERS.get(key)
        
        if not path:
            valid_keys = list(GOES_FOLDERS.keys())
            raise KeyError(f"The key '{key}' is not defined. Valid keys: {valid_keys}")
        
        # Crear la carpeta automáticamente (y sus padres si no existen)
        path.mkdir(parents=True, exist_ok=True)
        
        return path

    except (KeyError, Exception) as e:
        # Mantenemos el estándar de error en cascada de la v.0.1.8
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None

# ===================================================================
# INTEGRITY TEST
# ===================================================================
if __name__ == "__main__":
    print(f"\n" + "="*50)
    print(f" GOES FOLDER SYSTEM v.0.1.8")
    print(f" Root Detected: {BASE_DIR}")
    print(f"="*50)
    
    try:
        p = get_my_path("data_raw")
        print(f" [+] Success: Path is ready at {p}")
    except Exception as e:
        print(f" [-] Fail: {e}")
