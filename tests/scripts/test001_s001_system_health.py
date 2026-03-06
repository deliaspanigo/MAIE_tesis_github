# =============================================================================
# FILE PATH: tests/scripts/test001_s001_system_health.py
# Description: Unit test for system integrity, paths, and environment.
# =============================================================================

import os
import sys
from pathlib import Path

# --- FIX PATHS ---
# Esto permite que el test vea la carpeta 'src' aunque se ejecute desde fuera
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT / "src"))

try:
    from legion_goes.SoT.goes_hardcoded_folders import LEGION_DATA_ROOT, GOES_FOLDERS
    from legion_goes.tasks.task01_init.actions.action01_welcome import C_LGN, C_GOS, C_RST, C_BLD
except ImportError as e:
    print(f"[ERROR] Could not import legion_goes. Is the 'src' folder in the right place?\n{e}")
    sys.exit(1)

def run_health_check():
    """Verifica la salud básica del entorno de la tesis."""
    print(f"\n{C_BLD}{'='*60}{C_RST}")
    print(f"{C_LGN}LEGION-GOES SYSTEM HEALTH CHECK{C_RST}")
    print(f"{C_BLD}{'='*60}{C_RST}\n")

    # 1. Verificar Root de Datos
    print(f"[STEP 1] Checking DATA_ROOT...")
    if os.path.exists(LEGION_DATA_ROOT):
        print(f"  {C_GOS}OK:{C_RST} Root exists at {LEGION_DATA_ROOT}")
    else:
        print(f"  {C_LGN}WARNING:{C_RST} Root not found. Run 'LEGION-GOES run' first.")

    # 2. Verificar Carpetas del SoT
    print(f"\n[STEP 2] Verifying SoT Folder Consistency...")
    missing_count = 0
    for key, folder in GOES_FOLDERS.items():
        # Aquí puedes meter tu lógica de exclusión si es necesario
        full_path = os.path.join(LEGION_DATA_ROOT, folder)
        if os.path.exists(full_path):
            print(f"  + {key.ljust(15)} -> {C_GOS}[FOUND]{C_RST}")
        else:
            print(f"  + {key.ljust(15)} -> {C_LGN}[MISSING]{C_RST}")
            missing_count += 1

    # 3. Reporte Final
    print(f"\n{C_BLD}{'='*60}{C_RST}")
    if missing_count == 0:
        print(f"{C_GOS}RESULT: SYSTEM HEALTHY{C_RST}")
    else:
        print(f"{C_LGN}RESULT: INCOMPLETE ENVIRONMENT ({missing_count} folders missing){C_RST}")
    print(f"{C_BLD}{'='*60}{C_RST}\n")

if __name__ == "__main__":
    run_health_check()
