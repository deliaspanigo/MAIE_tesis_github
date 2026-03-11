"""
Path: legion_goes/tasks/task02_download/actions/fn_act01/step02_dict_parts/generate_dict03_dict_inventory.py
Version: 1.7.1
Description: Fixed undefined variables and string length call errors.
"""
from datetime import datetime
import os
import json
import itertools
from pathlib import Path  

# SOT Imports
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_sat import get_SOT_goes_info_sat
from legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder import get_SOT_specific_folder

# More internal imports
# Note: Renamed import to match your actual file name from 'ls'
from legion_goes.code.python_sp.f99_common.generate_list_expected_init_name import generate_list_expected_init_name
     

def generate_dict(sat_id: str, product_id: str, year: str, day: str) -> dict:
  
    # 1. Retrieve SoT info
    sat_SoT_info  = get_SOT_goes_info_sat(sat_id = sat_id)
    prod_SoT_info = get_SOT_goes_info_product(product_id = product_id)
  
    # 2. Get target base folder
    target_folder_raw = get_SOT_specific_folder(key="data_raw")
  
    # 3. Extract basic parameters
    str_SOT_bucket_name = sat_SoT_info['bucket']
    str_SOT_selected_cadence = prod_SoT_info["cadence_full_disk"]
    str_SOT_time_format = prod_SoT_info["time_format"] 
    
    # 4. Generate the list of expected prefixes
    list_expected_init_name = generate_list_expected_init_name(
        sat_id = sat_id, 
        product_id = product_id, 
        year = year, 
        day = day
    )
  
    inventory = {}
    total = len(list_expected_init_name)
    max_d = len(str(total))
  
    # 5. Build inventory dictionary
    for i, filename in enumerate(list_expected_init_name, 1):
        # Corrected string slicing and length check
        selected_timestamp = filename.split('_s')[-1]
        
        # FIX: Used len() instead of calling the string as a function
        selected_hour = selected_timestamp[7:9] if len(selected_timestamp) >= 9 else "00"
      
        # Path logic
        rel_folder = Path(str_SOT_bucket_name) / product_id / year / day / selected_hour
        abs_folder = (target_folder_raw / rel_folder).resolve()
      
        key = f"file{i:0{max_d}d}"
        inventory[key] = {
            "pos": f"{i:0{max_d}d}/{total:0{max_d}d}",
            "timestamp": selected_timestamp,
            "time_format": str_SOT_time_format,
            "cadence": str_SOT_selected_cadence,
            "year" : year,
            "day" : day,
            "hour": selected_hour, # FIX: Used correct variable name
            "status": {
                "is_ready": True,
                "exists_online": None,
                "exists_local": None,
                "is_done": None
            },
            "file_s3": {
                "bucket": str_SOT_bucket_name, # FIX: Used str_SOT_bucket_name
                "prefix_day": f"{product_id}/{year}/{day}",
                "prefix_hour": f"{product_id}/{year}/{day}/{selected_hour}",
                "init_name": filename,
                "file_name": None,
                "file_exists": None,
                "size_mb": None
            },
            "file_local": {
                "init_name": filename,
                "file_name": None,
                "path_relative": None,
                "path_absolute": None,
                "file_exists": None,
                 "size_mb": None
                 },
            "folder_local": {
                "super_root_folder": str(target_folder_raw),
                "path_relative": str(rel_folder),
                "path_absolute": str(abs_folder)
            }
        }
    return inventory

# ===================================================================
# MAIN EXECUTION
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GENERATE DOWNLOAD PLAN INVENTORY ".center(80, "="))
    
    # Test values
    T_SAT = "16"
    T_PROD = "ABI-L2-MCMIPF"
    T_YEAR = "2026"
    T_DAY = "070"

    try:
        inventory = generate_dict(T_SAT, T_PROD, T_YEAR, T_DAY)
        
        print(f"Satellite: GOES-{T_SAT}")
        print(f"Product:   {T_PROD}")
        print(f"Entries:   {len(inventory)}")
        
        if inventory:
            first_key = list(inventory.keys())[0]
            print(f"\nSample Entry ({first_key}):")
            print(f"  Hour: {inventory[first_key]['hour']}")
            print(f"  Path: {inventory[first_key]['folder_local']['path_absolute']}")

    except Exception as e:
        print(f"\n❌ Error generating inventory: {e}")
        # Helpful for debugging which line exactly failed
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80 + "\n")
