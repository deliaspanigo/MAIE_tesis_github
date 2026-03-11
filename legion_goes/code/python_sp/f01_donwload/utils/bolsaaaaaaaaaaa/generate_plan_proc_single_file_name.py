# =============================================================================
# FILE PATH: legion_goes/code/python_sp/f01_donwload/utils/generate_plan_proc_single_file_name.py
# Version: 1.1.2 (Improved: SAT Normalization & FNP Validation)
# =============================================================================
import re
from pathlib import Path
from legion_goes.sot.goes_hardcoded.access.get_SOT_goes_info_sat import get_SOT_goes_info_sat

def generate_plan_proc_single_file_name(sat_id: str, product_id: str, year: str, day: str, fnp_tag: str) -> str:
    """
    Generates standardized filename for Task 03 processing plans.
    Template: plan_02_proc-01-single_[YEAR]_[DAY]_[SAT]_[POS]_[PROD]_[FNP].json
    """
    ctx = "[fn01 - generate_plan_proc_single_file_name]"
    template = "plan_02_proc-01-single_[YEAR]_[DAY]_[SAT]_[POS]_[PROD]_[FNP].json"

    try:
        # 1. Normalizar sat_id (Quitar 'G' si el usuario la puso)
        clean_sat_id = str(sat_id).upper().replace("G", "")
        
        # 2. Obtener Info del SOT (Source of Truth)
        sat_info = get_SOT_goes_info_sat(sat_id=clean_sat_id)

        # 3. Reemplazo Progresivo
        name = template.replace("[YEAR]", str(year))
        name = name.replace("[DAY]", str(day).zfill(3))
        name = name.replace("[SAT]", f"GOES{sat_info['id']}")
        name = name.replace("[POS]", sat_info['position'].upper())
        name = name.replace("[PROD]", product_id)
        name = name.replace("[FNP]", fnp_tag.lower()) # Forzamos minúsculas para el tag

        return name

    except Exception as e:
        raise RuntimeError(f"\n{ctx} Filename generation failed for SAT {sat_id}: {str(e)}") from None

# --- TEST RÁPIDO ---
if __name__ == "__main__":
    test_name = generate_plan_proc_single_file_name(
        sat_id="19", 
        product_id="ABI-L2-MCMIPF", 
        year="2026", 
        day="3", 
        fnp_tag="fnp01"
    )
    print(f"Generated Name: {test_name}")
