# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_act01/step02_dict_parts/generate_dict01_self_info.py
# Version: 1.7.0 (Dual Path Logic: Plan vs Raw Data)
# =============================================================================
from legion_goes.code.python_sp.f01_donwload.utils.generate_plan_download_json_file_path import generate_plan_download_json_file_path

from datetime import datetime
from pathlib import Path
import os 
########################################################################################
def generate_dict(sat_id: str, product_id: str,  year: str, day: str) -> dict:
    """Generates metadata about the Download Plan file itself."""
    time_now = datetime.now()
    time_now_format = time_now.strftime("%Y-%m-%d %H:%M:%S")
  
    file_path = generate_plan_download_json_file_path(
        sat_id=sat_id,
        product_id=product_id,
        year=year,
        day=day
    )
    
    file_obj = Path(file_path)

    
    return {
        "description": "Download Plan for 1 day, for 1 specific product.",
        "task": "Download",
        "product_id": product_id,
        "file_name": str(file_obj.name),            # Filename as string
        "path_absolute": str(file_obj.resolve()),    # Absolute path as string
        "creation_time": time_now_format
    }

# ===================================================================
# MAIN EXECUTION - Super simple example
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GENERATE DOWNLOAD PLAN METADATA ".center(80, "="))
    print("Quick example of metadata generation...\n")

    # Example with typical values you use
    sat_id = "19"                  # GOES-19
    product_id = "ABI-L2-LSTF"   # Common product
    year = "2026"
    day = "003"                    # Day 100 of the year

    
    try:
        metadata = generate_dict(sat_id, product_id, year, day)
        
        print(f"Product: {product_id}")
        print(f"Satellite: GOES-{sat_id}")
        print(f"Date: {year}-{day}")
        print("\nGenerated metadata:")
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        print("\nDone.")
    
    except Exception as e:
        print(f"\n❌ Error generating metadata:")
        print(f"   {e}")

    print("=" * 80 + "\n")
