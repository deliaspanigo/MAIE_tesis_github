
# src/goes_processo/HARDCODED_FOLDERS.py

import os
from pathlib import Path

# Anchor everything to the project root: MAIE_tesis_github
# Structure: src/goes_processor/HARDCODED_FOLDERS.py -> 3 levels up to reach root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Dictionary with dynamic paths based on the project root
_FOLDERS = {
    "data_raw": BASE_DIR / "data_raw" / "goes_raw",
    "plan_download": BASE_DIR / "data_planner" / "p01_download",
    "plan_processing": BASE_DIR / "data_planner" / "p02_processing",
    
  
    "proc_core01": BASE_DIR / "data_processed" / "a02_processing" / "core01_proc_one_file",
    "proc_core02": BASE_DIR / "data_processed" / "a02_processing" / "core02_proc_accumulate",
}

def get_my_path(key, *subfolders):
    """
    Returns the absolute path, ensures the directory exists, 
    and allows adding dynamic subfolders.
    
    Example: get_my_path("data_raw", "noaa-goes19", "2026", "003")
    """
    base = _FOLDERS.get(key)
    if not base:
        raise KeyError(f"The key '{key}' is not defined in HARDCODED_FOLDERS")
    
    # joinpath handles multiple arguments to build the full tree
    final_path = base.joinpath(*subfolders)
    
    # Automatically create the folder structure if it doesn't exist
    final_path.mkdir(parents=True, exist_ok=True)
    
    return final_path
