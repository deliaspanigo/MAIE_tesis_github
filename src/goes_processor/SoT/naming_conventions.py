"""
Path: src/goes_processor/SoT/naming_conventions.py
Version: 0.3.5
Description: Master Naming Engine for MAIE Tesis 2026.
             Standardizes filenames for local storage and processing.
"""

from pathlib import Path
from .goes_sat import get_sat_info
from .goes_prod import SAVED_INFO_PROD_GOES

# ===================================================================
# CONFIGURATION & LEVELS
# ===================================================================
PRODUCT_LEVELS = {
    "l1b": {"prefix": "SP", "code_short": "L1b"},
    "l2":  {"prefix": "SP", "code_short": "L2"},
    "l3":  {"prefix": "SP", "code_short": "L3"}
}

# ===================================================================
# INTERNAL HELPERS
# ===================================================================

def _get_sat_position_from_sot(sat_id: str) -> str:
    """Internal helper to fetch the official position (EAST/WEST)."""
    sat_data = get_sat_info(sat_id)
    return sat_data["pos"]

# ===================================================================
# NAMING CORE LOGIC
# ===================================================================

def generate_name_part01(level_key: str, sat_id: str) -> str:
    """
    Generates: SP-LEVEL_GOESXX-POSITION
    Example: SP-L2_GOES19-EAST
    """
    ctx = "[SoT - naming_conventions.py - generate_name_part01()]"
    try:
        l_key = str(level_key).lower()
        if l_key not in PRODUCT_LEVELS:
            lvl = {"prefix": "SP", "code_short": l_key.upper()}
        else:
            lvl = PRODUCT_LEVELS[l_key]
        
        sat_data = get_sat_info(sat_id)
        return f"{lvl['prefix']}-{lvl['code_short']}_GOES{sat_data['id']}-{sat_data['pos']}"
    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n")

def generate_name_part02(product_id: str, timestamp_goes: str) -> str:
    """
    Generates: PRODUCT_DATE-TIME
    Example: ABI-L2-LSTF_2026062-1400
    """
    clean_prod = str(product_id).upper().strip()
    t = str(timestamp_goes)
    # Formato: YYYYDDD-HHMM
    formatted_time = f"{t[0:7]}-{t[7:11]}" 
    return f"{clean_prod}_{formatted_time}"

def generate_name_part03(sat_id: str, fn_code: str = None, crs_mode: str = "WGS84", suffix: str = "RAW", ext: str = "nc") -> str:
    """
    Generates the metadata block: [FN]_CRS-MODE_SUFFIX.EXT
    """
    parts = []
    if fn_code:
        parts.append(str(fn_code).upper())

    pos = _get_sat_position_from_sot(sat_id)
    mode = str(crs_mode).upper().strip()

    if mode == "NATIVE":
        parts.append(f"CRS-GOES-{pos}")
    else:
        clean_mode = mode.replace("CRS-", "")
        parts.append(f"CRS-{clean_mode}")

    parts.append(str(suffix).upper())
    clean_ext = str(ext).lower().replace(".", "").strip()
    
    return f"{'_'.join(parts)}.{clean_ext}"

# ===================================================================
# MASTER INTERFACE
# ===================================================================

def get_full_filename(level: str, sat: str, prod: str, time: str, 
                      fn: str = None, crs: str = "WGS84", 
                      suffix: str = "RAW", ext: str = "nc") -> str:
    """
    Universal entry point: [PART01]_[PART02]_[PART03]
    """
    p1 = generate_name_part01(level, sat)
    p2 = generate_name_part02(prod, time)
    p3 = generate_name_part03(sat, fn, crs, suffix, ext)
    
    return f"{p1}_{p2}_{p3}"

# ===================================================================
# BRIDGE FOR OLD ACTIONS (The "Fixer")
# ===================================================================

def _get_sat_info(sat_id: str):
    """
    ⚠️ DEPRECATED: This is a bridge for actions v.0.3.4.
    Redirects to the new centralized goes_sat.get_sat_info.
    """
    return get_sat_info(sat_id)
