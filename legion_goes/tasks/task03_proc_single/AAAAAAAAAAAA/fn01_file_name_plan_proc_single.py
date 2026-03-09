# =============================================================================
# FILE PATH: src/legion_goes/tasks/task03_proc_single/actions/fn01_file_name_plan_proc_single.py
# Version: 1.7.0
# Description: Self-auditing naming and path generator for GOES processing plans.
#              Renamed to 'generate' to emphasize active logic creation.
# =============================================================================

import inspect
import sys
import re
from pathlib import Path

# =============================================================================
# CRITICAL SOT IMPORTS & STRUCTURE VALIDATION
# =============================================================================
try:
    try:
        current_file = Path(__file__).name
    except NameError:
        current_file = "fn01_file_name_plan_proc_single (Interactive)"

    from legion_goes.SoT.naming_conventions import _get_sat_info
    from legion_goes.SoT.goes_hardcoded_folders import get_my_path
    from legion_goes.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS

except ImportError as e:
    error_header = "!" * 85
    msg = (
        f"\n{error_header}\n"
        f"  [CRITICAL IMPORT ERROR]\n"
        f"  LOCATION: {current_file}\n"
        f"  CAUSE: Structure mismatch in SoT imports.\n"
        f"  DETAIL: {e}\n"
        f"{error_header}\n"
    )
    print(msg)
    raise ImportError(msg) from None

# =============================================================================
# 1. THE GUARDIAN (Auditores Internos)
# =============================================================================

def _audit_interface_integrity():
    """ 
    STRICT AUTOMATIC AUDIT: 
    Ensures all 'generate' functions are synced with the validator. 
    """
    ctx = "[Internal Audit]"
    TARGET_VALIDATOR = 'validate_proc_params'
    my_name = inspect.currentframe().f_code.co_name
    
    current_module = sys.modules[__name__]
    if not hasattr(current_module, TARGET_VALIDATOR): return
        
    validator_func = getattr(current_module, TARGET_VALIDATOR)
    try:
        val_sig = inspect.signature(validator_func)
        validator_args = {arg_name for arg_name in val_sig.parameters}
    except Exception: return

    for name, func in inspect.getmembers(current_module, inspect.isfunction):
        # Auditamos solo funciones que generen nombres o rutas
        if func.__module__ == __name__ and name.startswith('generate_'):
            try:
                f_sig = inspect.signature(func)
                func_args = {arg_name for arg_name in f_sig.parameters}
                data_args = {a for a in func_args if not a.startswith('default_')}
                
                missing = data_args - validator_args
                if missing:
                    raise ImportError(f"\n{'!'*75}\n{ctx} INTERFACE MISMATCH: '{name}' needs {missing}\n{'!'*75}\n")
            except (ValueError, TypeError): continue

# =============================================================================
# 2. THE GATEKEEPER (Validador)
# =============================================================================

def validate_proc_params(year=None, day=None, sat_id=None, product_id=None, fnp_tag=None):
    """ Valida parámetros específicos de procesamiento contra el SoT. """
    fn_name = inspect.currentframe().f_code.co_name
    ctx = f"[{fn_name}]"

    try:
        # 1. Validar Año
        if year is not None:
            if not (isinstance(year, (str, int)) and len(str(year)) == 4):
                raise ValueError(f"Invalid year: '{year}'. Expected 'YYYY'.")

        # 2. Validar Día Juliano
        if day is not None:
            d = int(day)
            if not (1 <= d <= 366): raise ValueError(f"Day '{d}' out of range.")

        # 3. Validar Producto
        if product_id is not None and product_id not in AVAILABLE_GOES_PRODUCTS:
            raise ValueError(f"Product '{product_id}' not found in SoT.")

        # 4. Validar FNP Tag
        if fnp_tag is not None:
            if not isinstance(fnp_tag, str) or len(fnp_tag) < 1:
                raise ValueError(f"Invalid fnp_tag: '{fnp_tag}'.")

        return True

    except Exception as e:
        raise type(e)(f"\n{'='*80}\n❌ PROC VALIDATION ERROR: {ctx}\nDETAILS: {str(e)}\n{'='*80}") from None

# =============================================================================
# 3. THE WORKERS (Generators)
# =============================================================================

def generate_plan_proc_single_file_name(year: str, day: str, sat_id: str, product_id: str, fnp_tag: str) -> str:
    """ 
    CONSTRUYE ACTIVAMENTE el nombre del archivo JSON del plan. 
    Ej: plan_02_proc-01-single_2026_062_GOES19_EAST_ABI-L2-MCMIPF_default-rgb.json
    """
    ctx = "[fn01 - generate_plan_proc_single_file_name]"
    template = "plan_02_proc-01-single_[YEAR]_[DAY]_[SAT]_[POS]_[PROD]_[TAG].json"
    
    try:
        validate_proc_params(year=year, day=day, sat_id=sat_id, product_id=product_id, fnp_tag=fnp_tag)
        
        sat_info = _get_sat_info(sat_id)
        
        name = template.replace("[YEAR]", str(year))
        name = name.replace("[DAY]", str(day).zfill(3))
        name = name.replace("[SAT]", f"GOES{sat_info['id']}")
        name = name.replace("[POS]", sat_info['pos'].upper())
        name = name.replace("[PROD]", product_id)
        name = name.replace("[TAG]", fnp_tag)
        
        return name
        
    except Exception as e:
        raise RuntimeError(f"\n{ctx} Filename generation failed:\n{str(e)}") from None

def generate_plan_proc_single_file_path(year: str, day: str, sat_id: str, product_id: str, fnp_tag: str) -> Path:
    """ 
    CONSTRUYE ACTIVAMENTE la ruta absoluta donde residirá el plan.
    """
    ctx = "[fn01 - generate_plan_proc_single_file_path]"
    
    try:
        # Inferencia de carpeta base desde el SoT
        base_dir = get_my_path("data_plan") 
        
        # Subestructura: /data_plan/YEAR/DDD/
        target_dir = base_dir / str(year) / str(day).zfill(3)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        filename = generate_plan_proc_single_file_name(year, day, sat_id, product_id, fnp_tag)
        
        return target_dir / filename
        
    except Exception as e:
        raise RuntimeError(f"\n{ctx} Path resolution failed:\n{str(e)}") from None

# =============================================================================
# INITIALIZATION
# =============================================================================

_audit_interface_integrity()
