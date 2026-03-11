"""
Path: legion_goes/code/python_sp/f99_utils/get_s_timestamp_from_nc.py
Version: 1.0.1
Description: Standardized timestamp extractor from GOES NetCDF filenames.
"""

import re
from pathlib import Path

def get_s_timestamp_from_nc(nc_path):
    """
    1. Validates .nc extension.
    2. Extracts the 's' time block (minimum 11 digits).
    
    Args:
        nc_path (str/Path): Path to the NetCDF file.
        
    Returns:
        str: Timestamp starting with 's' (e.g., 's20260701200201') or None if invalid.
    """
    path_obj = Path(nc_path)
    
    # --- VALIDATION 1: Extension ---
    if path_obj.suffix.lower() != '.nc':
        print(f"      ⚠️ [ERROR] Invalid extension (expected .nc): {path_obj.suffix}")
        return None

    # --- VALIDATION 2: Time Pattern ---
    # Regex breakdown:
    # _s          -> Must start with '_s'
    # (\d{11,14}) -> Captures between 11 and 14 digits
    # (?=_|\.)    -> Lookahead: followed by an underscore or the file extension dot
    filename = path_obj.name
    match = re.search(r'_s(\d{11,14})(?=_|\.)', filename)
    
    if match:
        # Returns with the 's' prefix included
        return f"s{match.group(1)}"
    else:
        print(f"      ⚠️ [ERROR] Valid timestamp not detected in: {filename}")
        return None

# =============================================================================
# TESTS
# =============================================================================
if __name__ == "__main__":
    print("\n" + " EXCLUSIVE FUNCTION DEBUGGING ".center(50, "="))
    
    # Case 1: NOAA Standard (with underscores on both sides)
    case1 = "OR_ABI-L2-MCMIPF_G16_s20260701200201_e2026.nc"
    print(f"Test 1 (Standard):  {get_s_timestamp_from_nc(case1)}")
    
    # Case 2: Short example (no underscore after the timestamp)
    case2 = "G16_s20260701200.nc"
    print(f"Test 2 (Short):     {get_s_timestamp_from_nc(case2)}")
    
    # Case 3: Extension error
    case3 = "file_s20260701200.txt"
    print(f"Test 3 (Extension): {get_s_timestamp_from_nc(case3)}")
    
    print("=" * 50 + "\n")
