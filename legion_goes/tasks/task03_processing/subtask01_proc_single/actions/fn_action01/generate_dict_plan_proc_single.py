"""
FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action01/generate_dict_plan_proc_single.py
Version: 1.0.2
Description: Main orchestrator using LONG ABSOLUTE PATHS for all internal 
             library imports to ensure project-wide compatibility.
"""

import json
from pathlib import Path

# --- LONG PATH IMPORTS (Absolute Project Paths) ---
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict01_self_info
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict02_sat_prod_info
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict03_inventory
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.fn_action01.step02_dict_parts import generate_dict04_summary

def generate_dict_plan_proc_single(
    sat_id: str, 
    product_id: str, 
    year: str, 
    day: str, 
    fnp_tag: str = "fnp01",
    save_json: bool = True
) -> dict:
    """
    Assembles the 4 dictionary parts using absolute path imports 
    and saves the result to an absolute disk location.
    """
    
    # 1. Metadata & Absolute Path for the Plan (v.0.0.1)
    dict01 = generate_dict01_self_info.generate_dict(
        sat_id=sat_id, product_id=product_id, year=year, day=day, fnp_tag=fnp_tag
    )
    
    # 2. Technical Satellite/Product Info (SOT)
    dict02 = generate_dict02_sat_prod_info.generate_dict(
        sat_id=sat_id, product_id=product_id, year=year, day=day
    )
    
    # 3. Processing Inventory (Input & Output Absolute Paths)
    dict03_full = generate_dict03_inventory.generate_dict(
        sat_id=sat_id, product_id=product_id, year=year, day=day, fnp_tag=fnp_tag
    )
    inventory = dict03_full.get("proc_single_inventory", {})
    
    # 4. Progress Summary (Root Absolute Directory)
    dict04 = generate_dict04_summary.generate_dict(dict_proc_inventory=inventory)
    
    # --- FINAL ASSEMBLY ---
    plan_dict = {
        "self_info": dict01,
        "sat_prod_info": dict02,
        "summary": dict04,
        "proc_single_inventory": inventory
    }

    # --- SAVE TO DISK ---
    if save_json:
        abs_file_path = Path(dict01["path_absolute"])
        
        # Ensure parent directories exist (Absolute Path)
        abs_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(abs_file_path, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=4, ensure_ascii=False)
            
        print(f"💾 [SAVED] Absolute Plan: {abs_file_path}")
    
    return plan_dict

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " LEGION-GOES: ABSOLUTE PATHS & LONG IMPORTS ".center(80, "="))
    
    T_PARAMS = {
        "sat_id": "16",
        "product_id": "ABI-L2-MCMIPF",
        "year": "2026",
        "day": "070",
        "fnp_tag": "fnp01"
    }

    try:
        full_plan = generate_dict_plan_proc_single(**T_PARAMS, save_json=True)
        print(f"✅ Success: Plan generated for {T_PARAMS['product_id']}")
        
    except Exception as e:
        print(f"❌ [CRITICAL ERROR]: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 80 + "\n")
