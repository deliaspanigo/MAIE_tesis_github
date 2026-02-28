# =============================================================================
# FILE PATH: .../a02_planning/core01_planner_download/fn01_file_name_plan_download.py
# Version: 0.1.8 (Dual-Layer Guard)
# =============================================================================

# 1. CAPA DE SISTEMA (Standard Libraries)
try:
    from pathlib import Path
    import re
except ImportError as e:
    print("\n" + "!"*80)
    print(f" [Planning - Core01 Planner Downloaod - fn01_file_name_plan_download.py]")
    print(f" Critical Python libraries missing: {e}")
    print(f" [SYSTEM LIB ERROR] - Critical Python libraries missing: {e}")
    print(" Check your Python installation or venv.")
    print("!"*80 + "\n")
    raise SystemExit(1)

# 2. CAPA DE PROYECTO (Your Module: goes_processor)
try:
    from goes_processor.SoT.goes_hardcoded_folders import get_my_path
    from goes_processor.SoT.goes_sat import get_satellite_info, AVAILABLE_GOES_SAT_POSITIONS
    from goes_processor.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError as e:
    print("\n" + "="*80)
    print(f" [Planning - Core01 Planner Downloaod - fn01_file_name_plan_download.py]")
    print(f" [PROJECT LIB ERROR] - Internal module 'goes_processor' not found: {e}")
    print("="*80)
    print(" Ensure you are running the script from the project root (MAIE_tesis_github).")
    print(" Ensure 'src' is in your PYTHONPATH.")
    print("="*80 + "\n")
    raise SystemExit(1)

# ===================================================================
# INTERNAL CONTROLS
# ===================================================================

def _validate_filename_params(year: str, day: str, sat_id: str, sat_position: str, product_id: str):
    """Internal control for filename components."""
    ctx = "[CONTROL][fn01_file_name_plan_download.py - _validate_filename_params()]"
    
    if not re.match(r'^\d{4}$', str(year)):
        raise ValueError(f"{ctx} Invalid year: {year}")
    
    # Permitimos días de 1 a 3 dígitos (ej: '5' -> '005')
    if not re.match(r'^\d{1,3}$', str(day)) or not (1 <= int(day) <= 366):
        raise ValueError(f"{ctx} Invalid Julian day: {day}")

    if str(sat_position).lower() not in AVAILABLE_GOES_SAT_POSITIONS:
        raise ValueError(f"{ctx} Invalid position: {sat_position}. Use: {AVAILABLE_GOES_SAT_POSITIONS}")

    if product_id not in AVAILABLE_GOES_PRODUCTS:
        raise ValueError(f"{ctx}\n Product {product_id} not found in SoT.\n")

# ===================================================================
# PUBLIC INTERFACE
# ===================================================================

def get_plan_download_file_name(year: str, day: str, sat_id: str, sat_position: str, product_id: str) -> str:
    """Generates consistent filename for download plans."""
    ctx = "[Planning - get_plan_download_file_name()]"
    
    try:
        _validate_filename_params(year, day, sat_id, sat_position, product_id)
        
        # Obtenemos info del satélite (esto valida el sat_id de paso)
        sat_info = get_satellite_info(sat_id)
        sat_display_name = sat_info["name06"]
        
        day_str = str(day).zfill(3)
        return f"plan_01_download_{year}_{day_str}_{sat_display_name}_{sat_position}_{product_id}.json"

    except (ValueError, KeyError) as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: {e}\n") from None

def get_plan_download_file_path(year: str, day: str, sat_id: str, sat_position: str, product_id: str) -> Path:
    """Returns the full absolute path and ensures directory exists."""
    ctx = "[Planning - get_plan_download_file_path()]"
    
    try:
        base_dir = get_my_path("data_plan")
        day_str = str(day).zfill(3)
        
        # Subestructura temporal: /data_plan/YEAR/DAY/
        target_dir = base_dir / year / day_str
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_name = get_plan_download_file_name(year, day, sat_id, sat_position, product_id)
        
        return target_dir / file_name

    except Exception as e:
        raise ValueError(f"\n[CRITICAL]{ctx}: Failed to resolve path: {e}\n") from None
