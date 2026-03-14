"""
Path: legion_goes/tasks/task02_download/actions/fn_act02/step02_update_dict_parts/update_dict04_summary.py
Version: 1.8.3
Description: Summary update logic using Hard/Soft branches and 'is_done_file' tracking.
"""
import os
import json
from datetime import datetime

def update_dict04_summary(dict_plan: dict) -> dict:
    """High-level analysis of the plan status based on the new tracking architecture."""
    
    # 1. Guard & Setup
    if 'summary' not in dict_plan:
        # Esto no debería pasar si la Action 01 corrió bien, pero por seguridad:
        return dict_plan
        
    inventory = dict_plan.get('inventory', {})
    summary = dict_plan.get('summary', {})
    
    # Aseguramos que existan las ramas hard/soft
    if 'hard' not in summary: summary['hard'] = {}
    if 'soft' not in summary: summary['soft'] = {}

    total_expected = len(inventory)
    
    # 2. Analytics: Contamos los archivos que realmente pasaron la auditoría
    # IMPORTANTE: Ahora buscamos 'is_done_file' en la rama 'tracking'
    done_count = sum(1 for item in inventory.values() 
                     if item.get('tracking', {}).get('is_done_file', False))
    
    # 3. Calculate metrics
    completion_percentage = round((done_count / total_expected * 100), 2) if total_expected > 0 else 0.0
    missing_count = total_expected - done_count
    is_fully_done = (done_count == total_expected)
    
    # 4. Update Summary SOFT (The Reality)
    summary['soft'].update({
        'is_done_day': is_fully_done,
        'local_total_files': done_count,
        'missing_files': missing_count,
        'progress_percentage': completion_percentage,
        'time_last_mod': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status_tag': "COMPLETE" if is_fully_done else "IN_PROGRESS"
    })
    
    # 5. Update Summary HARD (The Promise - just in case)
    summary['hard']['expected_total_files'] = total_expected
    
    # Log de feedback
    print(f"    [SUMMARY UPDATE] {summary['soft']['status_tag']}: {completion_percentage}% ({done_count}/{total_expected})")
    
    return dict_plan
