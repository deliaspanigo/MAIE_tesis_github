# =============================================================================
# Path: legion_goes/code/python_sp/f02_processing/sp001_single/f02_auto_processing/fn01_run_collector/run_collector.py
# Version: 1.0.2
# Description: Central Collector that assembles the multi-pack execution plan.
# =============================================================================

import os
import sys
from typing import Dict, List, Any, Optional

# --- IMPORTACIÓN DE LOS RECOLECTORES ---
# Importamos las funciones desde sus respectivos archivos (Packs)
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_auto_processing.fn01_run_collector.pack01_elements_standard_proc import pack01_standard_proc
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_auto_processing.fn01_run_collector.pack02_strip_gallery_png import pack02_strip_gallery_png
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_auto_processing.fn01_run_collector.pack03_metadata import pack03_metadata

def run_collector(
    sat_id: str,
    product_id: str,
    year: int,
    day: int,
    s_timestamp_short: str,
    fnp_tag: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Orchestrates the collection of all processing steps (Packs).
    Returns a list of 'Bags', where each bag is a standalone task ready for the Executor.
    """
    
    execution_plan = []
    
    # Parámetros que todos los packs necesitan para resolver sus rutas
    common_params = {
        "sat_id": sat_id,
        "product_id": product_id,
        "year": year,
        "day": day,
        "s_timestamp_short": s_timestamp_short,
        "fnp_tag": fnp_tag
    }

    print(f"\n" + "-"*60)
    print(f"📦 [COLLECTOR] Building plan: {product_id} | {s_timestamp_short}")
    print("-"*60)

    # --- STEP 1: Pack 01 - Science Processing ---
    # Recolecta la función FNP y las rutas de salida de archivos .png, .nc, etc.
    bag01 = pack01_standard_proc(**common_params)
    if bag01:
        execution_plan.append(bag01)
        print(f"  ✅ Step 1/3: Pack01 (Science) collected.")
    else:
        print(f"  ❌ Step 1/3: Pack01 failed. Process halted.")
        return None

    # --- STEP 2: Pack 02 - Gallery Strip ---
    # Recolecta la función para crear el strip horizontal de previsualización.
    bag02 = pack02_strip_gallery_png(**common_params)
    if bag02:
        execution_plan.append(bag02)
        print(f"  ✅ Step 2/3: Pack02 (Gallery) collected.")
    else:
        print(f"  ⚠️  Step 2/3: Pack02 skipped (check individual pack logs).")

    # --- STEP 3: Pack 03 - Metadata & Audit ---
    # Recolecta la función para crear el meta.json final.
    bag03 = pack03_metadata(**common_params)
    if bag03:
        execution_plan.append(bag03)
        print(f"  ✅ Step 3/3: Pack03 (Metadata) collected.")
    else:
        print(f"  ⚠️  Step 3/3: Pack03 skipped (check individual pack logs).")

    print(f"\n🚀 Collector finished. Total steps in plan: {len(execution_plan)}")
    print("-"*60 + "\n")
    
    return execution_plan

# =============================================================================
# DIAGNOSTIC TEST
# =============================================================================
if __name__ == "__main__":
    # Test con parámetros de ejemplo
    test_params = {
        "sat_id": "19",
        "product_id": "ABI-L2-MCMIPF",
        "year": 2026,
        "day": 3,
        "s_timestamp_short": "s20260031245",
        "fnp_tag": "fnp01"
    }
    
    plan = run_collector(**test_params)
    
    if plan:
        print("PLAN SUMMARY:")
        for i, step in enumerate(plan, 1):
            print(f"  [{i}] {step['meta']['task_name']}")
