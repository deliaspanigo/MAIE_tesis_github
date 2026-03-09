"""
Path: src/legion_goes/task/task03_processing/subtask01_proc_single/actions/action02_check_plan_proc_single.py
Version: 1.4.4
Description: Procedural integrity check. Fixed parameter mapping for Task 02 (SoT).
"""

import json
from pathlib import Path
from datetime import datetime

# Localizadores
from .fn01_file_name_plan_proc_single import get_plan_proc_single_file_path
from legion_goes.task.task02_download.actions.fn01_file_name_plan_download import get_plan_download_file_path

def execute_check_integrity_proc_single(path_plan_proc: Path, path_plan_download: Path):
    """
    Sincroniza y verifica físicamente los archivos. 
    Actualiza el JSON in-place. No devuelve nada.
    """
    if not path_plan_proc.exists() or not path_plan_download.exists():
        print(f"❌ [ERROR] Plan no encontrado:\nProc: {path_plan_proc.exists()}\nDown: {path_plan_download.exists()}")
        return

    # 1. Cargar planes
    with open(path_plan_proc, 'r', encoding='utf-8') as f:
        plan_proc = json.load(f)
    with open(path_plan_download, 'r', encoding='utf-8') as f:
        plan_down = json.load(f)

    proc_inventory = plan_proc.get("proc_single_inventory", {})
    down_inventory = plan_down.get("download_inventory", {})
    
    # Mapa de búsqueda por timestamp del plan de descarga (Source of Truth)
    down_map = {info['time_stamp']: info for info in down_inventory.values()}

    count_ready = 0

    # 2. Iterar y Verificar
    for fid, proc_item in proc_inventory.items():
        ts = proc_item["time_stamp"]
        
        if ts in down_map:
            down_item = down_map[ts]
            file_local = down_item.get("file_local", {})
            abs_path_str = file_local.get("path_absolute")
            
            if abs_path_str:
                path_to_check = Path(abs_path_str)
                
                # VERIFICACIÓN FÍSICA REAL EN DISCO
                if path_to_check.exists() and path_to_check.is_file():
                    proc_item["input_ref"].update({
                        "file_name": file_local.get("file_name_real"),
                        "path_absolute": abs_path_str,
                        "path_relative": file_local.get("path_relative"),
                        "file_exists": True
                    })
                    proc_item["status"]["is_ready_to_proc"] = True
                    proc_item["status"]["error"] = None
                    count_ready += 1
                else:
                    proc_item["input_ref"]["file_exists"] = False
                    proc_item["status"]["is_ready_to_proc"] = False
                    proc_item["status"]["error"] = "PHYSICAL_FILE_MISSING"
            else:
                proc_item["status"]["error"] = "NO_PATH_IN_DOWNLOAD_PLAN"
        else:
            proc_item["status"]["error"] = "TIMESTAMP_NOT_FOUND_IN_SOT"

    # 3. Actualizar metadatos del resumen
    plan_proc["summary"]["total_ready"] = count_ready
    plan_proc["summary"]["last_audit"] = datetime.now().isoformat()

    # 4. Persistencia
    with open(path_plan_proc, 'w', encoding='utf-8') as f:
        json.dump(plan_proc, f, indent=4)

def run_integrity_check_by_params(year: int, day: int, sat_pos: str, product_id: str, fnp_tag: str):
    """
    Orquestador: Resuelve rutas y dispara el chequeo.
    Mapeo corregido para Task 02: (year, day, sat_id, product_id)
    """
    str_year = str(year)
    str_day = str(day).zfill(3)

    # A. Ruta Proceso (Task 03)
    path_proc = get_plan_proc_single_file_path(str_year, str_day, sat_pos, product_id, fnp_tag)
    
    # B. Ruta Descarga (Task 02) -> Ajustado a tu firma real en fn01_file_name_plan_download.py
    # Pasamos los argumentos por posición tal como los definiste
    path_down = get_plan_download_file_path(str_year, str_day, sat_pos, product_id)

    print(f"--- 🛠️  AUDITORÍA DE PROCESAMIENTO ---")
    print(f"📦 Plan: {path_proc.name}")
    
    execute_check_integrity_proc_single(path_proc, path_down)
    
    # C. Resumen independiente
    with open(path_proc, 'r') as f:
        res = json.load(f)
        ready = res["summary"]["total_ready"]
        total = len(res["proc_single_inventory"])
        print(f"📊 Resumen: {ready}/{total} archivos validados físicamente.")
        print(f"--------------------------------------")
