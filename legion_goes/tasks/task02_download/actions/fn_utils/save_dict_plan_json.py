# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_utils/save_dict_plan_json.py
# Version: 1.1.0 (Robust Directory Creation)
# =============================================================================
import json
import os
from pathlib import Path

# --- 1. ATOMIC I/O ---

def save_dict_plan_json(dict_plan: dict, path_json: str):
    """
    Saves the download plan dictionary to a JSON file.
    Automatically creates parent directories if they don't exist.
    """
    
    the_path = Path(path_json)
    
    try:
        # 1. Crear directorios padres si no existen (mkdir -p)
        # parents=True crea toda la cadena, exist_ok=True evita error si ya existe
        the_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 2. Guardar el archivo
        with open(the_path, 'w', encoding='utf-8') as f:
            json.dump(dict_plan, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        # Error ruidoso para debug en Jupyter/Script
        error_msg = (
            f"\n" + "!"*80 + "\n"
            f"[CRITICAL ERROR] Failed to save plan JSON.\n"
            f"Target Path: {the_path.absolute()}\n"
            f"Detail: {e}\n"
            f"!"*80
        )
        raise RuntimeError(error_msg) from None
