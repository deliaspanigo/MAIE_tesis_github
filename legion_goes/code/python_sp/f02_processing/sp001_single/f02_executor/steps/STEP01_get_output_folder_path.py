"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/steps/STEP01_get_output_folder_path.py
Version: 0.0.3
Description: Isolated step with flexible product validation in filename.
"""

import re
from pathlib import Path

# --- SOT IMPORTS ---
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_product import get_SOT_goes_info_product

# --- UTILITY IMPORTS ---
from legion_goes.code.python_sp.sp001_single.f02_executor.utils.get_folder_full_path_proc_single import get_folder_full_path_proc_single

def STEP01_get_output_folder_path(sat_id, product_id, year, day, fnp_tag, nc_path):
    nc_file = Path(nc_path)
    
    # --- VALIDACIÓN FLEXIBLE ---
    # Normalizamos ambos para la comparación: eliminamos guiones y guiones bajos
    clean_id = product_id.upper().replace('-', '').replace('_', '')
    clean_filename = nc_file.name.upper().replace('-', '').replace('_', '')

    if clean_id not in clean_filename:
        print(f"      ❌ [STEP01 ERROR] Product mismatch. '{product_id}' not found in: {nc_file.name}")
        return None

    # --- TIME PARSING ---
    match = re.search(r'_s(\d{11,14})_', nc_file.name)
    if not match:
        print(f"      ❌ [STEP01 ERROR] Time pattern '_s...' not found in: {nc_file.name}")
        return None

    full_time_str = match.group(1)
    
    sot_prod = get_SOT_goes_info_product(product_id=product_id)
    time_fmt = sot_prod.get("time_format", "YYYYJJJHHMM")
    
    time_short = full_time_str[:len(time_fmt)]
    s_time_short = f"s{time_short}"
    
    pos_hour = time_fmt.find("HH")
    hour_val = int(full_time_str[pos_hour:pos_hour+2]) if pos_hour != -1 else 0

    # --- PATH RESOLUTION ---
    output_dir_str = get_folder_full_path_proc_single(
        sat_id=str(sat_id), 
        product_id=product_id, 
        year=year, 
        day=day, 
        hour=hour_val, 
        s_time_short=s_time_short, 
        fnp_tag=fnp_tag
    )
    
    if not output_dir_str: 
        return None
    
    Path(output_dir_str).mkdir(parents=True, exist_ok=True)
    
    return str(output_dir_str)

# =============================================================================
# MAIN (Diagnostic Test)
# =============================================================================
if __name__ == "__main__":
    print("\n" + " TEST: STEP01 PATH RESOLUTION (CORRECTED) ".center(60, "="))
    
    test_nc = "OR_ABI-L2-MCMIPF-M6_G16_s20260701200201_e20260701210201_c20260701215201.nc"
    
    # Test 1: Debería ser exitoso (MCMIPF coincide con el nombre)
    print(f"Test 1 (Valid):")
    res1 = STEP01_get_output_folder_path("16", "ABI-L2-MCMIPF", 2026, 70, "fnp01", test_nc)
    print(f"Result: {res1}")

    # Test 2: Debería fallar (LSTF no está en el nombre)
    print(f"\nTest 2 (Wrong Product):")
    res2 = STEP01_get_output_folder_path("16", "ABI-L2-LSTF", 2026, 70, "fnp01", test_nc)
    print(f"Result: {res2}")
    
    print("=" * 60 + "\n")
