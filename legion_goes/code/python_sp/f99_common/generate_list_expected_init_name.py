"""
Path: legion_goes/code/python_sp/f99_common/generate_list_expected_init_name.py
Version: 1.8.0
Description: Generates a list of expected GOES file starting strings (prefixes) for download planning.
"""

from pathlib import Path

# SOT Imports
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product

# Common Logic Imports
from legion_goes.code.python_sp.f99_common.generate_list_expected_timestamp import generate_list_expected_timestamp

def generate_list_expected_init_name(sat_id: str, product_id: str, year: str, day: str) -> list:
    """
    Generates a list of expected file start strings based on SoT defaults.
    Combines the product's initial name, satellite ID, and generated timestamps.
    
    Example output item: OR_ABI-L2-LSTF-M6_G16_s20260702000
    """
    # 1. Retrieve Product Info from Source of Truth (SoT)
    prod_sot_info = get_SOT_goes_info_product(product_id=product_id)
    init_file_name = prod_sot_info.get("init_file_name", "OR_ABI-L2-UNKNOWN-M6_G")
    
    # 2. Generate the required timestamps using the common utility
    # Note: This function already validates lengths based on SoT time_format
    list_timestamps = generate_list_expected_timestamp(
        sat_id=sat_id, 
        product_id=product_id, 
        year=year, 
        day=day
    )
    
    # 3. Construct the base prefix: [InitName][SatID]_s
    # Example: OR_ABI-L2-LSTF-M6_G16_s
    file_base_prefix = f"{init_file_name}{sat_id}_s"
    
    # 4. Combine prefix with timestamps
    list_expected_init_names = [f"{file_base_prefix}{t}" for t in list_timestamps]
    
    return list_expected_init_names

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: EXPECTED PRODUCT INITIAL NAME GENERATION ".center(70, "="))
    
    # Mock parameters for the test
    TEST_SAT = "16"
    TEST_PROD = "ABI-L2-MCMIPF"
    TEST_YEAR = "2026"
    TEST_DAY = "070" 

    print(f"Input Parameters:")
    print(f"   - Satellite: {TEST_SAT}")
    print(f"   - Product:   {TEST_PROD}")
    print(f"   - Date:      Year {TEST_YEAR} / Day {TEST_DAY}")
    print("-" * 70)

    try:
        # Execute the function
        expected_names = generate_list_expected_init_name(
            sat_id=TEST_SAT,
            product_id=TEST_PROD,
            year=TEST_YEAR,
            day=TEST_DAY
        )

        if expected_names:
            print(f"✅ Success! Generated {len(expected_names)} expected prefixes.")
            
            # Show top 10 samples for verification
            print("\nSamples (First 10):")
            for i, name in enumerate(expected_names[:10], 1):
                print(f"   {i:02d}. {name}")
            
            if len(expected_names) > 10:
                print(f"   ... and {len(expected_names) - 10} more.")
        else:
            print("⚠️ [WARNING] No names were generated. Check SoT default_time settings.")

    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Execution failed: {e}")

    print("=" * 70 + "\n")
