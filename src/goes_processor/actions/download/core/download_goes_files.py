# src/goes_processor/actions/download/download.py

import fsspec
from pathlib import Path
import os
import shutil
from typing import List
import socket
import time
from datetime import datetime

def check_internet_connection():
    """Checks if there is an active internet connection."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def download_goes_files(
    satellite: str,
    product: str,
    year: str,
    day_of_year: str,
    hour: str,
    minute: str,
    overwrite: bool,
    output_dir: str
) -> List[Path]:
    """
    Downloads GOES NetCDF files directly from NOAA S3 bucket.
    """
    
    start_time_process = time.time()
    system_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n[*] System started at: {system_start_time}")
    
    if not check_internet_connection():
        print("\n" + "!"*60 + "\n[!] ERROR: NO INTERNET ACCESS.\n" + "!"*60)
        return []

    bucket_name = f"noaa-goes{satellite}"
    # Initialize S3 filesystem
    fs = fsspec.filesystem('s3', anon=True)
    
    # Construct S3 path prefix
    path_prefix = f"{bucket_name}/{product}/{year}/{day_of_year.zfill(3)}"
    if hour != "all":
        path_prefix += f"/{hour.zfill(2)}"

    print(f"[*] Scanning S3 path: s3://{path_prefix}")
    
    try:
        all_files = fs.glob(f"{path_prefix}/**/*.nc")
    except Exception as e:
        print(f"[!] Error accessing S3 bucket: {e}")
        return []

    # Filter by minute if specified
    if minute != "all":
        time_match = f"s{year}{day_of_year.zfill(3)}{hour.zfill(2)}{minute.zfill(2)}"
        files_to_download = [f for f in all_files if time_match in f]
    else:
        files_to_download = all_files

    total_files = len(files_to_download)
    if total_files == 0:
        print(f"[!] No files were found matching the criteria.")
        return []

    print(f"[*] Found {total_files} files.")

    # Padding for progress counter
    padding = max(len(str(total_files)), 2)
    downloaded_paths = []
    
    for i, remote_file in enumerate(files_to_download, 1):
        filename = remote_file.split('/')[-1]
        hour_folder = remote_file.split('/')[-2]
        
        # Local path structure: output_dir/bucket/product/year/day/hour/file
        local_path = Path(output_dir) / bucket_name / product / year / day_of_year.zfill(3) / hour_folder / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)

        remote_size = fs.size(remote_file)
        progress_label = f"[{i:0{padding}d}/{total_files:0{padding}d}]"

        # Integrity Check
        if local_path.exists():
            local_size = local_path.stat().st_size
            if local_size == remote_size:
                if not overwrite:
                    print(f"   {progress_label} [OK - EXISTS] {filename} ({local_size/(1024**2):.1f} MB)")
                    downloaded_paths.append(local_path)
                    continue
            else:
                print(f"   {progress_label} [CORRUPT] Size mismatch ({local_size} != {remote_size}). Retrying...")
                local_path.unlink()

        # Download Process
        print(f"   {progress_label} [DOWNLOADING] {filename}...")
        try:
            with fs.open(remote_file, 'rb') as rf, open(local_path, 'wb') as lf:
                shutil.copyfileobj(rf, lf)
            
            if local_path.stat().st_size == remote_size:
                print(f"         └─> [DONE] {local_path.stat().st_size/(1024**2):.1f} MB")
                downloaded_paths.append(local_path)
            else:
                print(f"         └─> [!] ERROR: Final file size is incorrect.")
        except Exception as e:
            print(f"         └─> [!] NETWORK ERROR: {e}")
            if local_path.exists(): local_path.unlink()

    print(f"\n[*] PROCESS COMPLETED in {(time.time() - start_time_process)/60:.2f} minutes")
    return downloaded_paths
