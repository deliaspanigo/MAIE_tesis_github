# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action01/step02_dict_parts/generate_dict03_inventory.py
# Version: 2.3.6 (Collector-Agnostic Mapping - English Version)
# =============================================================================

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# --- ABSOLUTE IMPORTS ---
from legion_goes.tasks.task02_download.actions.fn_act01.generate_dict_plan_download import generate_dict_plan_download
from legion_goes.code.python_sp.f02_processing.sp001_single.f02_auto_processing.fn01_run_collector.run_collector import run_collector

def map_bag_to_output_info(bag: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a Collector 'Bag' into the JSON 'Pack' structure.
    Dynamically extracts names and paths for the Auditor.
    """
    if not bag: return {}
    
    meta = bag.get('meta', {})
    schema = meta.get('dict_output_file_name', {})
    # Prioritize audit paths if they exist, otherwise use execution paths
    paths = bag.get('execution_kwargs_audit', bag.get('execution_kwargs', {}))
    
    return {
        "description": meta.get('task_name', "Unknown Task"),
        "hard": {
            "output_folder_absolute": meta.get('output_folder'),
            "list_files_names": schema,
            "list_files_paths": paths
        },
        "soft": { 
            "list_file_exists": {k: None for k in schema.keys()}, 
            "list_file_size": {k: None for k in schema.keys()}       
        }
    }

def generate_dict(sat_id: str, product_id: str, year: str, day: str, fnp_tag: str = "fnp01") -> Dict[str, Any]:
    """
    Builds the inventory by processing the 3 Packs from the execution plan.
    """
    dict_plan_download = generate_dict_plan_download(sat_id=sat_id, product_id=product_id, year=year, day=day) 
    download_inventory = dict_plan_download.get("inventory", {})
    
    if not download_inventory:
        return {}

    dict_proc_single_inventory = {}
    total = len(download_inventory)
    max_d = len(str(total))

    for i, (fid_down, info_down) in enumerate(download_inventory.items(), 1):
        defin_down = info_down.get('definition', {})
        track_down = info_down.get('tracking', {})
        sot_meta_down = defin_down.get('SOT_metadata', {})
        
        timestamp = sot_meta_down.get('timestamp')
        s_timestamp_short = f"s{timestamp}" if timestamp else None
        if not s_timestamp_short: continue

        # --- COLLECTOR CALL ---
        execution_plan = run_collector(
            sat_id=sat_id, product_id=product_id, 
            year=int(year), day=int(day), 
            s_timestamp_short=s_timestamp_short, fnp_tag=fnp_tag
        )
        
        # Validate that we have the 3 expected packs
        if not execution_plan or len(execution_plan) < 3:
            continue

        new_fid = f"proc_single_{str(i).zfill(max_d)}"
        
        dict_proc_single_inventory[new_fid] = {
            "definition": {
                "SOT_metadata": {
                    "key": new_fid,
                    "pos": f"{i:0{max_d}d}/{total:0{max_d}d}",
                    "fid_download_ref": fid_down,
                    "timestamp": timestamp,
                    "fnp_tag": fnp_tag
                },
                "input_info": {
                    "hard": {
                        "init_name": defin_down.get("s3_metadata", {}).get("hard", {}).get("init_name"),
                        "folder_path_absolute": defin_down.get('local_folder_info', {}).get('hard', {}).get("folder_path_absolute")
                    },
                    "soft": { "file_name": None, "file_path": None, "file_size_mb": 0, "file_exists": False }
                },
                "output_info": {
                    "pack01": map_bag_to_output_info(execution_plan[0]),
                    "pack02": map_bag_to_output_info(execution_plan[1]),
                    "pack03": map_bag_to_output_info(execution_plan[2])
                }
            },
            "tracking": {
                "is_ready_to_proc": track_down.get("is_done_file", False),
                "is_done_pack01": None,
                "is_done_pack02": None,
                "is_done_pack03": None,
                "is_done_proc": None,
                "error_log": None,
                "time_last_mod": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }

    return dict_proc_single_inventory
