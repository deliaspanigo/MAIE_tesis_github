# =============================================================================
# FILE PATH: legion_goes/code/python_sp/f99_common/load_dict_plan_from_json_file.py
# Version: 1.1.0 (Robust Directory Creation)
# =============================================================================

import json
import os
from pathlib import Path

# --- 1. ATOMIC I/O ---

def load_dict_plan_from_json_file(path_json: str) -> dict:
    """
    Loads the download plan JSON file.
    Returns the dict if success, raises FileNotFoundError if missing.
    """
    # Convertimos a Path y nos aseguramos de tener la ruta absoluta para el log
    the_path = Path(path_json).resolve()
    
    if not the_path.exists():
        # En lugar de return None, lanzamos un error descriptivo
        error_msg = (
            f"\n" + "!"*80 + "\n"
            f"[CRITICAL ERROR] Plan file not found.\n"
            f"Target Path: {the_path}\n"
            f"CWD: {os.getcwd()}\n"
            f"Check if action01_create_json was executed first."
            f"\n" + "!"*80
        )
        raise FileNotFoundError(error_msg)

    try:
        with open(the_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data is None:
                raise ValueError(f"File at {the_path} is empty.")
            return data
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON at {the_path}: {e}")
