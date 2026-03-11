"""
Path: legion_goes/code/python_sp/f99_common/generate_list_expected_timestamp.py
Version: 1.8.0
Description: Generates expected GOES timestamps based on SoT configurations with length validation.
"""

import itertools
from pathlib import Path

# SOT Imports
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product

def generate_list_expected_timestamp(sat_id: str, product_id: str, year: str, day: str) -> list:
    """
    Generates a list of expected timestamp strings (prefixes) based on SoT defaults.
    Ensures all generated items match the required SoT time format length.
    
    Example output: ['20260700000', '20260700100', ...]
    """
    # 1. Retrieve SOT information
    prod_sot_info = get_SOT_goes_info_product(product_id=product_id)
    sot_time_format = prod_sot_info.get("time_format", "YYYYJJJHHMM")
    sot_default_time = prod_sot_info.get("default_time", {})
    
    # Required length based on SoT (e.g., 'YYYYJJJHHMM' = 11 characters)
    required_length = len(sot_time_format)

    # 2. Base date prefix (Year + Julian Day)
    date_prefix = f"{year}{day}"

    # 3. Generate all time combinations (HH + MM + SS) from SoT defaults
    # We use .strip() and ensure combinations are built from SOT keys
    list_time_suffixes = [
        f"{h}{m}{s}".strip()
        for h, m, s in itertools.product(
            sot_default_time.get("hours", [""]),
            sot_default_time.get("minutes", [""]),
            sot_default_time.get("seconds", [""])
        )
    ]
    
    # 4. Build full timestamps
    raw_list = [f"{date_prefix}{t}" for t in list_time_suffixes]
    
    # 5. Length Validation Control
    # Filters out any timestamp that doesn't match the SoT format length
    validated_list = []
    for ts in raw_list:
        if len(ts) == required_length:
            validated_list.append(ts)
        else:
            print(f"      ⚠️ [WARNING] Timestamp '{ts}' rejected. "
                  f"Length {len(ts)} != Expected {required_length}")
        
    return validated_list

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: EXPECTED TIMESTAMP GENERATION ".center(60, "="))
    
    # Mock parameters for testing
    TEST_SAT = "16"
    TEST_PROD = "ABI-L2-MCMIPF"
    TEST_YEAR = "2026"
    TEST_DAY = "070" # Julian Day
    
    print(f"Target Product: {TEST_PROD}")
    print(f"Target Date:    Year {TEST_YEAR}, Day {TEST_DAY}")
    
    try:
        expected_timestamps = generate_list_expected_timestamp(
            sat_id=TEST_SAT, 
            product_id=TEST_PROD, 
            year=TEST_YEAR, 
            day=TEST_DAY
        )
        
        print(f"\n✅ Successfully generated {len(expected_timestamps)} timestamps.")
        
        # Display first 5 samples
        print("First 5 samples:")
        for ts in expected_timestamps[:5]:
            print(f"   - {ts}")
            
    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Failed to generate list: {e}")
    
    print("=" * 60 + "\n")
