# =============================================================================
# Path: legion_goes/code/python_sp/sp001_single/f02_executor/utils/get_folder_full_path_proc_single.py
# Version: 1.0.3
# Description: Standardized path generator with strict timestamp validation and slicing.
# =============================================================================

from pathlib import Path
from typing import Optional

# SOT Metadata Imports
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_sat import get_SOT_goes_info_sat
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product

try:
    import legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder as get_SOT
except ImportError:
    get_SOT = None

def get_folder_full_path_proc_single(
    sat_id: str, 
    product_id: str, 
    year: int, 
    day: int, 
    s_timestamp_short: str, 
    fnp_tag: str
) -> Optional[str]:
    """
    Generates a standardized hierarchical folder path based on project SOT rules.
    Performs validation on timestamp format and length.
    """
    
    # --- 1. SOT METADATA RETRIEVAL ---
    try:
        if get_SOT is None:
            raise ImportError("SOT folder module is not available.")

        # Get root processing folder
        root_folder = get_SOT.get_SOT_specific_folder(key="data_proc", subkey="sp01_single")
        
        # Get satellite bucket info
        sat_info = get_SOT_goes_info_sat(sat_id=sat_id)
        bucket_name = sat_info.get('bucket', 'unknown_bucket')
        
        # Get product time format requirements
        product_info = get_SOT_goes_info_product(product_id=product_id)
        sot_time_format = product_info.get("time_format", "") # e.g., "YYYYJJJHHMM"
        
        # --- 2. TIMESTAMP VALIDATION & CLEANING ---
        
        # Check if it starts with 's'
        if not s_timestamp_short.startswith('s'):
            raise ValueError(f"Timestamp must start with 's'. Received: {s_timestamp_short}")
        
        # Extract timestamp without the 's'
        timestamp_short = s_timestamp_short[1:]
        
        # Check if the extracted timestamp matches the SOT format length
        if len(timestamp_short) != len(sot_time_format):
            raise ValueError(
                f"Length mismatch! Timestamp '{timestamp_short}' ({len(timestamp_short)} digits) "
                f"does not match SOT format '{sot_time_format}' ({len(sot_time_format)} digits)."
            )
        
        # FIX: Slicing for 'sYYYYJJJHHMM' (HH is at indices 8:10 in the full string)
        # Note: In 's20260031245', index 8 and 9 are '1' and '2'.
        selected_hour = s_timestamp_short[8:10] if len(s_timestamp_short) >= 10 else "00"
        
    except Exception as e:
        print(f"      ❌ [SOT PATH ERROR] {e}")
        return None

    # --- 3. HIERARCHICAL PATH ASSEMBLY ---
    try:
        path_obj = (
            Path(root_folder) / 
            bucket_name / 
            product_id / 
            str(year) / 
            str(day).zfill(3) / 
            str(selected_hour) / 
            s_timestamp_short / 
            fnp_tag
        )
        
        # We use .resolve() if we want to clean '..' or symlinks, 
        # but for path generation, string conversion is usually enough.
        return str(path_obj)

    except (ValueError, TypeError) as e:
        print(f"      ❌ [PATH ERROR] Formatting failed: {e}")
        return None

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " UNIT TEST: FOLDER PATH GENERATOR (V.1.0.3) ".center(80, "="))
    
    # Test data following 'sYYYYJJJHHMM' format (11 digits after 's')
    # If your SOT format for LSTF/MCMIPF is 'YYYYJJJHHMMSS' (13 digits), this test will trigger the length error.
    test_params = {
        "sat_id": "19",
        "product_id": "ABI-L2-LSTF",
        "year": 2026,
        "day": 3,
        "s_timestamp_short": "s20260031245", # s + YYYY + JJJ + HH + MM
        "fnp_tag": "fnp01"
    }

    print(f"📥 Input:      {test_params['s_timestamp_short']}")
    print(f"📂 Product:    {test_params['product_id']}")
    print("-" * 80)

    # Execution
    full_path = get_folder_full_path_proc_single(**test_params)

    if full_path:
        print(f"✅ [SUCCESS] Path Generated:")
        print(f"📍 {full_path}")
        
        # Hierarchy Breakdown
        p = Path(full_path)
        print("\n🔍 Breakdown:")
        print(f"   Hour Folder: {p.parent.parent.name} (HH)")
        print(f"   Sub-Folder:  {p.parent.name} (Timestamp)")
        print(f"   Tag:         {p.name} (Tag)")
    else:
        print("❌ [FAILED] Check the error message above for validation issues.")
    
    print("=" * 80 + "\n")
