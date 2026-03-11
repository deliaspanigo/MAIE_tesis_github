# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_act01/generate_dict_plan_download.py
# Version: 1.7.0 (Dual Path Logic: Plan vs Raw Data)
# =============================================================================
import os
import json  

from legion_goes.tasks.task02_download.actions.fn_act01.utils.generate_dict01_self_info     import generate_dict as generate_dict01_self_info
from legion_goes.tasks.task02_download.actions.fn_act01.utils.generate_dict02_sat_prod_info import generate_dict as generate_dict02_sat_prod_info
from legion_goes.tasks.task02_download.actions.fn_act01.utils.generate_dict03_inventory     import generate_dict as generate_dict03_inventory
from legion_goes.tasks.task02_download.actions.fn_act01.utils.generate_dict04_summary       import generate_dict as generate_dict04_summary

########################################################################################
def generate_dict_plan_download(sat_id: str, product_id: str, year: str, day: str) -> dict:
    """Generates metadata about the Download Plan file itself."""
  
  
    dict01_self_info = generate_dict01_self_info(sat_id=sat_id, product_id=product_id, year=year, day=day)
    dict02_sat_prod_info = generate_dict02_sat_prod_info(sat_id=sat_id, product_id=product_id, year=year, day=day)
    dict03_inventory = generate_dict03_inventory(sat_id=sat_id, product_id=product_id, year=year, day=day)
    dict04_summary = generate_dict04_summary(dict_inventory = dict03_inventory)
  
    
    dict_plan_download = {
        "self_info": dict01_self_info,
        "sat_prod_info": dict02_sat_prod_info,
        "inventory": dict03_inventory,
        "summary": dict04_summary
    }
  
    return dict_plan_download

# ===================================================================
# MAIN EXECUTION - Simple example
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GENERATE FULL DOWNLOAD PLAN DICTIONARY ".center(80, "="))
    print("Quick example of combined metadata generation...\n")
    
    # Typical values you use
    sat_id = "19" # GOES-19
    product_id = "ABI-L2-MCMIPF" # Common product
    year = "2026"
    day = "100" # Day 100 of the year
    
    try:
        full_dict = generate_dict_plan_download(sat_id, product_id, year, day)
       
        print(f"Satellite: GOES-{sat_id}")
        print(f"Product: {product_id}")
        print(f"Date: {year}-{day}")
        
        # Safe access to total expected files
        summary = full_dict.get("summary", {})
        expected_files = summary.get("expected_total_files", "KEY NOT FOUND")
        print(f"Total expected files: {expected_files}")
        
        print("\nFull combined dictionary (pretty print):")
        print(json.dumps(full_dict, indent=2, ensure_ascii=False))
        print("\nDone.")
   
    except Exception as e:
        print(f"\n❌ Error generating full dictionary:")
        print(f" {e}")
    
    print("=" * 80 + "\n")
