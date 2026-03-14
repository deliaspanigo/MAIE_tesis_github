"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/utils/get_str_s_timestamp_short_from_nc.py
Version: 1.1.0
Description: Extracts and slices the start timestamp from a NetCDF filename 
             based on the SOT (Source of Truth) time format length.
"""

import re
from pathlib import Path
from typing import Optional

# Assuming this import exists in your environment
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product

def get_str_s_timestamp_short_from_nc(
    product_id: str, 
    input_nc: str,
) -> Optional[str]:
    """
    Slices the timestamp from the NC filename using the exact length 
    defined in the SOT for that specific product.
    """
    
    # 1. Retrieve SOT Template
    product_SOT_info = get_SOT_goes_info_product(product_id=product_id)
    str_SOT_time_format = product_SOT_info["time_format"]
    total_expected = len(str_SOT_time_format)
    
    # 2. Extract Filename
    str_file_name = Path(input_nc).name
    
    # 3. Regex: Capture all digits following '_s'
    match = re.search(r'_s(\d+)', str_file_name)
    
    if match:
        full_timestamp_digits = match.group(1)
        
        # --- THE SURGICAL CUT ---
        # We only keep the characters that matter according to the SOT length
        timestamp_short = full_timestamp_digits[:total_expected]
        
        # Return with the project's standard 's' prefix
        return f"s{timestamp_short}"
    
    return None

# =============================================================================
# DIAGNOSTIC MAIN: SLICE VALIDATION
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: TIMESTAMP SHORT CUTTER ".center(80, "="))
    
    # Case: Filename has milliseconds (_s...123), but SOT only expects up to minutes
    test_nc = "OR_ABI-L2-MCMIPF-M6_G16_s20260701200559_e20260701205.nc"
    p_id = "ABI-L2-MCMIPF"
    
    print(f"📄 Original File: {test_nc}")
    
    res = get_str_s_timestamp_short_from_nc(p_id, test_nc)
    
    if res:
        print(f"\n✅ Result:          {res}")
        print(f"📊 Final Length:    {len(res) - 1} digits (excluding 's')")
        
        # Visual breakdown
        raw_digits = re.search(r'_s(\d+)', test_nc).group(1)
        print(f"\nBreakdown:")
        print(f"   Digits in NC:   {raw_digits}")
        print(f"   SOT Cutoff:     {raw_digits[:11]} <--- Precision stops here")
    else:
        print("❌ Pattern '_s' not found in filename.")

    print("=" * 80 + "\n")
