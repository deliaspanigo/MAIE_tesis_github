# =============================================================================
# FILE PATH: # FILE PATH: legion_goes/code/python_sp/f01_donwload/utils/generate_plan_proc_single_file_path.py.py
# Version: 1.2.6 (Refined Reference-Based Logic)
# =============================================================================
import os
from pathlib import Path

# --- LEGION IMPORTS ---
from legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder import get_SOT_specific_folder
from legion_goes.code.python_sp.f01_donwload.utils import generate_plan_proc_single_file_name

def generate_plan_proc_single_file_path(
    sat_id: str,
    product_id: str,
    year: str,
    day: str,
    fnp_tag: str
) -> Path:
    """
    Resolves the process plan path by detecting absolute/relative roots 
    and targeting the 'data_proc/sp01_single' subfolder.
    """
    ctx = "[fn01 - generate_plan_proc_single_file_path]"
    
    try:
        # 1. Capture Raw SOT Output (Usando subkey para data_proc)
        raw_sot_output = get_SOT_specific_folder(key="data_proc", subkey="sp01_single")
        sot_path = Path(raw_sot_output)
        
        # 2. SMART PATH LOGIC
        if sot_path.is_absolute():
            target_base = sot_path
        else:
            target_base = Path(os.getcwd()) / sot_path
        
        # 3. DATE-BASED SUBFOLDERS
        str_year = str(year)
        str_day = str(day).zfill(3)
        target_dir = target_base / str_year / str_day
        
        # 4. FILENAME GENERATION
        # IMPORTANTE: Aquí pasamos el fnp_tag que requiere el procesador
        filename = generate_plan_proc_single_file_name(
            sat_id=sat_id, 
            product_id=product_id, 
            year=year, 
            day=day,
            fnp_tag=fnp_tag
        )
            
        output_file_path = target_dir / filename

        return output_file_path
        
    except Exception as e:
        raise RuntimeError(f"\n{ctx} Path resolution failed:\n{str(e)}") from None

# ===================================================================
# UNIT TEST
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: PROC PATH GENERATOR TEST ".center(80, "="))
    
    try:
        path = generate_plan_proc_single_file_path(
            sat_id="19", 
            product_id="ABI-L2-MCMIPF", 
            year="2026", 
            day="003",
            fnp_tag="fnp01"
        )
        print(f"📍 Final Path: {path}")
        print(f"✅ Parent Dir: {path.parent}")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
