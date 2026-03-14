"""
Path: legion_goes/tasks/task02_download/actions/fn_act01/step02_dict_parts/generate_dict03_dict_inventory.py
Version: 1.8.2
Description: Refactored with 'definition', 'tracking'. Syntax fixed and JSON-only Main.
"""
from datetime import datetime
import os
import json
from pathlib import Path  

# SOT Imports
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_sat import get_SOT_goes_info_sat
from legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder import get_SOT_specific_folder

# Internal imports
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
        selected_timestamp = filename.split('_s')[-1]
        selected_hour = selected_timestamp[7:9] if len(selected_timestamp) >= 9 else "00"
        
        # Path logic
        rel_folder = Path(str_SOT_bucket_name) / product_id / year / day / selected_hour
        abs_folder = (target_folder_raw / rel_folder).resolve()
      
        key = f"file{i:0{max_d}d}"
        
        inventory[key] = {
            # --- GROUP 1: DEFINITION (Static Metadata) ---
            "definition": {
                "SOT_metadata": {
                    "key": key,
                    "pos": f"{i:0{max_d}d}/{total:0{max_d}d}",
                    "timestamp": selected_timestamp,
                    "time_format": str_SOT_time_format,
                    "product_id": product_id,
                    "cadence": str_SOT_selected_cadence,
                    "year": year,
                    "day": day,
                    "hour": selected_hour
                },
                "s3_metadata": { 
                    "hard": {
                        "bucket": str_SOT_bucket_name,
                        "prefix_day": f"{product_id}/{year}/{day}",
                        "prefix_hour": f"{product_id}/{year}/{day}/{selected_hour}",
                        "init_name": filename
                    },
                    "soft": {
                        "file_name": None,
                        "file_exists_online": None,
                        "file_size_mb_online": None,
                    }
                },
                "local_file_info": {
                    "hard": { "init_name": filename },
                    "soft": {
                        "file_name": None,
                        "folder_path_relative": str(rel_folder),
                        "folder_path_absolute": str(abs_folder),
                        "file_exists_localy": None,
                        "file_size_mb_localy": None,
                    }
                }, # <-- Llave cerrada correctamente
                "local_folder_info": {
                    "hard": {
                        "root_folder": str(target_folder_raw),
                        "folder_path_relative": str(rel_folder),
                        "folder_path_absolute": str(abs_folder)
                    },
                    "soft": { "folder_exists": None }
                }
            },
            
            # --- GROUP 2: TRACKING (Dynamic Status) ---
            "tracking": {
                "is_done_file": False,
                "file_exists_localy": None,
                "file_exists_online": None,
                "is_size_ok": None,
                "error": None,
                "time_last_mod": {
                    "time_system": None,
                    "time_utc": None 
                }
            }
        }
        
    return inventory

# ===================================================================
# MAIN EXECUTION (Solo el Diccionario Completo)
# ===================================================================
if __name__ == "__main__":
    full_inventory = generate_dict(
        sat_id="19", 
        product_id="ABI-L2-LSTF", 
        year="2026", 
        day="003"
    )
    # Imprime el JSON completo para inspección
    print(json.dumps(full_inventory, indent=4))
