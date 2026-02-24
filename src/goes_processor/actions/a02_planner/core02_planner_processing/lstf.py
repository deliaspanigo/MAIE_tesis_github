# src/goes_processor/actions/a02_planner/core02_planner_processing/lstf.py

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
    
    # Transition Logic: GOES-19 became the primary East satellite in early 2025
    if date_obj.year < 2025 or (date_obj.year == 2025 and date_obj.month < 4):
        return "16"
    return "19"

def gen_plan_processing_ONE_DAY_LSTF(year, day, dict_plan_download_LSTF):
    # 1. Formatting and Satellite selection
    sat = get_goes_satellite(year, day)
    day_str = str(day).zfill(3)
    product = "ABI-L2-LSTF"
    bucket = f"noaa-goes{sat}"
    str_folder_year_day = f"{bucket}/{product}/{year}/{day_str}"
    str_folder_planner = f"{bucket}/{year}/{day_str}"
    
    # 2. Convert Day of Year to Gregorian Date (YYYY-MM-DD)
    try:
        date_obj = datetime.strptime(f"{year}-{day_str}", "%Y-%j")
        date_gregorian = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return f"Error: Day {day_str} is invalid for year {year}."
    
    # 3. Initialize Inventory Structure
    inventory = {
        "satellite": f"GOES-{sat}",
        "product": product,
        "year": year,
        "day_of_year": day_str,
        "date_gregorian": date_gregorian,
        "is_done": False,
        "str_folder_year_day": str_folder_year_day,
        "str_folder_planner": str_folder_planner,
        "utc_sys_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "sys_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z"), # Local system time
        "files": {} 
    }
    
    # 4. Generate 24-hour slots
    hours = [f"{h:02d}" for h in range(24)]
    minutes = ["00"] 
    total_slots = len(hours) * len(minutes)
    counter = 1
    
    for h_str in hours:
        for m_str in minutes:
            # Timestamp used in file names (e.g., s20260031200)
            time_id = f"{year}{day_str}{h_str}{m_str}"
            s_time = f"s{time_id}"
            
            file_key = f"file{str(counter).zfill(2)}"
            pos_label = f"{str(counter).zfill(2)} of {str(total_slots).zfill(2)}"
            
            # S3 Search Pattern
            regex_pattern = f"{bucket}/{product}/{year}/{day_str}/{h_str}/OR_ABI-L2-LSTF-*{s_time}*.nc"
            
            inventory["proc"][file_key] = {
                "pos_proc": pos_label,
                "hour": h_str,
                "minutes": m_str,
                "s_time": s_time,
                list_input_files = {
                input_file01 = {
                "path_relative": None,
                "path_absolute": None,
                "file_exists": False}},
                list_output_files = {
                output_file01 = {
                "path_relative": None,
                "path_absolute": None,
                "file_exists": False}},
                output_file02 = {
                "path_relative": None,
                "path_absolute": None,
                "file_exists": False}

            }
            counter += 1
            
    return inventory


