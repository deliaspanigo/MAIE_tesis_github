# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_act02/step02_update_dict_parts/update_dict04_summary.py
# Version: 1.7.1 (Fixed Imports, Return Variable & Guard)
# =============================================================================
import os
import json
from datetime import datetime # <--- FIX 1: Missing Import

def update_dict04_summary(dict_plan: dict) -> dict:
    """High-level analysis of the plan status."""
    
    # Guard: Ensure summary exists
    if 'summary' not in dict_plan:
        dict_plan['summary'] = {}
        
    inventory = dict_plan.get('inventory', {})
    total_expected = dict_plan['summary'].get('expected_total_files', len(inventory))
    
    # Calculate how many files are actually downloaded/ready
    found_count = sum(1 for item in inventory.values() if item['status'].get('is_done'))
    
    # Update summary metadata
    dict_plan['summary'].update({
        'local_total_files': found_count,
        'is_done': (found_count == total_expected),
        'check_last_run': datetime.now().strftime("%Y-%m-%d %H:%M:%S") # <--- Now works
    })
    
    # FIX 2: Return the correct variable name (was plan_data)
    return dict_plan
