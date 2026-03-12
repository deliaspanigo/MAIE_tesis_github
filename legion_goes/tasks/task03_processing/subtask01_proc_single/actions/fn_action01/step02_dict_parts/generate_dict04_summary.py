# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action01/step02_dict_parts/generate_dict04_summary.py
# Version: 1.8.0 (Adapted for Processing Task 03)
# =============================================================================
import os
from pathlib import Path
from datetime import datetime

def generate_dict(dict_proc_inventory: dict) -> dict:
    """
    Generates a summary for the Processing Plan, calculating progress based 
    on the status of the inventory generated in step 03.
    """
    total_files = len(dict_proc_inventory)
    
    if total_files == 0:
        raise ValueError("Processing Inventory is empty")
    
    # 1. Calculate Statistics
    # We check the 'is_done' status of each record in the proc_inventory
    files_processed = sum(1 for item in dict_proc_inventory.values() if item["status"]["is_done"])
    progress_pct = round((files_processed / total_files) * 100, 2) if total_files > 0 else 0
    
    # 2. Extract Root Output Folder
    # We take the parent of the first file's output folder to get the day-level root
    first_key = next(iter(dict_proc_inventory))
    sample_output_folder = Path(dict_proc_inventory[first_key]["output_ref"]["output_folder"])
    
    # Usually: .../product/year/day/hour/fnp_tag -> we want the day or product root
    # For summary purposes, the absolute path of the first entry's parent is useful
    root_output_abs = sample_output_folder.parent.parent # Returns the 'day' level
    
    # 3. Current timestamp
    time_now = datetime.now()
    time_now_format = time_now.strftime("%Y-%m-%d %H:%M:%S")
    
    the_dict = {
        "is_all_done": files_processed == total_files,
        "total_files_in_plan": total_files,
        "total_files_already_processed": files_processed,
        "progress_percentage": f"{progress_pct}%",
        "root_output_directory": str(root_output_abs),
        "last_summary_update": time_now_format,
        "execution_tag": "v.0.0.1"
    }
    
    return the_dict

# ===================================================================
# MAIN EXECUTION - Diagnostic
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: GENERATE PROCESSING SUMMARY ".center(80, "="))

    # Fake inventory based on your Dict 03 structure
    mock_inventory = {
        "proc_single_001": {
            "status": {"is_done": True},
            "output_ref": {"output_folder": "/data/proc/ABI/2026/070/00/fnp01"}
        },
        "proc_single_002": {
            "status": {"is_done": False},
            "output_ref": {"output_folder": "/data/proc/ABI/2026/070/01/fnp01"}
        }
    }

    try:
        summary = generate_dict(mock_inventory)
        
        print(f"📊 Progress: {summary['progress_percentage']}")
        print(f"📁 Root:     {summary['root_output_directory']}")
        print(f"✅ Done:     {summary['is_all_done']}")
        
        print("\nFull Summary Dictionary:")
        for k, v in summary.items():
            print(f"   {k:<30}: {v}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

    print("=" * 80 + "\n")
