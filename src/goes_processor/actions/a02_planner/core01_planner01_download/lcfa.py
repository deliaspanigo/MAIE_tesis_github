# src/goes_processor/actions/a02_planner/core01_p01_download/lcfa.py

import s3fs
import os
import json
from datetime import datetime, timezone

def get_goes_satellite(year, day):
    """
    Determines the correct satellite based on the GOES-16 to GOES-19 
    transition which occurred around April 2025.
    """
    date_obj = datetime.strptime(f"{year}-{day}", "%Y-%j")
    if date_obj.year < 2025 or (date_obj.year == 2025 and date_obj.month < 4):
        return "16"
    return "19"

def gen_plan_download_ONE_DAY_LCFA(year, day):
    # 1. Basic Config
    sat = get_goes_satellite(year, day)
    day_str = str(day).zfill(3)
    product = "GLM-L2-LCFA"
    bucket = f"noaa-goes{sat}"
   
    # 2. Convert Julian Day to Gregorian Date
    try:
        date_obj = datetime.strptime(f"{year}-{day_str}", "%Y-%j")
        date_gregorian = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return f"Error: Day {day_str} is invalid for year {year}."
    
    # 3. Container: Product Metadata (prod_info)
    prod_info = {
        "satellite": f"GOES-{sat}",
        "product": product,
        "bucket": bucket,
        "year": year,
        "day": day_str,
        "date_julian": f"{year}{day_str}",
        "date_gregorian": date_gregorian,
        "resolution": "8km"
    }

    # 4. Container: Planner Metadata (planner_download_info)
    planner_download_info = {
        "file_name": None,
        "path_relative": None,
        "path_absolute": None,
        "is_done": False,
        "time_file_creation": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - System time",
        "time_last_mod": None
    }
    
    # 5. Initialize File Inventory (High frequency: every 20 sec)
    inventory_files = {}
    hours = [f"{h:02d}" for h in range(24)]
    minutes = [f"{m:02d}" for m in range(0, 60)]
    seconds = [f"{s:02d}" for s in range(0, 60, 20)] # 00, 20, 40
    
    total_slots = len(hours) * len(minutes) * len(seconds) # 4320 slots
    counter = 1
    
    for h_str in hours:
        for m_str in minutes:
            for s_str in seconds:
                # The label used in the JSON (13 digits)
                time_id = f"{year}{day_str}{h_str}{m_str}{s_str}"
                s_time_label = f"s{time_id}"
                
                file_key = f"file{str(counter).zfill(4)}"
                
                # --- THE FIX ---
                # We add a '*' immediately after the seconds string (s_time).
                # This matches 's2026003000000' + '0' (the decisecond) or any other variation.
                # Example: OR_GLM-L2-LCFA-*s2026003000000*.nc
                regex_pattern = f"{bucket}/{product}/{year}/{day_str}/{h_str}/OR_GLM-L2-LCFA*{s_time_label}*.nc"

                
                inventory_files[file_key] = {
                    "pos_file": f"{str(counter).zfill(4)} of {str(total_slots).zfill(4)}",
                    "year": year,
                    "day": day_str,
                    "hour": h_str,
                    "minutes": m_str,
                    "seconds": s_str,
                    "s_time": s_time_label,
                    "regex": regex_pattern,
                    "file_name": None,
                    "path_relative": None,
                    "path_absolute": None,
                    "file_exist_local": False,
                    "file_size_mb_web": None,
                    "file_size_mb_local": None,
                    "file_size_mb_web": None,
                    "is_check": False
                }
                counter += 1
                
    # 6. Return Unified Dictionary
    return {
        "prod_info": prod_info,
        "planner_download_info": planner_download_info,
        "download_files": inventory_files
    }
