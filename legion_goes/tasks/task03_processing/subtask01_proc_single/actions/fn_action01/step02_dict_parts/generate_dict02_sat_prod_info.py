"""
Path: legion_goes/tasks/task03_processing/subtask01_proc_single/actions/fn_action01/step02_dict_parts/generate_dict02_sat_prod_info.py
Version: 1.5.1
Description: Folder structure: .../day/HH/sYYYYJJJHHMM/fnp_tag/
             Añadido soporte para parámetro 'overwrite'.
"""

import json
from datetime import datetime
from pathlib import Path

# Localizadores y generadores
from legion_goes.tasks.task02_download.actions.fn_act01.generate_dict_plan_download      import generate_dict_plan_download
from legion_goes.tasks.task02_download.actions.fn_utils.generate_plan_download_file_path import generate_plan_download_file_path






def get_dict_plan_proc_single(int, sat_id: str, product_id: str, year: str, day: str, fnp_tag: str):
    """
    LÓGICA PURA: Construye el plan con rutas: HH -> sTimestamp -> fnp_tag.
    """
    
    # 01. Tacking download details as base for proc_single
    dict_plan_download = generate_dict_plan_download(sat_id = sat_id,  product_id = product_id, year=year, day=day)
    plan_download_file_path = generate_plan_download_file_path(sat_id=sat_id, product_id=product_id, year=year, day=day)
    plan_download_file_name = str(Path(plan_download_file_path).name)
    
    
    
    sat_prod_info = base_download.get('sat_prod_info', {})
    download_summary = base_download.get('summary', {})
    download_inventory = base_download.get('download_inventory', {})
    
    bucket = sat_prod_info.get('bucket_name', 'unknown_bucket')
    str_year = str(year)
    str_day = str(day).zfill(3)
    
    proc_single_inventory = {}

    # 2. Construcción del inventario
    for i, (fid, info) in enumerate(download_inventory.items(), 1):
        init_name = info['file_local']['init_name']
        timestamp = info['time_stamp']  # Formato YYYYJJJHHMM
        hour_folder = timestamp[7:9]    # Extraemos HH
        
        new_fid = f"proc_single{str(i).zfill(3)}"
        
        # --- Lógica de Carpetas v.1.5.0 ---
        # Estructura: f02_processed / bucket / product / year / day / HH / sYYYYJJJHHMM / fnp_tag
        base_path_proc = Path(output_folder_base).parent / "f02_processed"
        
        deep_folder_path = (
            base_path_proc / 
            bucket / 
            product_id / 
            str_year / 
            str_day / 
            hour_folder /         # Primero la Hora
            f"s{timestamp}" /     # Luego el Timestamp con 's'
            fnp_tag               # Finalmente el Tag del proceso
        )
        
        # 3. Inicializar diccionarios por atributos (Columnas)
        file_names = {}
        paths_absolute = {}
        paths_relative = {}
        files_exists = {}

        for out_key, out_template in dict_output_names.items():
            final_filename = out_template.replace("{init_name}", init_name).replace("{fnp_tag}", fnp_tag)
            final_path_abs = deep_folder_path / final_filename
            
            file_names[out_key] = final_filename
            paths_absolute[out_key] = str(final_path_abs.resolve())
            paths_relative[out_key] = str(final_path_abs).split('f02_processed/')[-1] if 'f02_processed/' in str(final_path_abs) else None
            files_exists[out_key] = final_path_abs.exists()

        proc_single_inventory[new_fid] = {
            "pos_file": info['pos_file'],
            "time_stamp": timestamp,
            "status": {
                "is_ready_to_proc": False, 
                "is_done": False,
                "error": None
            },
            "input_ref": {
                "regex": None,
                "file_name": None,
                "path_absolute": None,
                "path_relative": None,
                "file_exists": False
            },
            "output_ref": {
                "file_names": file_names,
                "paths_absolute": paths_absolute,
                "paths_relative": paths_relative,
                "files_exists": files_exists,
                "output_folder": str(deep_folder_path.resolve())
            }
        }

    return {
        "plan_proc_single_self_info": {
            "file_name": None,
            "path_absolute": None,
            "path_relative": None,
            "timestamp_creation": None,
            "fnp_tag": fnp_tag
        },
        "sat_prod_info": sat_prod_info,
        "summary": download_summary,
        "proc_single_inventory": proc_single_inventory
    }

def gen_and_save_plan_proc_single(year: int, day: int, sat_pos: str, product_id: str, 
                                  output_folder_base: str, 
                                  dict_output_names: dict,
                                  fnp_tag: str = "default_rgb",
                                  overwrite: bool = False):
    """
    ORQUESTADOR: Persiste el plan en disco con el nuevo orden HH -> sTimestamp.
    """
    
    # Obtener la ruta donde se guardará el plan
    path_plan_proc = get_plan_proc_single_file_path(str(year), str(day).zfill(3), sat_pos, product_id, fnp_tag)

    # Lógica de Overwrite: Si el archivo existe y overwrite es False, no recalculamos.
    if path_plan_proc.exists() and not overwrite:
        print(f"⚠️  [SKIP] El plan ya existe y overwrite=False en: {path_plan_proc.name}")
        return path_plan_proc

    dict_plan = get_dict_plan_proc_single(
        year, day, sat_pos, product_id, output_folder_base, dict_output_names, fnp_tag
    )
    
    dict_plan["plan_proc_single_self_info"].update({
        "file_name": path_plan_proc.name,
        "path_absolute": str(path_plan_proc.resolve()),
        "path_relative": str(path_plan_proc).split('src/')[-1] if 'src/' in str(path_plan_proc) else str(path_plan_proc),
        "timestamp_creation": datetime.now().isoformat()
    })

    path_plan_proc.parent.mkdir(parents=True, exist_ok=True)
    with open(path_plan_proc, 'w', encoding='utf-8') as f:
        json.dump(dict_plan, f, indent=4)

    print(f"🎯 [SUCCESS] Plan v.1.5.1 saved (Overwrite: {overwrite}).")
    print(f"    Structure: .../{str(day).zfill(3)}/HH/sTimestamp/{fnp_tag}/")
    return path_plan_proc
