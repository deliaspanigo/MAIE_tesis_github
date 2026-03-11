"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/utils/get_folder_full_path_proc_single.py
Version: 1.0.1
Description: Standardized path generator returning strings for compatibility with processing cores.
"""

from pathlib import Path
from typing import Optional

# Ensure these are accessible in your PYTHONPATH
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_sat import get_SOT_goes_info_sat

try:
    import legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder as get_SOT
except ImportError:
    get_SOT = None

def get_folder_full_path_proc_single(
    sat_id: str, 
    product_id: str, 
    year: int, 
    day: int, 
    hour: int, 
    s_time_short: str, 
    fnp_tag: str
) -> Optional[str]:
    """
    Generates a hierarchical folder path as a STRING based on project standards:
    [ROOT] / [BUCKET] / [PRODUCT] / [YEAR] / [DAY] / [HOUR] / [TIME_SHORT] / [FNP_TAG]

    Args:
        sat_id (str): Satellite identifier (e.g., 'G16').
        product_id (str): Product name (e.g., 'ABI-L2-MCMIPF').
        year (int): Year.
        day (int): Julian day.
        hour (int): Hour.
        s_time_short (str): Short timestamp (e.g., 's20260031200').
        fnp_tag (str): Processing tag (e.g., 'fnp01').

    Returns:
        Optional[str]: Absolute path string or None if lookup fails.
    """
    
    # --- 1. SOT METADATA RETRIEVAL ---
    try:
        if get_SOT is None:
            raise ImportError("SOT folder module is not available.")

        # Retrieve base path and bucket name
        root_folder = get_SOT.get_SOT_specific_folder(key="data_proc", subkey="sp01_single")
        sat_info = get_SOT_goes_info_sat(sat_id=sat_id)
        bucket_name = sat_info.get('bucket', 'unknown_bucket')
        
    except Exception as e:
        print(f"      ❌ [SOT PATH ERROR] Metadata lookup failed: {e}")
        return None

    # --- 2. HIERARCHICAL PATH ASSEMBLY ---
    try:
        # Assemble using Path for OS-safety, then convert to string
        path_obj = (
            Path(root_folder) / 
            bucket_name / 
            product_id / 
            str(year) / 
            f"{int(day):03d}" / 
            f"{int(hour):02d}" / 
            s_time_short / 
            fnp_tag
        )
        
        # Return as string as requested
        return str(path_obj.resolve())

    except (ValueError, TypeError) as e:
        print(f"      ❌ [PATH ERROR] Formatting failed: {e}")
        return None
