# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action01/step02_dict_parts/generate_dict02_sat_prod_info.py
# Version: 1.7.0 (Dual Path Logic: Plan vs Raw Data)
# =============================================================================
from datetime import datetime
import os
import json
import itertools

# SOT Imports
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_sat import get_SOT_goes_info_sat
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product

# Download Imports


def generate_dict(sat_id: str, product_id: str, year: str, day: str) -> dict:
    
    # Harcoded info for sat_id and product_id
    sat_SoT_info = get_SOT_goes_info_sat(sat_id = sat_id)
    prod_SoT_info = get_SOT_goes_info_product(product_id = product_id)
  
    # Basics 01
    bucket_name = sat_SoT_info['bucket']
    selected_cadence = prod_SoT_info["cadence_full_disk"]
    position = sat_SoT_info['position'].upper()
  
    # Basics 02
    date_julian = f"{year}{day.zfill(3)}"  # Día juliano como string (ej. "2026100")
    satellite_name = f"GOES-{sat_id}"
  
    # Basics 03
    date_julian_obj = datetime.strptime(date_julian, "%Y%j")
    date_gregorian = date_julian_obj.strftime("%Y-%m-%d")  # Fecha gregoriana formateada
  
    the_dict = {
        "satellite": satellite_name,
        "position": position.upper(),
        "bucket": bucket_name,
        "product_id": product_id,
        "cadence": selected_cadence,
        "year": year,
        "day": day,
        "date_julian": date_julian,          # Día juliano como string (ej. "2026100")
        "date_gregorian": date_gregorian     # Fecha gregoriana (ej. "2026-04-10")
    }
    return the_dict

# ===================================================================
# MAIN EXECUTION - Super simple example
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GENERATE SATELLITE & PRODUCT METADATA ".center(80, "="))
    print("Quick example of metadata generation...\n")

    # Example with typical values you use
    sat_id = "19"                  # GOES-19
    product_id = "ABI-L2-LSTF"   # Common product
    year = "2026"
    day = "003"                    # Day 100 of the year

    try:
        metadata = generate_dict(sat_id, product_id, year, day)
        
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        print("\nDone.")
    
    except Exception as e:
        print(f"\n❌ Error generating metadata:")
        print(f"   {e}")

    print("=" * 80 + "\n")
