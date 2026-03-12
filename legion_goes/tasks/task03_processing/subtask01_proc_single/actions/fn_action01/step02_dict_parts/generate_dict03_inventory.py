"""
FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action01/step02_dict_parts/generate_dict03_inventory.py
Version: 1.5.4
Description: Fixed indentation and variable mapping for inventory generation.
"""

import json
from pathlib import Path
from typing import Dict, Any

# --- LOCATORS AND GENERATORS ---
from legion_goes.tasks.task02_download.actions.fn_act01.generate_dict_plan_download import generate_dict_plan_download
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_executor.utils.get_dict_standard_output_info import get_dict_standard_output_info

def generate_dict(sat_id: str, product_id: str, year: str, day: str, fnp_tag: str = "fnp01") -> Dict[str, Any]:
    """
    CORE LOGIC: Builds the processing plan with specific output paths for each file.
    """
    # 1. Load Download Plan (Base inventory)
    dict_plan_download = generate_dict_plan_download(sat_id=sat_id, product_id=product_id, year=year, day=day) 
    download_inventory = dict_plan_download.get("inventory", {})
    
    dict_proc_single_inventory = {}

    # 2. Build Processing Inventory
    for i, (fid, info) in enumerate(download_inventory.items(), 1):
        init_name = info['file_s3']['init_name']
        timestamp = info['timestamp']  # Expected format: YYYYJJJHHMM
        s_timestamp_short = f"s{timestamp}"
        
        # 3. Get FNP Metadata & Paths for this specific timestamp
        # This calls your standardized utility we fixed earlier
        bag_fnp_info = get_dict_standard_output_info(
            sat_id=sat_id, 
            product_id=product_id, 
            year=int(year), 
            day=int(day), 
            s_timestamp_short=s_timestamp_short, 
            fnp_tag=fnp_tag
        )
        
        if not bag_fnp_info:
            continue # Skip if we can't resolve paths for this file

        new_fid = f"proc_single_{str(i).zfill(3)}"
        
        # 4. Extracting info from the resolved bag
        str_output_folder_path_abs = bag_fnp_info.get('str_output_folder_path_abs', '')
        dict_output_file_name = bag_fnp_info.get('dict_output_file_name', {})
        dict_output_file_path = bag_fnp_info.get('dict_output_file_path', {})
        
        # Check existence on the fly for the inventory status
        dict_output_file_exists = {k: Path(v).exists() for k, v in dict_output_file_path.items()}

        # 5. Build record
        dict_proc_single_inventory[new_fid] = {
            "pos_file": info.get('pos', i),
            "timestamp": timestamp,
            "status": {
                "is_ready_to_proc": info['status']['exists_local'], 
                "is_done": all(dict_output_file_exists.values()),
                "error": None
            },
            "input_ref": {
                "init_name": init_name,
                "file_name": info['file_local']['file_name'],
                "path_absolute": info['folder_local']['path_absolute'],
                "file_exists": info['status']['exists_local']
            },
            "output_ref": {
                "file_names": dict_output_file_name,
                "paths_absolute": dict_output_file_path,
                "files_exists": dict_output_file_exists,
                "output_folder": str_output_folder_path_abs
            }
        }

    return {
        "proc_single_inventory": dict_proc_single_inventory,
        "metadata": {
            "sat_id": sat_id,
            "product_id": product_id,
            "fnp_tag": fnp_tag,
            "total_files": len(dict_proc_single_inventory)
        }
    }

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: GENERATE SINGLE PROCESS PLAN ".center(70, "="))
    
    T_PARAMS = {
        "sat_id": "16",
        "product_id": "ABI-L2-MCMIPF",
        "year": "2026",
        "day": "070",
        "fnp_tag": "fnp01"
    }

    try:
        # Note: calling generate_dict as defined above
        result_plan = generate_dict(**T_PARAMS)
        inventory = result_plan.get("proc_single_inventory", {})
        
        if inventory:
            print(f"✅ Success! Generated plan for {len(inventory)} files.")
            first_key = list(inventory.keys())[0]
            sample = inventory[first_key]
            
            print(f"\nSample Entry: {first_key}")
            print(f"  Timestamp:     {sample['timestamp']}")
            print(f"  Input Ready:   {sample['status']['is_ready_to_proc']}")
            print(f"  Output Folder: {sample['output_ref']['output_folder']}")
        else:
            print("⚠️ [WARNING] Inventory is empty.")

    except Exception as e:
        print(f"❌ [CRITICAL ERROR]: {e}")
        import traceback
        traceback.print_exc()
