# =============================================================================
# FILE PATH: .../fn_action02/step02_update_dict_parts/update_dict04_summary.py
# Version: 1.9.8 (Self-Healing Dynamic Mapping)
# =============================================================================
from datetime import datetime

def update_dict04_summary(dict_plan: dict) -> dict:
    """
    Updates the summary. If 'status' or 'setup' are missing (old JSON), 
    it creates them on the fly to avoid KeyErrors.
    """
    inventory = dict_plan.get('inventory', {})
    total = len(inventory)
    
    if total == 0: 
        return dict_plan

    # 1. Conteo dinámico
    done = sum(1 for item in inventory.values() if item.get('tracking', {}).get('is_done_proc'))
    ready = sum(1 for item in inventory.values() if item.get('tracking', {}).get('is_ready_to_proc'))

    # 2. ASEGURAR ESTRUCTURA (Self-Healing)
    # Si Action 01 falló en crear las llaves, las creamos aquí.
    if 'summary' not in dict_plan:
        dict_plan['summary'] = {}
    
    if 'status' not in dict_plan['summary']:
        dict_plan['summary']['status'] = {}
        
    if 'setup' not in dict_plan['summary']:
        dict_plan['summary']['setup'] = {}

    # 3. Inyección de datos segura
    status = dict_plan['summary']['status']
    status.update({
        "is_all_done": (done == total),
        "progress_percentage": f"{round((done/total)*100, 2)}%",
        "readiness_percentage": f"{round((ready/total)*100, 2)}%",
        "files_total": total,
        "files_processed": done,
        "files_ready_to_process": ready,
        "files_pending_process": total - done,
        "files_waiting_for_download": total - ready
    })
    
    dict_plan['summary']['setup'].update({
        "last_summary_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    return dict_plan
