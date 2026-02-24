import json
import os
import time
import s3fs
from pathlib import Path
from datetime import datetime

# --- PRODUCT CONFIGURATION ---
PRODUCT_STRATEGY = {
    "ABI-L2-LSTF":   {"desc": "Land Surface Temperature"},
    "ABI-L2-MCMIPF": {"desc": "Cloud and Moisture Imagery"},
    "ABI-L2-FDCF":   {"desc": "Fire - Hot Spot Characterization"},
    "GLM-L2-LCFA":   {"desc": "Lightning Detection"},
}

def get_goes_satellite_id(year, day):
    try:
        date_obj = datetime.strptime(f"{year}-{str(day).zfill(3)}", "%Y-%j")
        if date_obj.year < 2025 or (date_obj.year == 2025 and date_obj.month < 4):
            return "16"
        return "19"
    except:
        return "16"

def run_plan_download(year, day, product, hour, minute, base_folder_planner, output_root, overwrite=False, check_again=False):
    """
    v.0.7.5 - Clean version with optimized S3 retrieval.
    """
    target_product = product.upper()
    fs = s3fs.S3FileSystem(anon=True)
    
    sat_id = get_goes_satellite_id(year, day)
    bucket_name = f"noaa-goes{sat_id}"
    str_year = str(year)
    str_day = str(day).zfill(3)
    
    # 1. Locate Planner JSON
    planner_dir = Path(base_folder_planner) / bucket_name / str_year / str_day
    filename_json = f"planner_download_{str_year}_{str_day}_{target_product}.json"
    full_json_path = planner_dir / filename_json
    
    if not full_json_path.exists():
        print(f"\n⚠️  Plan not found: {full_json_path}")
        return

    with open(full_json_path, 'r', encoding='utf-8') as f:
        planner_data = json.load(f)

    p_info = planner_data.get("planner_download_info", {})
    all_files = planner_data.get("download_files", {})
    
    filtered_files = {
        k: v for k, v in all_files.items() 
        if (hour.upper() == "ALL" or str(v.get("hour")).zfill(2) == hour.zfill(2)) and
           (minute.upper() == "ALL" or str(v.get("minutes")).zfill(2) == minute.zfill(2))
    }

    if not filtered_files:
        return 

    total_to_process = len(filtered_files)
    padding = len(str(total_to_process))

    print(f"\n🚀 SATELLITE DOWNLOADER | {target_product}")
    print(f"{'='*80}")
    print(f"🛰️  Satellite: GOES-{sat_id} | Date: {str_year}-{str_day}")
    print(f"📡 Status: Syncing with Amazon S3 server...")
    
    rel_folder = Path(bucket_name) / target_product / str_year / str_day
    local_dir = Path(output_root) / rel_folder
    local_dir.mkdir(parents=True, exist_ok=True)

    # --- HOURLY CACHE LOGIC ---
    s3_hour_cache = {} 

    def get_s3_hour_content(h_str):
        if h_str in s3_hour_cache: return s3_hour_cache[h_str]
        s3_hour_path = f"{bucket_name}/{target_product}/{str_year}/{str_day}/{h_str}/"
        try:
            items = fs.ls(s3_hour_path, detail=True)
            s3_hour_cache[h_str] = {os.path.basename(item['name']): item['size'] for item in items}
            return s3_hour_cache[h_str]
        except:
            return {}

    count_downloaded = 0
    count_exists = 0
    total_size_mb = 0
    start_time_job = time.time()

    # --- PROCESSING LOOP ---
    for idx, (file_key, info) in enumerate(filtered_files.items(), 1):
        h_str = str(info.get("hour")).zfill(2)
        s_time_pattern = info.get("s_time")
        
        hour_content = get_s3_hour_content(h_str)
        match_name = next((name for name in hour_content if s_time_pattern in name), None)
        
        if not match_name:
            continue

        size_web_mb = round(hour_content[match_name] / (1024 * 1024), 2)
        local_path = local_dir / match_name
        
        should_download = True
        if local_path.exists() and not overwrite:
            size_local = round(os.path.getsize(local_path) / (1024 * 1024), 2)
            if not check_again or size_local == size_web_mb:
                should_download = False

        if should_download:
            print(f"  [{str(idx).zfill(padding)}/{str(total_to_process).zfill(padding)}] ⬇️  Downloading: {match_name} | {size_web_mb} MB")
            s3_full_path = f"{bucket_name}/{target_product}/{str_year}/{str_day}/{h_str}/{match_name}"
            fs.get(s3_full_path, str(local_path))
            count_downloaded += 1
        else:
            count_exists += 1

        # Always update metadata
        f_size_final = round(os.path.getsize(local_path) / (1024 * 1024), 2)
        total_size_mb += f_size_final
        info.update({
            "file_name": match_name,
            "path_relative": str(rel_folder / match_name),
            "path_absolute": str(local_path.absolute()),
            "file_exist_local": True,
            "file_size_mb_web": size_web_mb,
            "file_size_mb_local": f_size_final,
            "is_check": True
        })

    # --- FINAL AUDIT AND SAVE ---
    p_info["time_last_mod"] = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - System time"
    total_local_in_plan = sum(1 for f in all_files.values() if f.get("file_exist_local", False))
    
    if hour.upper() == "ALL" and minute.upper() == "ALL":
        p_info["is_done"] = (total_local_in_plan == len(all_files))

    with open(full_json_path, 'w', encoding='utf-8') as f:
        json.dump(planner_data, f, indent=4, ensure_ascii=False)
    
    duration = round(time.time() - start_time_job, 2)
    print(f"\n  ✅ PROCESS COMPLETED:")
    print(f"     - Pre-existing: {count_exists}/{total_to_process}")
    print(f"     - Downloaded:   {count_downloaded}/{total_to_process}")
    print(f"     - Total Local:  {total_local_in_plan}/{len(all_files)}")
    print(f"     - Total Size:   {round(total_size_mb, 2)} MB")
    print(f"     - Duration:     {duration}s")
    print(f"{'='*80}\n")
