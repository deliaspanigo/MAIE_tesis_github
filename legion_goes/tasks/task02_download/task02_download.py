# =============================================================================
# PATH: legion_goes/tasks/task02_download/task02_download.py
# Version: 1.2.0 (The Master Orchestrator - English Version)
# =============================================================================

import os
from pathlib import Path

# --- ACTION IMPORTS (Entry Points) ---
from legion_goes.tasks.task02_download.actions.action01_create_json_plan_download import run_action as run_act01_create
from legion_goes.tasks.task02_download.actions.action02_update_json_plan_download import run_action as run_act02_update
from legion_goes.tasks.task02_download.actions.action03_run_plan_download import run_action as run_act03_run_download

def run_task(
    sat_id: str, 
    product_id: str, 
    year: str, 
    day: str, 
    overwrite_json_plan: bool = False,
    threads: int = 4
):
    """
    Total Orchestrator for Task 02.
    Flow: Generation -> Audit/Sync -> Execution (S3 Download).
    """
    ctx = "[TASK-02 DOWNLOAD]"
    
    print("\n" + "═"*80)
    print(f" {ctx} STARTING PROCESS FOR SAT {sat_id} | DAY {day} ".center(80))
    print("═"*80)

    # 1. ACTION 01: Create/Verify Plan
    # Aquí se genera la estructura 'definition' y 'tracking' inicial.
    print(f"\n🚀 STEP 1: Creating/Verifying Download Plan...")
    success_01 = run_act01_create(
        sat_id=sat_id, 
        product_id=product_id, 
        year=year, 
        day=day, 
        overwrite_json_plan=overwrite_json_plan
    )
    if not success_01:
        print(f"❌ {ctx} Failed at Action 01 (Create Plan). Aborting.")
        return False

    # 2. ACTION 02: Audit/Sync Local Inventory
    # Aquí verificamos qué archivos ya tenemos físicamente en el disco.
    print(f"\n🚀 STEP 2: Syncing Local Inventory & Integrity...")
    success_02 = run_act02_update(
        sat_id=sat_id, 
        product_id=product_id, 
        year=year, 
        day=day
    )
    if not success_02:
        print(f"❌ {ctx} Failed at Action 02 (Update Plan). Aborting.")
        return False

    # 3. ACTION 03: Run S3 Download
    # Aquí es donde ocurre la descarga multihilo (ThreadPoolExecutor).
    # Ojo: la Action 03 ya hace un audit interno al final, así que el JSON quedará perfecto.
    print(f"\n🚀 STEP 3: Starting S3 Download Multithreading ({threads} threads)...")
    success_03 = run_act03_run_download(
        sat_id=sat_id, 
        product_id=product_id, 
        year=year, 
        day=day, 
        threads=threads
    )
    
    if not success_03:
        print(f"❌ {ctx} Failed at Action 03 (Download Run).")
        return False

    # --- FINAL MESSAGE ---
    print("\n" + "═"*80)
    print(f" ✨ {ctx} ALL ACTIONS COMPLETED SUCCESSFULLY ✨ ".center(80))
    print(f" Data stored in: .../{year}/{day}/ ".center(80))
    print("═"*80 + "\n")
    
    return True

# ===================================================================
# MAIN TEST (Integración Total)
# ===================================================================
if __name__ == "__main__":
    # Configuramos los parámetros de prueba
    test_params = {
        "sat_id": "19",
        "product_id": "ABI-L2-LSTF",
        "year": "2026",
        "day": "003",
        "overwrite_json_plan": False, # Lo ponemos en False para no borrar el plan si ya existe
        "threads": 8                  # Aprovechamos la potencia de tu equipo
    }

    # Lanzamos el proceso completo
    try:
        run_task(**test_params)
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user. JSON plans may be in-progress.")
    except Exception as e:
        print(f"\n❌ UNHANDLED ERROR in Orchestrator: {e}")
