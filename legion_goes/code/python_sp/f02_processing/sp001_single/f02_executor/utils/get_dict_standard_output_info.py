"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/run_executor_proc_single.py
Version: 0.0.1
Description: Main orchestrator for single product processing. 
             Fixed SyntaxErrors and added diagnostic main.
"""

import time
import json
from pathlib import Path

# --- IMPORTING ISOLATED STEPS ---
# Asegúrate de que estas rutas de importación sean correctas en tu entorno

from legion_goes.code.python_sp.f02_processing.sp001_single.f02_executor.utils.get_folder_full_path_proc_single import get_folder_full_path_proc_single
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_executor.utils.get_elements_from_FNP import get_elements_from_FNP

def get_dict_standard_output_info(sat_id="16", product_id="ABI-L2-MCMIPF", year=None, day=None, s_timestamp_short=None, fnp_tag="fnp01"):
    """
    Orchestrates metadata and path resolution.
    """
    # 0. Initial Input Validation

    # --- STEP 01: OUTPUT CONFIGURATION ---
    str_output_folder_path_abs = get_folder_full_path_proc_single(
        sat_id=str(sat_id), 
        product_id=product_id, 
        year=year, 
        day=day, 
        s_timestamp_short=s_timestamp_short, 
        fnp_tag=fnp_tag
    )
    
    if not str_output_folder_path_abs: 
        return None
    
    # --- STEP 02: DYNAMIC IMPORT ---
    bag_fnp = get_elements_from_FNP(
        product_id=product_id, fnp_tag=fnp_tag, 
        list_expected=['dict_output_schema', 'fnp_python_code']
    )
    
    # Fix Case Sensitivity (bag_FNP vs bag_fnp)
    if not bag_fnp or not bag_fnp.get('fnp_python_code'): 
        return None

    dict_output_init_name = bag_fnp['dict_output_schema']
    
    # --- STEP 2.5: OUTPUT PATH MAPPING ---
    # Usamos el nombre del archivo original (stem) para reemplazar el template si es necesario
    #init_name = Path(nc_path).stem
    
    dict_output_file_name = dict_output_init_name.copy()  # Evitar modificar el original
    
    dict_output_file_path = {
        k: str(Path(str_output_folder_path_abs) / v) 
        for k, v in dict_output_file_name.items()
    }
    

    dict_output_file_exists = {
        key: Path(file_path).exists() 
        for key, file_path in dict_output_file_path.items()
    }
    
    
    # FIX: Usar ':' en lugar de '=' para el diccionario de retorno
    return {
        "bag_fnp": bag_fnp,
        "str_output_folder_path_abs": str_output_folder_path_abs,
        "dict_output_init_name": dict_output_init_name,
        "dict_output_file_name": dict_output_file_name,
        "dict_output_file_path": dict_output_file_path,
        "dict_output_file_exists": dict_output_file_exists
    }

# =============================================================================
# MAIN DIAGNOSTIC
# =============================================================================
if __name__ == "__main__":
    print("\n" + " LEGION-GOES: EXECUTOR DIAGNOSTIC ".center(80, "="))
    
    # 1. Simulación de parámetros de entrada
    test_params = {
        "sat_id": "16",
        "product_id": "ABI-L2-MCMIPF",
        "year": 2026,
        "day": 70,
        "s_timestamp_short": "s20260701200",
        "fnp_tag": "fnp01"
    }

    print("-" * 80)

    try:
        # 2. Ejecución de la lógica de información
        start_time = time.time()
        result_dict = get_dict_standard_output_info(**test_params)
        end_time = time.time()

        if result_dict:
            print(f"✅ [SUCCESS] Dictionary generated in {round(end_time - start_time, 4)}s")
            print("\n📂 Output Folder:")
            print(f"📍 {result_dict['str_output_folder_path_abs']}")
            
            print("\n📝 Output Files Mapping:")
            for key, path in result_dict['dict_output_file_path'].items():
                print(f"   🔹 {key}: {Path(path).name}")
                # print(f"      Full: {path}") # Descomentar para ver ruta completa
            
            print("\n⚙️  FNP Elements:")
            print(f"   Functions loaded: {result_dict['bag_fnp'].keys()}")
        else:
            print("❌ [FAILED] Could not generate output information.")

    except Exception as e:
        print(f"❌ [CRITICAL ERROR] Diagnostic failed:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80 + "\n")
