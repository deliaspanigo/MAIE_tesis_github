# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_act01/step01_generate_init_file_name/generate_list_expected_product_init_name.py
# Version: 1.7.0 (Dual Path Logic: Plan vs Raw Data)
# =============================================================================
import json
import itertools
from datetime import datetime, timezone
from pathlib import Path

# SOT Imports
from legion_goes.sot.sat_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product

# --- 1. HELPER FUNCTIONS ---
def generate_list_expected_product_init_name(sat_id: str, product_id: str, year: str, day: str) -> list:
    """
    Generates a list of expected file start strings (prefixes) based on SoT defaults.
    Example: OR_ABI-L2-LSTF-M6_G16_s20241001200
    """
    # SOT info
    prod_SOT_info = get_SOT_goes_info_product(product_id=product_id)
    init_file_name = prod_SOT_info["init_file_name"]
    time_info = prod_SOT_info["default_time"]
    
    # Basics
    str_year = str(year)
    str_day = str(day).zfill(3)
    date_prefix = f"{str_year}{str_day}"
    
    # Generate all time combinations (HHMMSS) from SoT
    raw_times = [
        f"{h}{m}{s}".strip()
        for h, m, s in itertools.product(
            time_info["hours"],
            time_info["minutes"],
            time_info["seconds"]
        )
    ]
    
    # Construct prefix: [InitName][SatID]_s
    # Example: OR_ABI-L2-LSTF-M6_G16_s
    file_prefix = f"{init_file_name}{sat_id}_s"
    
    # Combine prefix + date + times
    list_output = [f"{file_prefix}{date_prefix}{t}" for t in raw_times]
    
    return list_output

# ===================================================================
# MAIN EXECUTION - Super simple example
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GENERATE LIST OF EXPECTED INIT FILE NAMES ".center(80, "="))
    print("Quick example of list generation...\n")

    # Example with typical values you use
    sat_id = "19"                  # GOES-19
    product_id = "ABI-L2-MCMIPF"   # Common product
    year = "2026"
    day = "100"                    # Day 100 of the year

    try:
        file_names = generate_list_expected_product_init_name(sat_id, product_id, year, day)
        
        print(f"Product: {product_id}")
        print(f"Satellite: GOES-{sat_id}")
        print(f"Date: {year}-{day}")
        print(f"Number of generated names: {len(file_names)}")
        print("\nFirst 5 names (example):")
        for name in file_names[:5]:
            print(f" → {name}")
        print(f"\n... (total: {len(file_names)} entries)")
        print("\nDone.")
    
    except Exception as e:
        print(f"\n❌ Error generating the list:")
        print(f"   {e}")

    print("=" * 80 + "\n")
