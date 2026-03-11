"""
Path: legion_goes/code/python_sp/sp001_single/f02_executor/check_all_path_exists_from_dict.py
Version: 1.0.0
Description: Utility to verify the physical existence of multiple files from a dictionary mapping.
"""

from pathlib import Path
from typing import Dict, Any

def check_all_path_exists_from_dict(dict_output: Dict[Any, str], verbose: bool = True) -> bool:
    """
    Checks if all files defined in the output dictionary exist on disk.
    
    Args:
        dict_output (dict): A dictionary where values are file paths (str or Path).
        verbose (bool): If True, prints missing files to the console.
        
    Returns:
        bool: True if ALL files exist, False if at least one is missing or dict is empty.
    """
    if not dict_output:
        if verbose:
            print("      ⚠️ [PATH CHECK] Warning: Empty output dictionary provided.")
        return False

    # Identify missing files by checking disk existence
    missing_files = [
        Path(file_path).name for file_path in dict_output.values() 
        if not Path(file_path).exists()
    ]
    
    if missing_files:
        if verbose:
            total_missing = len(missing_files)
            # Create a clean summary string for the first 3 missing items
            preview = ", ".join(missing_files[:3])
            suffix = f" (and {total_missing - 3} more...)" if total_missing > 3 else ""
            print(f"      🔍 [MISSING] {preview}{suffix}")
        return False

    return True
