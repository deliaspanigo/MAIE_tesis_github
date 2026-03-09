# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_utils/generate_plan_download_file_name.py
# Version: 1.1.1
# Description: Self-auditing naming and path generator for GOES plans.
# Fully automatic local function discovery and validation.
# =============================================================================
import inspect
import sys
import re
from pathlib import Path
from legion_goes.sot.sat_hardcoded.access.get_SOT_goes_info_sat import get_SOT_goes_info_sat

# --- DETECCIÓN SEGURA DEL NOMBRE DEL ARCHIVO ---
# Eliminamos los bloques try-except anidados que causaban el NameError
current_file = Path(__file__).name if "__file__" in locals() or "__file__" in globals() else "fn01_file_name_plan_download (Interactive)"

# =============================================================================
# THE WORKERS (Generators)
# =============================================================================
def generate_plan_download_file_name(sat_id: str, product_id: str, year: str, day: str) -> str:
    """
    Generates standardized filename using progressive substitution.
    """
    ctx = "[fn01 - generate_plan_download_file_name]"

    template = "plan_01-download_[YEAR]_[DAY]_[SAT]_[POS]_[PROD].json"

    try:
        # Retrieve satellite info from the Source of Truth
        sat_info = get_SOT_goes_info_sat(sat_id=sat_id)

        # Build filename via string replacement
        name = template.replace("[YEAR]", str(year))
        name = name.replace("[DAY]", str(day).zfill(3))
        name = name.replace("[SAT]", f"GOES{sat_info['id']}")
        name = name.replace("[POS]", sat_info['position'].upper())
        name = name.replace("[PROD]", product_id)
        return name

    except Exception as e:
        raise RuntimeError(f"\n{ctx} Filename generation failed:\n{str(e)}") from None

# ===================================================================
# MAIN EXECUTION - Super simple example
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: PLAN DOWNLOAD FILENAME GENERATOR ".center(80, "="))
    print(f"Context: {current_file}")
    print("Quick example of filename generation...\n")

    # Example with a product you use a lot: ABI-L2-MCMIPF on GOES-19
    sat_id = "19"
    product_id = "ABI-L2-MCMIPF"
    year = "2026"
    day = "100"

    try:
        filename = generate_plan_download_file_name(sat_id, product_id, year, day)
        
        print(f"Product: {product_id}")
        print(f"Satellite: GOES-{sat_id}")
        print(f"Date: {year}-{day}")
        print(f"Generated filename:")
        print(f" → {filename}")
        print("\nDone.")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("=" * 80 + "\n")
