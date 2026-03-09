# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_act01/step02_dict_parts/generate_dict04_summary.py
# Version: 1.7.0 (Dual Path Logic: Plan vs Raw Data)
# =============================================================================
import os
from pathlib import Path
from datetime import datetime

def generate_dict(dict_inventory: dict) -> dict:
    """
    Generates a summary dictionary from the inventory.
    """
    total_files = len(dict_inventory)
    
    if not dict_inventory:
        raise ValueError("Inventory is empty")
    
    # Toma la PRIMERA clave que exista (no asume que es 1)
    first_key = next(iter(dict_inventory))  # Primera clave disponible
    the_first = dict_inventory[first_key]
    
    # Convert strings to Path objects
    rel_path = Path(the_first["folder_local"]["path_relative"])
    abs_path = Path(the_first["folder_local"]["path_absolute"])
    
    # Parent folders (remove last subfolder)
    folder_path_hour_rel = rel_path.parent
    folder_path_hour_abs = abs_path.parent
    
    # Current timestamp
    time_now = datetime.now()
    time_now_format = time_now.strftime("%Y-%m-%d %H:%M:%S")
    
    the_dict = {
        "is_done": False,
        "expected_total_files": total_files,
        "local_total_files": None,
        "output_folder_year_day_relative": str(folder_path_hour_rel),
        "output_folder_year_day_absolute": str(folder_path_hour_abs),
        "summary_timestamp": time_now_format,
        "total_files_processed": None,
        "progress_percentage": None
    }
    return the_dict

# ===================================================================
# MAIN EXECUTION - Simple example
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GENERATE SUMMARY DICT04 EXAMPLE ".center(80, "="))
    print("Quick test of generate_dict04_summary...\n")

    # Minimal fake inventory to test (only 1 entry needed)
    example_inventory = {
        1: {
            "folder_local": {
                "path_relative": "noaa-goes19/ABI-L2-MCMIPF/2026/100/000000",
                "path_absolute": "/home/user/data_raw/noaa-goes19/ABI-L2-MCMIPF/2026/100/000000"
            }
            # ... other fields not needed for this test
        }
    }

    try:
        summary_dict = generate_dict(example_inventory)
        
        print("Input inventory (first entry):")
        print(f"   Relative path: {example_inventory[1]['folder_local']['path_relative']}")
        print(f"   Absolute path: {example_inventory[1]['folder_local']['path_absolute']}")
        
        print("\nGenerated summary dict:")
        for key, value in summary_dict.items():
            print(f"   {key}: {value}")
        
        print("\nDone.")
    
    except Exception as e:
        print(f"\n❌ Error generating summary dict:")
        print(f"   {e}")

    print("=" * 80 + "\n")
