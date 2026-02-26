# =============================================================================
# FILE PATH: src/goes_processor/utils/file_names.py
# Purpose: Centralized utility for generating consistent file names and paths.
# MODIFICATION: Now uses 'name06' (e.g., GOES19) from goes_sat.py for filenames.
# =============================================================================

from pathlib import Path
from goes_processor.HARDCODED_FOLDERS import get_my_path
from goes_processor.info.goes_sat import get_satellite_info

def get_plan_file_name(
    year: str,
    day: str,
    sat_id: str,
    sat_position: str,
    product_id: str
) -> str:
    """
    Generates consistent filename for download plans using formal satellite names.
    Format: plan_download_YYYY_DDD_GOESXX_pos_PRODUCT.json
    
    Parameters:
        year: str → "2026"
        day: str → "003"
        sat_id: str → "19" (ID used to lookup name06)
        sat_position: str → "east" or "west"
        product_id: str → "ABI-L2-LSTF"
    """
    # 🛡️ Lookup the formal name (name06) from our Source of Truth
    sat_info = get_satellite_info(sat_id)
    sat_display_name = sat_info["name06"] if sat_info else f"GOES{sat_id}"
    
    day_str = str(day).zfill(3)
    
    # Example output: plan_download_2026_003_GOES19_east_ABI-L2-LSTF.json
    return f"plan_download_{year}_{day_str}_{sat_display_name}_{sat_position}_{product_id}.json"


def get_plan_path(
    year: str,
    day: str,
    sat_id: str,
    sat_position: str,
    product_id: str,
    create_dir: bool = True
) -> Path:
    """
    Returns the full absolute path for the plan file.
    """
    base_dir = get_my_path("plan_download")
    
    day_str = str(day).zfill(3)
    target_dir = base_dir / year / day_str
    
    if create_dir:
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # 🔄 This now calls the updated version with name06
    file_name = get_plan_file_name(year, day, sat_id, sat_position, product_id)
    return target_dir / file_name
