"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/utils/get_folder_full_path_proc_single.py
Version: 1.0.2
Description: Standardized path generator with diagnostic main and fixed hour slicing.
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
    s_timestamp_short: str, 
    fnp_tag: str
) -> Optional[str]:
    """
    Generates a hierarchical folder path as a STRING based on project standards.
    """
    
    # --- 1. SOT METADATA RETRIEVAL ---
    try:
        if get_SOT is None:
            raise ImportError("SOT folder module is not available.")

        # Retrieve base path and bucket name
        root_folder = get_SOT.get_SOT_specific_folder(key="data_proc", subkey="sp01_single")
        sat_info = get_SOT_goes_info_sat(sat_id=sat_id)
        bucket_name = sat_info.get('bucket', 'unknown_bucket')
        
        # FIX: Slicing para formato 'sYYYYJJJHHMM' (HH está en 8:10)
        selected_hour = s_timestamp_short[8:10] if len(s_timestamp_short) >= 10 else "00"
        
    except Exception as e:
        print(f"      ❌ [SOT PATH ERROR] Metadata lookup failed: {e}")
        return None

    # --- 2. HIERARCHICAL PATH ASSEMBLY ---
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
        
        return str(path_obj.resolve())

    except (ValueError, TypeError) as e:
        print(f"      ❌ [PATH ERROR] Formatting failed: {e}")
        return None

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: FOLDER PATH GENERATOR ".center(80, "="))
    
    # Datos de prueba siguiendo tu formato 'sYYYYJJJHHMM'
    test_params = {
        "sat_id": "16",
        "product_id": "ABI-L2-MCMIPF",
        "year": 2026,
        "day": 3,
        "s_timestamp_short": "s20260031245", # s + 2026 + 003 + 12 (hora) + 45 (min)
        "fnp_tag": "fnp01"
    }

    print(f"📥 Input Timestamp: {test_params['s_timestamp_short']}")
    
    # Mostrar visualmente el slicing de la hora
    ts = test_params['s_timestamp_short']
    print(f"🔍 Hour Slicing:    {ts} -> [{ts[8:10]}] (indices 8:10)")
    print("-" * 80)

    # Ejecución
    full_path = get_folder_full_path_proc_single(**test_params)

    if full_path:
        print(f"✅ [SUCCESS] Generated Path:")
        print(f"📍 {full_path}")
        
        # Validar estructura jerárquica
        p = Path(full_path)
        print("\n📂 Hierarchy Breakdown:")
        print(f"   Root:    {p.parents[6].name if len(p.parts) > 7 else '.../'}")
        print(f"   Hour:    {p.parents[1].name} (HH)")
        print(f"   Folder:  {p.parent.name} (sTimestamp)")
        print(f"   Process: {p.name} (fnp_tag)")
    else:
        print("❌ [FAILED] Could not generate path.")
    
    print("=" * 80 + "\n")
