# =============================================================================
# FILE PATH: src/legion_goes/SoT/goes_hardcoded_folders.py
# Version: 0.2.2 (LEGION-GOES Passive & Library-Ready)
# =============================================================================

import os
from pathlib import Path
from types import MappingProxyType

# ===================================================================
# LOGIC: DYNAMIC ROOT DETECTION
# ===================================================================

def _resolve_working_root() -> Path:
    """
    Decides the root for data storage (The Workspace).
    Priority: 1. ENV Variable | 2. Current Working Directory (CWD)
    """
    return Path(os.getenv("LEGION_PROJECT_ROOT", os.getcwd())).resolve()

def _get_library_source_root() -> Path:
    """
    Finds where the actual .py code is located (The Library).
    Used for internal assets like satpy_cache or config files.
    """
    # Path: src/legion_goes/SoT/file.py -> SoT -> legion_goes -> src (3 levels)
    return Path(__file__).resolve().parent.parent.parent

# --- ACTIVE ROOTS ---
LEGION_DATA_ROOT = _resolve_working_root()
LEGION_SRC_ROOT = _get_library_source_root()

# ===================================================================
# PRIVATE SOURCE OF TRUTH (Dictionary Factory)
# ===================================================================

def _generate_folder_map(root: Path) -> dict:
    """
    Builds the LEGION folder map. 
    Most paths are relative to the execution 'root' (Workspace).
    Internal paths are relative to the library 'src' (Package).
    """
    return {
        "root": root,
        "data_raw": root / "data_raw",
        "data_plan": root / "data_plan",
        "data_proc": root / "data_proc",
        
        # Processing (Internal structure for processed data)
        "proc_single": root / "data_proc" / "proc01_single",
        "proc_aggregated": root / "data_proc" / "proc02_aggregated",
        
        # Support and System
        "reports": root / "reports",
        "logs": root / "reports" / "logs",
        
        # SPECIAL: Cache lives inside the installed package to persist LUTs
        #"satpy_cache": LEGION_SRC_ROOT / "legion_goes" / "satpy_cache",
        #"tests_labs": root / "tests" / "labs",
    }

# Official map loaded at startup based on current execution context
_FOLDERS = _generate_folder_map(LEGION_DATA_ROOT)
GOES_FOLDERS = MappingProxyType(_FOLDERS)

# ===================================================================
# PUBLIC INTERFACE
# ===================================================================

def get_my_path(key: str, create: bool = False, custom_root: Path = None) -> Path:
    """
    Returns the absolute Path for a LEGION-GOES key.
    
    Args:
        key (str): The folder key (e.g., 'data_raw').
        create (bool): If True, physically creates the directory. Defaults to False.
        custom_root (Path, optional): Forces a different workspace root (Sandbox mode).
    """
    ctx = "[LEGION-GOES SoT - get_my_path()]"
    
    try:
        # Use detected data root or a personalized one (for testing)
        target_map = _generate_folder_map(Path(custom_root)) if custom_root else GOES_FOLDERS

        path = target_map.get(key)
        
        if not path:
            raise KeyError(f"Key '{key}' not found. Valid keys: {list(target_map.keys())}")
        
        # PASSIVE LOGIC: Only create directory if explicitly requested
        if create and key != "root":
            path.mkdir(parents=True, exist_ok=True)
        
        return path

    except Exception as e:
        # Propagate error with context for debugging
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None

# ===================================================================
# SELF-TEST (LEGION-GOES Health Check)
# ===================================================================
if __name__ == "__main__":
    print(f"\n" + "="*75)
    print(f" LEGION-GOES SYSTEM - SoT v.0.2.2 (Passive Mode)")
    print(f" Execution/Data Root: {LEGION_DATA_ROOT}")
    print(f" Library Source:      {LEGION_SRC_ROOT}")
    print(f"="*75)
    
    for k, v in GOES_FOLDERS.items():
        # In this self-test, we check existence without creating
        status = "✅ EXISTS" if v.exists() else "🚀 MISSING (Ready to create)"
        print(f" {status.ljust(25)} | {k.ljust(12)} -> {v}")
    
    print("="*75)
    print(" NOTE: Run 'LEGION-GOES run' to trigger physical folder creation.\n")
