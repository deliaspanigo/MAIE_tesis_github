"""
Path: src/legion_goes/task/task03_processing/subtask01_proc_single/fn01_file_name_plan_proc_single.py
Version: 0.4.0
Description: Filename and path generator for GOES proc single general plans.
             Added 'proc_tag' support for multiple processing types.
"""

from pathlib import Path
import re

# Importaciones desde el SoT central
try:
    from legion_goes.SoT.naming_conventions import _get_sat_info
    from legion_goes.SoT.goes_hardcoded_folders import get_my_path
    from legion_goes.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError as e:
    print(f"\n[CRITICAL ERROR] - Structure mismatch in SoT imports: {e}\n")
    raise SystemExit(1)

def get_plan_proc_single_file_name(year: str, day: str, sat_id: str, product_id: str, proc_tag: str) -> str:
    """Genera el nombre del .json incluyendo el tag de procesamiento."""
    ctx = "[task03_proc - fn01 - get_plan_proc_single_file_name()]"
    
    try:
        # 1. Validaciones
        if not re.match(r'^\d{4}$', str(year)):
            raise ValueError(f"Invalid year format: {year}.")
        
        if not (1 <= int(day) <= 366):
            raise ValueError(f"Invalid Julian day: {day}.")
            
        if product_id not in AVAILABLE_GOES_PRODUCTS:
            raise ValueError(f"Product {product_id} not found in SoT.")

        # 2. Inferencia de Satélite
        sat_info = _get_sat_info(sat_id)
        sat_label = f"GOES{sat_info['id']}"
        pos_label = sat_info['pos'].upper() 
        
        day_str = str(day).zfill(3)
        
        # Resultado esperado: plan_02_proc-01-single_2026_062_GOES19_EAST_ABI-L2-MCMIPF_default-rgb.json
        return f"plan_02_proc-01-single_{year}_{day_str}_{sat_label}_{pos_label}_{product_id}_{proc_tag}.json"

    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None

def get_plan_proc_single_file_path(year: str, day: str, sat_id: str, product_id: str, proc_tag: str) -> Path:
    """Devuelve la ruta absoluta al plan de procesamiento."""
    ctx = "[task03_proc - fn01 - get_plan_proc_single_file_path()]"
    
    try:
        base_dir = get_my_path("data_plan")
        day_str = str(day).zfill(3)
        
        # Subestructura: /data_plan/YEAR/DDD/
        target_dir = base_dir / str(year) / day_str
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_name = get_plan_proc_single_file_name(year, day, sat_id, product_id, proc_tag)
        return target_dir / file_name

    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: Failed to resolve path: {e}\n") from None
