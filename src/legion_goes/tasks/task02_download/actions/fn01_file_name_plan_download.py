# =============================================================================
# FILE PATH: src/legion_goes/tasks/task02_download/actions/fn01_file_name_plan_download.py
# Version: 1.1.0
# Description: Self-auditing naming and path generator for GOES plans.
#              Fully automatic local function discovery and validation.
# =============================================================================

import inspect
import sys
import re
from pathlib import Path

# =============================================================================
# CRITICAL SOT IMPORTS & STRUCTURE VALIDATION
# =============================================================================
try:
    # Attempt to get the current filename for error reporting
    try:
        current_file = Path(__file__).name
    except NameError:
        current_file = "fn01_file_name_plan_download (Notebook/Interactive)"

    # Importing from the SoT (Source of Truth) directory
    from legion_goes.SoT.naming_conventions import _get_sat_info
    from legion_goes.SoT.goes_hardcoded_folders import get_my_path
    from legion_goes.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS

except ImportError as e:
    # High-impact visual error message
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
    # Raise ImportError so the Notebook shows the full Traceback without killing the kernel
    raise ImportError(msg) from None

# =============================================================================
# 1. THE GUARDIAN (Fully Automatic Audit)
# =============================================================================

def _audit_interface_integrity():
    """
    STRICT AUTOMATIC AUDIT: 
    Ultra-compatible version using direct iteration to avoid 'tuple'/'MappingProxy' errors.
    Ensures all functions in this module are synced with the validator.
    """
    import inspect
    import sys

    ctx = "[Internal Audit]"
    TARGET_VALIDATOR = 'validate_params'
    my_name = inspect.currentframe().f_code.co_name
    
    current_module = sys.modules[__name__]
    if not hasattr(current_module, TARGET_VALIDATOR):
        return
        
    validator_func = getattr(current_module, TARGET_VALIDATOR)
    
    # DIRECT EXTRACTION: Iterate over the Signature.parameters object
    try:
        val_sig = inspect.signature(validator_func)
        validator_args = {arg_name for arg_name in val_sig.parameters}
    except Exception:
        return

    for name, func in inspect.getmembers(current_module, inspect.isfunction):
        # Audit only functions defined within this specific file
        if func.__module__ == __name__ and name not in [TARGET_VALIDATOR, my_name]:
            try:
                # Extract argument names from the current function
                f_sig = inspect.signature(func)
                func_args = {arg_name for arg_name in f_sig.parameters}
                
                # Filter control arguments (ignore those starting with 'default_')
                data_args = {a for a in func_args if not a.startswith('default_')}
                
                # Set difference to find missing parameters in the validator
                missing = data_args - validator_args
                
                if missing:
                    raise ImportError(
                        f"\n{'!'*75}\n"
                        f"{ctx} INTERFACE MISMATCH\n"
                        f"Function '{name}' requires: {missing}\n"
                        f"But '{TARGET_VALIDATOR}' does not support them.\n"
                        f"{'!'*75}\n"
                    )
            except (ValueError, TypeError):
                continue

# =============================================================================
# 2. THE GATEKEEPER (Validator)
# =============================================================================

def validate_params(year=None, day=None, sat_id=None, product_id=None, output_folder_base=None):
    """
    Validates input parameters against the Source of Truth (SoT).
    Includes a safety wrapper to pinpoint internal validation errors.
    """
    import pathlib
    import inspect

    # Identify this function name for the error message context
    fn_name = inspect.currentframe().f_code.co_name
    ctx = f"[{fn_name}]"

    try:
        from legion_goes.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
        
        # 1. Validate Year
        if year is not None:
            if not (isinstance(year, str) and len(year) == 4 and year.isdigit()):
                raise ValueError(f"Invalid year format: '{year}'. Expected YYYY string (e.g., '2026').")

        # 2. Validate Julian Day
        if day is not None:
            try:
                d = int(day)
                if not (1 <= d <= 366):
                    raise ValueError(f"Day '{d}' is out of range (1-366).")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid Julian day: '{day}'. Detail: {e}")

        # 3. Validate Product (Supports Dict, List, and Tuple)
        if product_id is not None:
            if product_id not in AVAILABLE_GOES_PRODUCTS:
                # Safe extraction of options for the error message
                options = list(AVAILABLE_GOES_PRODUCTS.keys()) if hasattr(AVAILABLE_GOES_PRODUCTS, 'keys') else list(AVAILABLE_GOES_PRODUCTS)
                raise ValueError(
                    f"Product '{product_id}' not found in SoT.\n"
                    f"Available options: {', '.join(map(str, options))}"
                )

        # 4. Validate Output Path
        if output_folder_base is not None:
            if not isinstance(output_folder_base, (str, pathlib.Path)):
                raise TypeError(f"output_folder_base must be Path or str, not {type(output_folder_base)}")

        # 5. Validate Satellite ID (Optional for now)
        if sat_id is not None:
            pass

        return True

    except Exception as e:
        # Capture ANY error, whether a triggered ValueError or an unexpected bug
        error_msg = (
            f"\n{'='*80}\n"
            f"❌ CRITICAL ERROR INSIDE: {ctx}\n"
            f"DETAILS: {str(e)}\n"
            f"{'='*80}"
        )
        # Raise the original exception type but with our custom header
        raise type(e)(error_msg) from None

# =============================================================================
# 3. THE WORKERS (Generators)
# =============================================================================

def generate_plan_download_file_name(year: str, day: str, sat_id: str, product_id: str) -> str:
    """Generates standardized filename using progressive substitution."""
    ctx = "[fn01 - generate_plan_download_file_name]"
    template = "plan_01-download_[YEAR]_[DAY]_[SAT]_[POS]_[PROD].json"
    
    try:
        # Input validation
        validate_params(year=year, day=day, sat_id=sat_id, product_id=product_id)
        
        # Retrieve satellite info from naming_conventions.py
        sat_info = _get_sat_info(sat_id)
        
        # Build filename via string replacement
        name = template.replace("[YEAR]", str(year))
        name = name.replace("[DAY]", str(day).zfill(3))
        name = name.replace("[SAT]", f"GOES{sat_info['id']}")
        name = name.replace("[POS]", sat_info['pos'].upper())
        name = name.replace("[PROD]", product_id)
        return name
        
    except Exception as e:
        raise RuntimeError(f"\n{ctx} Filename generation failed:\n{str(e)}") from None

def generate_plan_download_file_path(
    year: str, 
    day: str, 
    sat_id: str, 
    product_id: str, 
    output_folder_base: str, 
    default_sub_folder: bool = True
) -> Path:
    """Resolves absolute path for a plan file and creates directories."""
    ctx = "[fn01 - generate_plan_download_file_path]"
    
    try:
        # Input validation
        validate_params(
            year=year, day=day, sat_id=sat_id, 
            product_id=product_id, output_folder_base=output_folder_base
        )
        
        base_dir = Path(output_folder_base)
        # Organize by /Year/Day/ format
        target_dir = base_dir / str(year) / str(day).zfill(3) if default_sub_folder else base_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        filename = generate_plan_download_file_name(year, day, sat_id, product_id)
        return target_dir / filename
        
    except Exception as e:
        raise RuntimeError(f"\n{ctx} Path resolution failed:\n{str(e)}") from None

# =============================================================================
# INITIALIZATION
# =============================================================================

# Run the guardian audit upon module import
_audit_interface_integrity()
