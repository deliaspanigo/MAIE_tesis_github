"""
Path: src/goes_processor/task/task02_download/actions/fn01_file_name_plan_download.py
Version: 0.3.2
Description: Filename and path generator for GOES download plans.
             Integrated with v.0.3.0 Satellite Inference (SoT).
"""

from pathlib import Path
import re

# Importaciones desde el SoT central
try:
    from goes_processor.SoT.naming_conventions import _get_sat_info
    from goes_processor.SoT.goes_hardcoded_folders import get_my_path
    from goes_processor.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError as e:
    print(f"\n[CRITICAL ERROR] - Structure mismatch in SoT imports: {e}\n")
    raise SystemExit(1)

def get_plan_download_file_name(year: str, day: str, sat_id: str, product_id: str) -> str:
    """Generates the .json filename for download plans by inferring satellite position."""
    ctx = "[task02_download - actions - fn01 - get_plan_download_file_name()]"
    
    try:
        # 1. Validaciones de formato
        if not re.match(r'^\d{4}$', str(year)):
            raise ValueError(f"Invalid year format: {year}. Expected YYYY.")
        
        # El día puede venir como '5' o '005', lo manejamos con zfill después
        if not (1 <= int(day) <= 366):
            raise ValueError(f"Invalid Julian day: {day}. Must be 1-366.")
            
        if product_id not in AVAILABLE_GOES_PRODUCTS:
            raise ValueError(f"Product {product_id} not found in AVAILABLE_GOES_PRODUCTS SoT.")

        # 2. Inferencia de Satélite (Motor v.0.3.0)
        # Esto nos da el ID limpio (16, 17, 18, 19) y la posición (EAST, WEST)
        sat_info = _get_sat_info(sat_id)
        sat_label = f"GOES{sat_info['id']}"
        pos_label = sat_info['pos'] 
        
        day_str = str(day).zfill(3)
        
        # Resultado: plan_01_download_2026_060_GOES16_EAST_ABI-L2-LSTF.json
        return f"plan_01_download_{year}_{day_str}_{sat_label}_{pos_label}_{product_id}.json"

    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None

def get_plan_download_file_path(year: str, day: str, sat_id: str, product_id: str) -> Path:
    """Returns the absolute Path to the plan and ensures the directory structure exists."""
    ctx = "[task02_download - actions - fn01 - get_plan_download_file_path()]"
    
    try:
        base_dir = get_my_path("data_plan")
        day_str = str(day).zfill(3)
        
        # Subestructura temporal: /data_plan/YEAR/DDD/
        target_dir = base_dir / str(year) / day_str
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_name = get_plan_download_file_name(year, day, sat_id, product_id)
        return target_dir / file_name

    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: Failed to resolve path: {e}\n") from None
