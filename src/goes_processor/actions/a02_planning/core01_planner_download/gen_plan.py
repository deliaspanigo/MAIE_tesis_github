# =============================================================================
# FILE PATH:
# src/goes_processor/actions/a02_planning/core01_planner_download/gen_plan.py
#
# Purpose: Generic download planner for GOES L2 products.
# Generates a single JSON-compatible download plan for one product and one satellite position.
# Does NOT handle "ALL" (that is CLI responsibility) and does NOT save files.
# The plan is mutable during generation (regular dict), sealed with StrictDict in the CLI if needed.
# =============================================================================

from datetime import datetime
from pathlib import Path

from goes_processor.HARDCODED_FOLDERS import get_my_path
from goes_processor.info.goes_sat import get_goes_id_by_date, get_satellite_info, get_goes_bucket
from goes_processor.info.goes_prod import GOES_PRODUCTS


def generate_download_plan_day(
    product_id: str,
    year: str,
    day: str,
    sat_position: str = "east"
) -> dict:
    """
    Generates a single download plan for one GOES L2 product and one satellite position.

    Parameters:
        product_id   : str → "ABI-L2-LSTF", "ABI-L2-MCMIPF", etc. (no "ALL")
        year         : str → "2026"
        day          : str → "003" (Julian day)
        sat_position : str → "east" or "west" (default "east")

    Returns:
        dict → Single plan structure
    """
    if product_id not in GOES_PRODUCTS:
        raise ValueError(f"Product '{product_id}' not found in GOES_PRODUCTS")

    prod_config = GOES_PRODUCTS[product_id]

    sat_id = get_goes_id_by_date(year, day, sat_position=sat_position)
    sat_info = get_satellite_info(sat_id)

    if not sat_info:
        raise ValueError(f"No satellite info found for {sat_id} on {year}-{day} ({sat_position})")

    bucket = sat_info["bucket"]
    day_str = str(day).zfill(3)

    # Cadence (used for reference and slot generation)
    cadence = prod_config.get("cadence_full_disk", prod_config.get("cadence", "10 minutes"))

    # Use the pre-defined number of files per day (from config, no calculation)
    expected_files = prod_config["total_files_one_day"]

    # For slot generation (minutes per hour), use cadence as fallback
    if "10minutes" in cadence.lower():
        minutes = [f"{m:02d}" for m in range(0, 60, 10)]
    elif "20seconds" in cadence.lower():
        minutes = [f"{m:02d}" for m in range(0, 60, 20)]
    else:  # default 1 hour or coarser (LSTF)
        minutes = ["00"]

    hours = [f"{h:02d}" for h in range(24)]
    total_slots = len(hours) * len(minutes)

    # Calculate max digits for pos_file formatting (e.g., 2 for 24, 3 for 144)
    max_digits = len(str(expected_files))

    # Date info
    try:
        date_obj = datetime.strptime(f"{year}-{day_str}", "%Y-%j")
        date_gregorian = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid day '{day_str}' for year {year}")

    prod_info = {
        "satellite": f"GOES-{sat_id}",
        "product": product_id,
        "bucket": bucket,
        "year": year,
        "day": day_str,
        "date_julian": f"{year}{day_str}",
        "date_gregorian": date_gregorian,
        "resolution": prod_config.get("resolution_nominal", "N/A (point-based)"),
        "expected_total_files_one_day": expected_files,
        "time_lapse": cadence,
        "sat_position": sat_position
    }

    planner_download_info = {
        "file_name": None,
        "path_relative": None,
        "path_absolute": None,
        "generated_at": datetime.now().isoformat()
    }

    inventory_files = {}
    counter = 1

    # Product-specific regex base
    regex_map = {
        "ABI-L2-LSTF":   f"OR_ABI-L2-LSTF-M6_G{sat_id}",
        "ABI-L2-MCMIPF": f"OR_ABI-L2-MCMIPF-M6_G{sat_id}",
        "ABI-L2-FDCF":   f"OR_ABI-L2-FDCF-M6_G{sat_id}",
        "GLM-L2-LCFA":   f"OR_GLM-L2-LCFA_G{sat_id}",
    }
    base_regex = regex_map.get(product_id, f"OR_*L2-*M6_G{sat_id}")

    # Determine if we need hour subfolder in regex
    use_hour_subfolder = "10minutes" in cadence.lower() or "20seconds" in cadence.lower()

    for h_str in hours:
        for m_str in minutes:
            time_id = f"{year}{day_str}{h_str}{m_str}"
            s_time = f"s{time_id}"
            file_key = f"file{counter:0{max_digits}d}"  # Consistent with pos_file

            # Path prefix (with or without hour subfolder)
            if use_hour_subfolder:
                path_prefix = f"{bucket}/{product_id}/{year}/{day_str}/{h_str}"
            else:
                path_prefix = f"{bucket}/{product_id}/{year}/{day_str}"

            # Flexible timestamp: match any timestamp starting with sYYYYDDDHH[MM]
            time_pattern = f"{year}{day_str}{h_str}" if not use_hour_subfolder else time_id

            regex_pattern = f"{path_prefix}/{base_regex}_s{time_pattern}*.nc"

            inventory_files[file_key] = {
                "pos_file": f"{counter:0{max_digits}d} of {expected_files:0{max_digits}d}",
                "year": year,
                "day": day_str,
                "hour": h_str,
                "minute": m_str,
                "s_time": s_time,
                "mini_summary": {
                    "is_ready": True,
                    "is_done": False,
                    "time_last_mod": None
                },
                "file_s3": {
                    "regex": regex_pattern,
                    "file_name": None,
                    "file_exists_web": False,
                    "file_size_mb_web": None,
                },
                "file_local": {
                    "regex": regex_pattern,
                    "file_name": None,
                    "path_relative": None,
                    "path_absolute": None,
                    "file_exists_local": False,
                    "file_size_mb_local": None,
                },
                "folder_local": {
                    "path_relative": None,
                    "path_absolute": None,
                    "folder_exists_local": False,
                }
            }
            counter += 1

    summary_info = {
        "is_done": False,
        "total_files_expected": expected_files,
        "total_files_ready": None,
        "total_files_downloaded": None,
        "total_time": None,
        "total_size_mb": None,
        "time_file_creation": datetime.now().isoformat(),
        "time_last_mod": None
    }

    return {
        "prod_info": prod_info,
        "planner_download_info": planner_download_info,
        "download_inventory": inventory_files,
        "summary": summary_info,
    }
