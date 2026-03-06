"""
Path: src/legion_goes/task/task03_processing/subtask01_proc_single/actions/fn02_proc_single_catalog.py
Version: 2.1.3
Description: Orquestador Maestro Multi-Producto con log detallado: [001/XXX] proc-single-fnpXX --- PRODUCTO --- FILE
"""

import json
import gc
from pathlib import Path
from datetime import datetime

# --- IMPORTACIONES DE ACCIONES BASE ---
try:
    from actions.action01_gen_plan_proc_single import gen_and_save_plan_proc_single
    from actions.action02_check_plan_proc_single import run_integrity_check_by_params
    
    # --- IMPORTACIONES POR PRODUCTO (Alias: producto_fnpXX_...) ---
    
    # 1. PRODUCTO: MCMIPF (Cloud & Moisture Imagery)
    from actions.fnp.ABI_L2_MCMIPF_SP_single_fnp01.code_python_proc_single import (
        execute_fnp_processing as mcmipf_fnp01_func, 
        dict_output_schema as mcmipf_fnp01_dict, 
        verify_fnp_interface as mcmipf_fnp01_verify
    )
    from actions.fnp.ABI_L2_MCMIPF_SP_single_fnp02.code_python_proc_single import (
        execute_fnp_processing as mcmipf_fnp02_func, 
        dict_output_schema as mcmipf_fnp02_dict, 
        verify_fnp_interface as mcmipf_fnp02_verify
    )

except ImportError as e:
    print(f"❌ Error de importación en Action03: {e}")
    raise

# =============================================================================
# 1. CATÁLOGO MAESTRO DE PRODUCTOS
# =============================================================================
CATALOGO_PRODUCTOS = {
    "MCMIPF": {
        "full_name": "ABI-L2-MCMIPF",
        "fnps": {
            "fnp01": {
                "id": "fnp01", 
                "func": mcmipf_fnp01_func, 
                "schema": mcmipf_fnp01_dict,
                "verifier": mcmipf_fnp01_verify
            },
            "fnp02": {
                "id": "fnp02", 
                "func": mcmipf_fnp02_func, 
                "schema": mcmipf_fnp02_dict,
                "verifier": mcmipf_fnp02_verify
            }
        }
    }
}
