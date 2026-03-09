# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_utils/generate_plan_download_file_path.py
# Version: 1.2.1 (Smart Absolute/Relative Handling)
# =============================================================================
import os
from pathlib import Path

# --- LEGION IMPORTS ---
from legion_goes.sot.folders_hardcoded.access.get_SOT_specific_folder import get_SOT_specific_folder
from legion_goes.tasks.task02_download.actions.fn_utils.generate_plan_download_file_name import generate_plan_download_file_name

def generate_plan_download_file_path(
    sat_id: str,
    product_id: str,
    year: str,
    day: str,
) -> Path:
    """Resolves the correct path by detecting if SOT provides an absolute or relative root."""
    ctx = "[fn01 - generate_plan_download_file_path]"
    
    try:
        # 1. Capture Raw SOT Output
        raw_sot_output = get_SOT_specific_folder(key="data_plan")
        sot_path = Path(raw_sot_output)
        
        # 2. SMART PATH LOGIC
        # If SOT returns an absolute path (/home/...), use it directly.
        # If it returns a relative path (data_raw), join it to the CWD.
        if sot_path.is_absolute():
            target_base = sot_path
        else:
            target_base = Path(os.getcwd()) / sot_path
        
        # 3. DATE-BASED SUBFOLDERS
        str_year = str(year)
        str_day = str(day).zfill(3)
        target_dir = target_base / str_year / str_day
        
        # 4. FILENAME GENERATION
        filename = generate_plan_download_file_name(
            sat_id=sat_id, 
            product_id=product_id, 
            year=year, 
            day=day
        )
            
        output_file_path = target_dir / filename
        
        # DEBUG LOG (Optional, you can remove this after verification)
        # print(f"DEBUG: Final path resolved to -> {output_file_path}")

        return output_file_path
        
    except Exception as e:
        raise RuntimeError(f"\n{ctx} Path resolution failed:\n{str(e)}") from None

# ===================================================================
# UNIT TEST
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: PATH GENERATOR TEST ".center(80, "="))
    
    try:
        path = generate_plan_download_file_path(
            sat_id="19", 
            product_id="ABI-L2-MCMIPF", 
            year="2026", 
            day="100"
        )
        print(f"📍 Final Path: {path}")
        print(f"✅ Exists?   : {path.exists()}")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
