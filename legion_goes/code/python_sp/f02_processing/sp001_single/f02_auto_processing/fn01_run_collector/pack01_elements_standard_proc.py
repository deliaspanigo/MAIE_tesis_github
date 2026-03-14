# =============================================================================
# Path: legion_goes/code/python_sp/f02_processing/sp001_single/f02_auto_processing/fn01_run_collector/pack01_standard_proc.py
# Version: 1.0.6
# Description: Standard module loader. Prepares the FNP science function 
#              and its output paths for the generic executor.
# =============================================================================

import sys
import importlib
from pathlib import Path
from typing import Dict, Any, Optional

# NEW CENTRALIZED IMPORT PATH
from legion_goes.code.python_sp.f02_processing.sp001_single.utils.get_folder_full_path_proc_single import get_folder_full_path_proc_single

def pack01_standard_proc(
    sat_id: str,
    product_id: str, 
    year: int,
    day: int,
    s_timestamp_short: str,
    fnp_tag: str
) -> Optional[Dict[str, Any]]:
    """
    Assembles the 'BAG' for the main science processing (FNP).
    It collects the dynamic function and resolves all absolute output paths.
    """
    
    # 1. Module Path Normalization (e.g., ABI-L2-LSTF -> ABI_L2_LSTF)
    prod_id_mod = product_id.upper().replace('-', '_')
    module_path = f"legion_goes.code.python_sp.f02_processing.sp001_single.f01_code.{prod_id_mod}.{fnp_tag}.fn01_python_code"
    
    try:
        # 2. Dynamic Import
        if module_path in sys.modules:
            importlib.reload(sys.modules[module_path])
        fnp_mod = importlib.import_module(module_path)
        
        # 3. Contract Validation
        dict_output_schema = getattr(fnp_mod, "dict_output_schema", None)
        fnp_python_code = getattr(fnp_mod, "fnp_python_code", None)

        if not dict_output_schema or not fnp_python_code:
            raise AttributeError(f"Module {module_path} is missing required attributes.")

        # 4. Resolve the Base Output Folder (Source of Truth)
        str_output_folder_abs = get_folder_full_path_proc_single(
            sat_id=sat_id,
            product_id=product_id,
            year=year,
            day=day,
            s_timestamp_short=s_timestamp_short,
            fnp_tag=fnp_tag
        )

        if not str_output_folder_abs:
            raise ValueError("Could not generate absolute folder path.")

        # 5. Build Absolute File Paths
        dict_output_file_path = {
            key: str(Path(str_output_folder_abs) / filename)
            for key, filename in dict_output_schema.items()
        }

        # 6. Assemble the BAG
        # We follow the same pattern as Pack 02 and 03
        bag = {
            "fnp_python_code": fnp_python_code,
            "execution_kwargs": dict_output_file_path,  # This will be unpacked with **
            "meta": {
                "task_name": f"Standard Processing: {product_id}",
                "output_folder": str_output_folder_abs,
                "dict_output_file_name": dict_output_schema
            }
        }
        
        return bag

    except Exception as e:
        print(f"      ❌ [PACK01 ERROR] {e}")
        return None

# =============================================================================
# QUICK DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    # Test with standard parameters
    test_params = {
        "sat_id": "16",
        "product_id": "ABI-L2-MCMIPF",
        "year": 2026,
        "day": 3,
        "s_timestamp_short": "s20260031245",
        "fnp_tag": "fnp01"
    }
    
    print(f"Testing Pack01 Collector for {test_params['product_id']}...")
    res = pack01_standard_proc(**test_params)
    
    if res:
        print("✅ Pack01 BAG created successfully.")
        print(f"   Target function: {res['fnp_python_code'].__name__}")
        print(f"   Outputs count: {len(res['execution_kwargs'])}")
    else:
        print("❌ Pack01 creation failed.")
