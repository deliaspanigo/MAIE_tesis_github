# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action01/step02_dict_parts/generate_dict04_summary.py
# Version: 2.2.1 (Triple Pack Support)
# =============================================================================

import json
from typing import Dict, Any
from datetime import datetime

def generate_dict(dict_proc_inventory: Dict[str, Any]) -> Dict[str, Any]:
    """
    CORE LOGIC: Analyzes the inventory to produce a high-level progress report.
    Considers the readiness of the download and the completion of processing.
    """
    total_items = len(dict_proc_inventory)
    
    # Contadores de estado
    count_ready = 0    # Archivos descargados listos para procesar
    count_done = 0     # Procesamiento completado (is_done_proc)
    count_pending = 0  # Pendientes de descarga
    
    for item in dict_proc_inventory.values():
        track = item.get("tracking", {})
        
        # 1. ¿Está el NetCDF disponible para ser procesado?
        if track.get("is_ready_to_proc"):
            count_ready += 1
        else:
            count_pending += 1
            
        # 2. ¿Se ha marcado el procesamiento como finalizado?
        if track.get("is_done_proc"):
            count_done += 1

    # Cálculo de porcentajes
    progress = (count_done / total_items * 100) if total_items > 0 else 0.0
    download_readiness = (count_ready / total_items * 100) if total_items > 0 else 0.0

    # RETORNO CON ESTRUCTURA COMPLETA
    return {
        "status": {
            "is_all_done": (count_done == total_items and total_items > 0),
            "total_files_in_scope": total_items,
            "files_ready_to_process": count_ready,
            "files_waiting_for_download": count_pending,
            "files_completed": count_done,
            "progress_percentage": f"{round(progress, 2)}%",
            "readiness_percentage": f"{round(download_readiness, 2)}%"
        },
        "setup": {
            "last_summary_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "schema_version": "v.0.0.1", # Sincronizado con tu GitHub
            "architecture": "Triple-Pack (Science, Gallery, Metadata)"
        },
        "description": "High-level summary of the single-processing task status."
    }

if __name__ == "__main__":
    print("\n" + " UNIT TEST: GENERATE SUMMARY (v.2.2.1) ".center(80, "="))
    mock_inventory = {
        "proc_single_001": {"tracking": {"is_ready_to_proc": True, "is_done_proc": True}},
        "proc_single_002": {"tracking": {"is_ready_to_proc": True, "is_done_proc": False}},
    }
    summary = generate_dict(dict_proc_inventory=mock_inventory)
    print(json.dumps(summary, indent=4))
