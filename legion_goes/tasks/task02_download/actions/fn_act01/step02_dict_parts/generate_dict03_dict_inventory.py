# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_act01/step02_dict_parts/generate_dict03_dict_inventory.py
# Version: 1.7.0 (Dual Path Logic: Plan vs Raw Data)
# =============================================================================
from datetime import datetime
import os
import json
import itertools
from pathlib import Path  # ← Added this import to fix NameError: Path is not defined

# SOT Imports
from legion_goes.sot.sat_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product
from legion_goes.sot.sat_hardcoded.access.get_SOT_goes_info_sat import get_SOT_goes_info_sat
from legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder import get_SOT_specific_folder

# More internal imports
from legion_goes.tasks.task02_download.actions.fn_act01.step01_product_init_name.generate_list_expected_init_names import generate_list_expected_product_init_name

def generate_dict(sat_id: str, product_id: str, year: str, day: str) -> dict:
  
    # Harcoded info for sat_id and product_id
    sat_SoT_info = get_SOT_goes_info_sat(sat_id = sat_id)
    prod_SoT_info = get_SOT_goes_info_product(product_id = product_id)
  
    # out_raw_base
    work_dir = Path(os.getcwd())
    sub_folder_war = get_SOT_specific_folder(key="data_raw")
    target_folder_raw = work_dir / sub_folder_war
  
  
    # Basics 01
    bucket_name = sat_SoT_info['bucket']
    selected_cadence = prod_SoT_info["cadence_full_disk"]
    position = sat_SoT_info['position'].upper()
    # Basics 02
    list_expected = generate_list_expected_product_init_name(sat_id = sat_id, product_id=product_id, year=year, day=day)
  
    # Basic03
    time_format = "YYYYDDDHHMMSS"
    inventory = {}
    total = len(list_expected)
    max_d = len(str(total))
  
  
    for i, filename in enumerate(list_expected, 1):
        t_id = filename.split('_s')[-1]
        str_hour = t_id[7:9] if len(t_id) >= 9 else "00"
      
        # KEY CHANGE: The inventory records paths pointing to the RAW folder
        rel_folder = Path(bucket_name) / product_id / year / day / str_hour
        abs_folder = (target_folder_raw / rel_folder).resolve()
      
        key = f"file{i:0{max_d}d}"
        inventory[key] = {
            "pos": f"{i:0{max_d}d}/{total:0{max_d}d}",
            "timestamp": t_id,
            "time_format": time_format[0:len(t_id)],
            "cadence": selected_cadence,
            "year" : year,
            "day" : day,
            "hour": str_hour,
            "status": {
                "is_ready": True,
                "exists_online": None,
                "exists_local": None,
                "is_done": None
            },
            "file_s3": {
                "bucket": bucket_name,
                "prefix_day": f"{product_id}/{year}/{day}",
                "prefix_hour": f"{product_id}/{year}/{day}/{str_hour}",
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
                "path_relative": str(rel_folder),
                "path_absolute": str(abs_folder) # Points to data_raw
            }
        }
    return inventory

# ===================================================================
# MAIN EXECUTION - Simple example in English
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GENERATE DOWNLOAD PLAN INVENTORY ".center(80, "="))
    print("Quick example of inventory generation...\n")

    # Typical values you use
    sat_id = "19"                  # GOES-19
    product_id = "ABI-L2-MCMIPF"   # Common product
    year = "2026"
    day = "100"                    # Day 100 of the year

    try:
        inventory = generate_dict(sat_id, product_id, year, day)
        
        print(f"Satellite: GOES-{sat_id}")
        print(f"Product: {product_id}")
        print(f"Date: {year}-{day}")
        print(f"Number of expected files: {len(inventory)}")
        print("\nFirst 3 files in inventory (example):")
        for key in list(inventory.keys())[:3]:
            item = inventory[key]
            print(f"   {key}:")
            print(f"     Timestamp: {item['timestamp']}")
            print(f"     Local folder path: {item['folder_local']['path_absolute']}")
            print(f"     Ready status: {item['status']['is_ready']}")
            print("     ---")
        print(f"\n... (total: {len(inventory)} entries)")
        print("\nDone.")
    
    except Exception as e:
        print(f"\n❌ Error generating inventory:")
        print(f"   {e}")

    print("=" * 80 + "\n")
