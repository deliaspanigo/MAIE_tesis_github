# =============================================================================
# FILE PATH:
# src/goes_processor/actions/a02_planning/core01_planner_download/check_plan.py
#
# Purpose: Checks local existence of files in a generated download plan.
# Updates mini_summary and summary with real local file status.
#
# Features:
#   - Uses full regex (including bucket) from data_raw/goes_raw root
#   - If multiple matches → takes the most recent by modification time
#   - Logs debug info for troubleshooting
#   - Updates mini_summary and summary
# =============================================================================

from datetime import datetime
from pathlib import Path
import glob

from goes_processor.HARDCODED_FOLDERS import get_my_path


def check_local_file_existence(plan: dict | list[dict]) -> dict | list[dict]:
    """
    Checks local existence of files in the download plan and updates mini_summary and summary.
    """
    if isinstance(plan, dict):
        plans = [plan]
    else:
        plans = plan

    updated_plans = []

    data_raw_root = get_my_path("data_raw") 
    print(f"DEBUG: data_raw_root = {data_raw_root}")
    print(f"DEBUG: data_raw_root exists? {data_raw_root.exists()}")

    for single_plan in plans:
        inventory = single_plan.get("download_inventory", {})
        local_exists_count = 0
        total_size = 0.0
        latest_mod_time = None

        product = single_plan["prod_info"].get("product", "unknown")
        year = single_plan["prod_info"].get("year", "unknown")
        day = single_plan["prod_info"].get("day", "unknown")
        bucket = single_plan["prod_info"].get("bucket", "unknown")

        print(f"\nDEBUG: Checking plan for {product} - {year}/{day} (bucket: {bucket})")

        for file_key, item in inventory.items():
            # Prefer absolute path if available
            abs_path_str = item["file_local"].get("path_absolute")
            found_path = None

            if abs_path_str:
                expected_path = Path(abs_path_str)
                print(f"DEBUG: Checking absolute path: {expected_path}")
                if expected_path.exists() and expected_path.is_file():
                    found_path = expected_path
                    print(f"DEBUG: Found via absolute path: {found_path}")
                else:
                    print(f"DEBUG: Absolute path not found: {expected_path}")

            # Fallback to regex search
            if found_path is None:
                regex = item["file_s3"].get("regex")
                if regex:
                    full_pattern = data_raw_root / regex
                    print(f"DEBUG: Searching with pattern: {full_pattern}")

                    candidates = glob.glob(str(full_pattern))
                    valid_candidates = [Path(p) for p in candidates if Path(p).is_file()]

                    print(f"DEBUG: Raw glob found {len(candidates)} candidates (valid files: {len(valid_candidates)})")
                    if valid_candidates:
                        print(f"DEBUG: First few candidates: {[p.name for p in valid_candidates[:3]]}")
                        found_path = max(valid_candidates, key=lambda p: p.stat().st_mtime if p.is_file() else 0)
                        print(f"DEBUG: Selected most recent: {found_path}")
                    else:
                        print("DEBUG: No valid file matches found")
                else:
                    print("DEBUG: No regex available")

            if found_path:
                item["mini_summary"]["is_ready"] = True
                item["mini_summary"]["is_done"] = True
                mtime = datetime.fromtimestamp(found_path.stat().st_mtime)
                item["mini_summary"]["time_last_mod"] = mtime.strftime("%Y-%m-%d %H:%M:%S")

                size_mb = round(found_path.stat().st_size / (1024 * 1024), 2)
                item["file_local"]["file_exists_local"] = True
                item["file_local"]["path_relative"] = str(found_path.relative_to(Path.cwd()))
                item["file_local"]["file_size_mb_local"] = size_mb
                item["file_local"]["path_absolute"] = str(found_path.resolve())

                folder_path = found_path.parent
                item["folder_local"]["path_relative"] = str(folder_path.relative_to(Path.cwd()))
                item["folder_local"]["path_absolute"] = str(folder_path.resolve())
                item["folder_local"]["folder_exists_local"] = folder_path.exists() and folder_path.is_dir()

                local_exists_count += 1
                total_size += size_mb

                if latest_mod_time is None or mtime > latest_mod_time:
                    latest_mod_time = mtime
            else:
                item["mini_summary"]["is_ready"] = True
                item["mini_summary"]["is_done"] = False
                item["mini_summary"]["time_last_mod"] = None

                item["file_local"]["file_exists_local"] = False
                item["file_local"]["path_relative"] = None
                item["file_local"]["file_size_mb_local"] = None
                item["file_local"]["path_absolute"] = None

                item["folder_local"]["path_relative"] = None
                item["folder_local"]["path_absolute"] = None
                item["folder_local"]["folder_exists_local"] = False

        # Update summary
        all_done = all(item["mini_summary"]["is_done"] for item in inventory.values())
        single_plan["summary"]["is_done"] = all_done
        single_plan["summary"]["total_files_ready"] = local_exists_count
        single_plan["summary"]["total_files_downloaded"] = local_exists_count

        if local_exists_count > 0:
            single_plan["summary"]["total_size_mb"] = round(total_size, 2)
            if latest_mod_time:
                single_plan["summary"]["time_last_mod"] = latest_mod_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            single_plan["summary"]["total_size_mb"] = None
            single_plan["summary"]["time_last_mod"] = None

        updated_plans.append(single_plan)

    return updated_plans[0] if isinstance(plan, dict) else updated_plans
