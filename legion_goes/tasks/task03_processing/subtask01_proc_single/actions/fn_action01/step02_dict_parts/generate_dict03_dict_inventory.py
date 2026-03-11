"""
Path: legion_goes/tasks/task02_download/actions/fn_act01/step02_dict_parts/get_dict_plan_proc_single.py
Version: 1.5.3
Description: Generates the processing plan inventory. 
             Links download results to the processing folder structure: HH -> sTimestamp -> fnp_tag.
"""

import json
from datetime import datetime
from pathlib import Path

# --- LOCATORS AND GENERATORS ---
from legion_goes.tasks.task02_download.actions.fn_utils.generate_plan_download_file_path import generate_plan_download_file_path
from legion_goes.tasks.task02_download.actions.fn_act01.generate_dict_plan_download import generate_dict_plan_download

# --- EXECUTOR UTILS ---
from legion_goes.code.python_sp.sp001_single.f02_executor.utils.get_folder_full_path_proc_single import get_folder_full_path_proc_single
from legion_goes.code.python_sp.sp001_single.f02_executor.steps.STEP02_get_elements_from_fnp import STEP02_get_elements_from_fnp

def get_dict_plan_proc_single(sat_id: str, product_id: str, year: str, day: str, fnp_tag: str = "fnp01"):
    """
    CORE LOGIC: Builds the processing plan with specific output paths for each file.
    """
    # 1. Load Download Plan (Base inventory)
    dict_plan_download = generate_dict_plan_download(sat_id=sat_id, product_id=product_id, year=year, day=day) 
    download_inventory = dict_plan_download.get("inventory", {})
    
    # 2. Get FNP Metadata (Schema)
    bag_fnp = STEP02_get_elements_from_fnp(
        product_id=product_id, 
        fnp_tag=fnp_tag, 
        list_expected=['dict_output_schema']
    )
    dict_output_schema = bag_fnp.get('dict_output_schema', {})
    
    proc_single_inventory = {}

    # 3. Build Processing Inventory
    for i, (fid, info) in enumerate(download_inventory.items(), 1):
        init_name = info['file_s3']['init_name']
        timestamp = info['timestamp']  # Expected format: YYYYJJJHHMM
        s_time_short = f"s{timestamp}"
        hour_folder = info['hour']     # Extracted from download inventory
        
        new_fid = f"proc_single_{str(i).zfill(3)}"
        
        # Get absolute processing folder path
        folder_full_path = get_folder_full_path_proc_single(
            sat_id=sat_id, 
            product_id=product_id, 
            year=year, 
            day=day, 
            hour=hour_folder, 
            s_time_short=s_time_short, 
            fnp_tag=fnp_tag
        )
        output_folder_path = Path(folder_full_path)
        
        # 4. Map specific output files
        file_names = {}
        paths_absolute = {}
        files_exists = {}

        for out_key, out_filename in dict_output_schema.items():
            final_path_abs = output_folder_path / out_filename
            
            file_names[out_key] = out_filename
            paths_absolute[out_key] = str(final_path_abs.resolve())
            files_exists[out_key] = final_path_abs.exists()

        # 5. Build record
        proc_single_inventory[new_fid] = {
            "pos_file": info['pos'],
            "timestamp": timestamp,
            "status": {
                "is_ready_to_proc": info['status']['exists_local'], 
                "is_done": False,
                "error": None
            },
            "input_ref": {
                "init_name": init_name,
                "file_name": info['file_local']['file_name'],
                "path_absolute": info['folder_local']['path_absolute'],
                "file_exists": info['status']['exists_local']
            },
            "output_ref": {
                "file_names": file_names,
                "paths_absolute": paths_absolute,
                "files_exists": files_exists,
                "output_folder": str(output_folder_path.resolve())
            }
        }

    return {
        "plan_proc_single_self_info": {
            "fnp_tag": fnp_tag,
            "timestamp_creation": datetime.now().isoformat(),
            "total_files": len(proc_single_inventory)
        },
        "sat_prod_info": {
            "sat_id": sat_id,
            "product_id": product_id,
            "year": year,
            "day": day
        },
        "proc_single_inventory": proc_single_inventory
    }

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: GENERATE SINGLE PROCESS PLAN ".center(70, "="))
    
    # Test Parameters
    T_SAT = "16"
    T_PROD = "ABI-L2-MCMIPF"
    T_YEAR = "2026"
    T_DAY = "070"
    T_FNP = "fnp01"

    print(f"Target: GOES-{T_SAT} | {T_PROD} | Day: {T_YEAR}-{T_DAY} | Tag: {T_FNP}")
    print("-" * 70)

    try:
        # Generate the dictionary
        result_plan = get_dict_plan_proc_single(
            sat_id=T_SAT, 
            product_id=T_PROD, 
            year=T_YEAR, 
            day=T_DAY, 
            fnp_tag=T_FNP
        )

        inventory = result_plan.get("proc_single_inventory", {})
        
        if inventory:
            print(f"✅ Success! Generated plan for {len(inventory)} files.")
            
            # Show the first entry as a sample
            first_key = list(inventory.keys())[0]
            sample = inventory[first_key]
            
            print(f"\nSample Entry: {first_key}")
            print(f"  Timestamp:     {sample['timestamp']}")
            print(f"  Input Ready:   {sample['status']['is_ready_to_proc']}")
            print(f"  Output Folder: {sample['output_ref']['output_folder']}")
            print(f"  Output Files:  {list(sample['output_ref']['file_names'].values())}")
        else:
            print("⚠️ [WARNING] Plan generated but inventory is empty.")

    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Failed to generate plan: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 70 + "\n")
