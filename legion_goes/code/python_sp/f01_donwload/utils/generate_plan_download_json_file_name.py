"""
Path: legion_goes/code/python_sp/f01_donwload/utils/generate_plan_download_file_name.py
Version: 1.1.0
Description: Generates a detailed standardized JSON filename for download plans using SoT metadata.
"""

from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_sat import get_SOT_goes_info_sat

def generate_plan_download_json_file_name(sat_id: str, product_id: str, year: str, day: str) -> str:
    """
    Generates standardized filename for Task 02 download plans.
    Template: plan_01-download_[YEAR]-[DAY]_[SAT]-[POS]_[PROD].json
    """
    ctx = "[fn: generate_plan_download_json_file_name]"
    # Standard template for download plans
    template = "plan_01-download_[YEAR]-[DAY]_[SAT]-[POS]_[PROD].json"

    try:
        # 1. Normalize sat_id (Remove 'G' if present)
        clean_sat_id = str(sat_id).upper().replace("G", "")
        
        # 2. Retrieve Satellite Info from Source of Truth (SoT)
        sat_info = get_SOT_goes_info_sat(sat_id=clean_sat_id)

        # 3. Progressive Replacement
        name = template.replace("[YEAR]", str(year))
        name = name.replace("[DAY]", str(day).zfill(3))
        name = name.replace("[SAT]", f"GOES{sat_info['id']}")
        name = name.replace("[POS]", sat_info['position'].upper())
        name = name.replace("[PROD]", product_id)

        return name

    except Exception as e:
        raise RuntimeError(f"\n{ctx} Filename generation failed for SAT {sat_id}: {str(e)}") from None

# =============================================================================
# QUICK TEST
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: DOWNLOAD PLAN FILENAME GENERATION ".center(60, "="))
    
    try:
        test_name = generate_plan_download_json_file_name(
            sat_id="16", 
            product_id="ABI-L2-MCMIPF", 
            year="2026", 
            day="70"
        )
        print(f"✅ Generated Name: {test_name}")
        # Expected: plan_01_download_2026_070_GOES16_EAST_ABI-L2-MCMIPF.json
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    print("=" * 60 + "\n")
