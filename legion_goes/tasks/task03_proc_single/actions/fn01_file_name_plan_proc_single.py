# =============================================================================
# FILE PATH: src/legion_goes/tasks/task03_proc_single/actions/fn01_file_name_plan_proc_single.py
# Version: 1.7.5 (Synced Pathing with Download Plan)
# =============================================================================

import inspect
import sys
from pathlib import Path

# =============================================================================
# CRITICAL SOT IMPORTS
# =============================================================================
try:
    from legion_goes.SoT.naming_conventions import _get_sat_info
    from legion_goes.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError as e:
    raise ImportError(f"Structure mismatch in SoT imports: {e}")

# =============================================================================
# 1. THE GATEKEEPER (Validador Sincronizado)
# =============================================================================

def validate_proc_params(year=None, day=None, sat_id=None, product_id=None, fnp_tag=None, output_folder_base=None):
    """ Valida parámetros incluyendo la base del output para consistencia. """
    if year is not None and not (isinstance(year, (str, int)) and len(str(year)) == 4):
        raise ValueError(f"Invalid year: '{year}'.")
    if day is not None:
        d = int(day)
        if not (1 <= d <= 366): raise ValueError(f"Day '{d}' out of range.")
    if product_id is not None and product_id not in AVAILABLE_GOES_PRODUCTS:
        raise ValueError(f"Product '{product_id}' not found in SoT.")
    if output_folder_base is not None:
        if not isinstance(output_folder_base, (str, Path)):
            raise TypeError("output_folder_base must be Path or str")
    return True

# =============================================================================
# 2. THE WORKERS (Generators)
# =============================================================================

def generate_plan_proc_single_file_name(year: str, day: str, sat_id: str, product_id: str, fnp_tag: str) -> str:
    """ Construye el nombre del archivo JSON usando el template estándar. """
    template = "plan_02-proc-01-single_[YEAR]_[DAY]_[SAT]_[POS]_[PROD]_[TAG].json"
    
    validate_proc_params(year=year, day=day, sat_id=sat_id, product_id=product_id, fnp_tag=fnp_tag)
    sat_info = _get_sat_info(sat_id)
    
    name = template.replace("[YEAR]", str(year))
    name = name.replace("[DAY]", str(day).zfill(3))
    name = name.replace("[SAT]", f"GOES{sat_info['id']}")
    name = name.replace("[POS]", sat_info['pos'].upper())
    name = name.replace("[PROD]", product_id)
    name = name.replace("[TAG]", fnp_tag)
    return name

def generate_plan_proc_single_file_path(
    year: str, 
    day: str, 
    sat_id: str, 
    product_id: str, 
    fnp_tag: str, 
    output_folder_base: str,
    default_sub_folder: bool = True
) -> Path:
    """
    CONSTRUYE la ruta absoluta sincronizada con la estructura de descarga.
    Subestructura: /output_folder_base/YEAR/DDD/filename.json
    """
    ctx = "[fn01 - generate_plan_proc_single_file_path]"
    
    try:
        # Validación
        validate_proc_params(
            year=year, day=day, sat_id=sat_id, 
            product_id=product_id, fnp_tag=fnp_tag,
            output_folder_base=output_folder_base
        )
        
        base_dir = Path(output_folder_base)
        
        # IGUAL QUE EN DOWNLOAD: /YYYY/DDD/
        if default_sub_folder:
            target_dir = base_dir / str(year) / str(day).zfill(3)
        else:
            target_dir = base_dir
            
        target_dir.mkdir(parents=True, exist_ok=True)
        
        filename = generate_plan_proc_single_file_name(year, day, sat_id, product_id, fnp_tag)
        return target_dir / filename
        
    except Exception as e:
        raise RuntimeError(f"\n{ctx} Path resolution failed:\n{str(e)}") from None
