"""
Path: legion_goes/tasks/task02_download/actions/fn_act01/step02_dict_parts/generate_dict04_summary.py
Version: 1.8.2
Description: Refactored to map from definition -> local_folder_info -> hard.
"""
import json
from pathlib import Path
from datetime import datetime

def generate_dict(dict_inventory: dict) -> dict:
    """
    Generates a summary dictionary from the inventory using the 
    hardcoded paths in the new definition structure.
    """
    if not dict_inventory:
        raise ValueError("Inventory is empty")

    total_files = len(dict_inventory)
    
    # 1. Acceso a la primera entrada para extraer metadatos de ruta
    first_key = next(iter(dict_inventory))
    the_first = dict_inventory[first_key]
    
    # 2. ACCESO ACTUALIZADO v.1.8.2: definition -> local_folder_info -> hard
    local_hard = the_first.get("definition", {}).get("local_folder_info", {}).get("hard", {})
    rel_path_str = local_hard.get("folder_path_relative")
    abs_path_str = local_hard.get("folder_path_absolute")
    
    
    if not rel_path_str or not abs_path_str:
        raise KeyError(f"Missing 'hard' path info in definition for key: {first_key}")

    rel_path = Path(rel_path_str)
    abs_path = Path(abs_path_str)
    
    # Subimos un nivel: de la carpeta de la hora (00, 01...) a la carpeta del día
    folder_path_day_rel = rel_path.parent
    folder_path_day_abs = abs_path.parent
    
    # Timestamp de generación
    time_now_format = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 3. Construcción del summary
    the_dict = {
        "hard": {
            "expected_total_files": total_files,
            "output_folder_day_relative": str(folder_path_day_rel),
            "output_folder_day_absolute": str(folder_path_day_abs),

        },
        "soft": {
            "is_done_day": None,
            "local_total_files": None,
            "time_last_mod": time_now_format,
            "status_tag": "INITIALIZED"
        }
    }
    
    return the_dict

# ===================================================================
# MAIN EXECUTION (Solo el Diccionario Completo)
# ===================================================================
if __name__ == "__main__":
    # Simulación de inventario v.1.8.2
    example_inventory = {
        "file001": {
            "definition": {
                "local_folder_info": {
                    "hard": {
                        "folder_path_relative": "noaa-goes19/ABI-L2-LSTF/2026/003/00",
                        "folder_path_absolute": "/home/legion/bulk/data_raw/noaa-goes19/ABI-L2-LSTF/2026/003/00"
                    }
                }
            }
        }
    }

    try:
        summary = generate_dict(example_inventory)
        print(json.dumps(summary, indent=4))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=4))
