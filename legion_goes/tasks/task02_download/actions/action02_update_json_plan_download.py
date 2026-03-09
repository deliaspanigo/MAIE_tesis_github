# =============================================================================
# PATH: src/legion_goes/tasks/task02_download/actions/action02_update_json_plan_download.py
# Version: 1.8.0 (Fix: Variable Scope & Integrity Check)
# =============================================================================

import os
from pathlib import Path
from datetime import datetime

# --- UTILS & ACTS ---
from legion_goes.tasks.task02_download.actions.fn_utils.load_dict_plan_file_json import load_dict_plan_file_json
from legion_goes.tasks.task02_download.actions.fn_utils.save_dict_plan_json import save_dict_plan_json
from legion_goes.tasks.task02_download.actions.fn_utils.generate_plan_download_file_path import generate_plan_download_file_path
from legion_goes.tasks.task02_download.actions.fn_act02.update_dict_plan_download import update_dict_plan_download

def run_action(
    sat_id: str, 
    product_id: str, 
    year: str, 
    day: str
):
    """
    Main entry point to check local integrity.
    Locates the JSON in the CONTROL folder, scans physical disk, 
    and updates 'is_done' status accordingly.
    """
    ctx = "[Action02 - Update Download Plan json]"
    
    try:
        # 1. Resolve JSON file path
        json_file_path = generate_plan_download_file_path(sat_id=sat_id, product_id=product_id, year=year, day=day)
        file_exists = json_file_path.exists()
        
        print(f"\n{'='*80}")
        print(f"🚀 {ctx}".center(80))
        print(f"{'='*80}")
        print(f"📂 INFO: [Satellite: G{sat_id}] | [Product: {product_id}] | [Date: {year}-{day}]")
        print(f"📂 TARGET PATH: {json_file_path}")
        print(f"📂 DETAILS: [file_exists: {file_exists}]")
        print(f"{'-'*80}")

        if not file_exists:
            print(f"❌ [ERROR]: Plan file not found. Run Action 01 first.")
            return False
    
        # 2. Load existing plan
        dict_plan_download_local = load_dict_plan_file_json(path_json = str(json_file_path))
        
        # 3. Update plan with current local inventory/status (Physical Audit)
        print(f"🔄 Starting physical disk audit...")
        dict_plan_download_local_mod = update_dict_plan_download(dict_plan = dict_plan_download_local)
        print(f"✨ Physical audit finished.")
        
        # 4. Save updated plan
        print(f"💾 Saving updated JSON plan...")
        save_dict_plan_json(dict_plan = dict_plan_download_local_mod, path_json = str(json_file_path))
        print(f"✅ [SUCCESS]: Plan synced with local storage.")
        
        # --- UI SUMMARY ---
        print("\n" + "=" * 80)
        print(f" RESULT: ✅ SUCCESS ".center(80))
        print("=" * 80 + "\n")
        
        return True

    except Exception as e:
        print(f"❌ [ERROR in {ctx}]: {e}")
        return False

# ===================================================================
# MAIN EXECUTION (Unit Test)
# ===================================================================
if __name__ == "__main__":
    test_sat_id = "19"
    test_product_id = "ABI-L2-MCMIPF"
    test_year = "2026"
    test_day = "003"

    # Execution
    run_action(
        sat_id=test_sat_id,
        product_id=test_product_id,
        year=test_year,
        day=test_day
    )
