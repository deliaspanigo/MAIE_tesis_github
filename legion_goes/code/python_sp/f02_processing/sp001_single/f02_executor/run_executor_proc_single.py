"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/run_executor_proc_single.py
Version: 0.0.1
Description: Main orchestrator for single product processing. 
             Connects isolated steps and measures execution time.
"""

import time
from pathlib import Path

# --- IMPORTING ISOLATED STEPS ---
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_executor.steps.STEP03_run_fnp import STEP03_run_fnp

# --- UTILITY IMPORTS ---
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_executor.utils.check_all_path_exists_from_dict import check_all_path_exists_from_dict
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_executor.utils.get_elements_from_FNP import get_elements_from_FNP
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_executor.utils.get_dict_standard_output_info import get_dict_standard_output_info
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_executor.utils.get_str_s_timestamp_short_from_nc import get_str_s_timestamp_short_from_nc 


    
def run_executor_proc_single(sat_id="16", product_id="ABI-L2-MCMIPF", year=None, day=None, fnp_tag="fnp01", overwrite=False, nc_path=None):
    """
    Orchestrates the processing of a single NetCDF file through three steps:
    1. Path resolution & validation.
    2. Dynamic logic loading.
    3. Execution and post-processing.
    """
    # Start global performance timing
    global_start_time = time.time()
    print("-" * 80)

    # 0. Initial Input Validation
    if not nc_path:
        print("❌ [ERROR] No nc_path provided.")
        return False
        
    input_file = Path(nc_path).resolve()
    if not input_file.exists():
        print(f"❌ [ERROR] NC file not found: {input_file}")
        return False
    
    
    s_timestamp_short = get_str_s_timestamp_short_from_nc(product_id= product_id, input_nc= nc_path)
    
    # 01. dict Standard output info proc single
    dict_standard_output_info = get_dict_standard_output_info(sat_id=sat_id, product_id=product_id, year=year, day=day, s_timestamp_short = s_timestamp_short, fnp_tag=fnp_tag)
    
    # --- STEP 01: OUTPUT CONFIGURATION (Returns String) ---
    str_output_folder_path_abs = dict_standard_output_info["str_output_folder_path_abs"]
    if not str_output_folder_path_abs: 
        return False
    
    # --- STEP 02: DYNAMIC IMPORT (Returns BAG/Dict) ---
    # We expect 'dict_output_schema' and 'fnp_python_code' (the core function)
    bag_fnp = dict_standard_output_info["bag_fnp"]
    if not bag_fnp or not bag_fnp.get('fnp_python_code'): 
        return False

    # --- STEP 2.5: OUTPUT PATH MAPPING ---
    # Convert schema relative names to full absolute paths based on STEP01 result
    dict_output_file_path = dict_standard_output_info["dict_output_file_path"]

    # --- SKIP LOGIC: Check if work is already done ---
    if check_all_path_exists_from_dict(dict_output_file_path) and not overwrite:
        print(f"✨ [SKIP] Outputs already exist in: {Path(ostr_output_folder_path_abs).name}")
        return True

    # --- STEP 03: EXECUTION & POST-PROCESSING (Returns Bool) ---
    print(f"🚀 [START] Processing {product_id} | {fnp_tag}")
    success = STEP03_run_fnp(
        fnp_func=bag_fnp['fnp_python_code'], 
        input_nc=input_file, 
        dict_outputs=dict_output_file_path, 
        overwrite=overwrite
    )

    # --- FINAL REPORTING ---
    if success:
        total_time = round(time.time() - global_start_time, 2)
        print(f"✅ Finished {product_id} successfully in {total_time}s.")
    else:
        print(f"❌ Execution failed for {product_id}.")
    
    print("-" * 80)
    return success

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " LEGION-GOES EXECUTOR V.0.0.1 ".center(80, "="))
    
    # Auto-find first .nc file in current directory for a quick test
    nc_test = next(Path(".").glob("*.nc"), None)
    
    if nc_test:
        run_executor_proc_single(
            nc_path=nc_test, 
            sat_id="16", 
            product_id="ABI-L2-MCMIPF", 
            year=2026, 
            day=70, 
            fnp_tag="fnp01", 
            overwrite=True
        )
    else:
        print("💡 [INFO] No .nc files found in the current folder to run diagnostic.")
