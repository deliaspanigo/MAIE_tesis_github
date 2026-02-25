import os
import json
from datetime import datetime
from pathlib import Path

# --- My Libraries ---
from goes_processor.HARDCODED_FOLDERS import get_my_path

######################################################################################################
class StrictDict(dict):
    """
    Diccionario que impide la creación de nuevas llaves después de su inicialización.
    Mantiene la integridad de la estructura del producto.
    """
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = StrictDict(value)
        super().__init__(data)

    def __setitem__(self, key, value):
        if key not in self:
            raise KeyError(
                f"\n[STRICT ERROR] Attempted to add new key: '{key}'.\n"
                f"Only existing keys defined in the product template can be modified."
            )
        super().__setitem__(key, value)

######################################################################################################
# FUNCIONES AUXILIARES
######################################################################################################

def get_goes_satellite(year, day):
    """Determina el satélite (16 o 19) según la fecha de transición de NOAA."""
    date_obj = datetime.strptime(f"{year}-{str(day).zfill(3)}", "%Y-%j")
    if date_obj.year < 2025 or (date_obj.year == 2025 and date_obj.month < 4):
        return "16"
    return "19"

def get_str_file_path_json_planner_download(year, day, str_prod):
    """Busca recursivamente el JSON del planner de descarga."""
    internal_str_base_folder = get_my_path("plan_download")
    base_path = Path(internal_str_base_folder)
    target_filename = f"planner_download_{year}_{str(day).zfill(3)}_{str_prod.upper()}.json"
    results = list(base_path.rglob(target_filename))
    return str(results[0].absolute()) if results else None

######################################################################################################
# GENERADORES DE OUTPUTS POR FUNCIÓN (MODULAR)
######################################################################################################

def gen_dict_outputs_fn01(raw_file_name, bucket, product, year, day_str, path_proc_base):
    """
    Lógica encapsulada para fn01 con rutas absolutas y relativas.
    """
    if not raw_file_name or raw_file_name == "PENDING_DOWNLOAD":
        base = "UNKNOWN_LSTF_FILE"
    else:
        base = os.path.splitext(raw_file_name)[0]
    
    # 1. Definición de carpetas
    str_fn01_relative = f"{bucket}/{product}/{year}/{day_str}/fn01"
    path_fn01_absolute = path_proc_base / str_fn01_relative
    
    # 2. Diccionario de Nombres
    names = {
        "native_grey_png":  f"{base}_fn01_native_grey.png",
        "native_color_png": f"{base}_fn01_native_color.png",
        "wgs84_grey_png":   f"{base}_fn01_wgs84_grey.png",
        "wgs84_color_png":  f"{base}_fn01_wgs84_color.png",
        "wgs84_grey_tif":   f"{base}_fn01_wgs84_grey.tif",
        "wgs84_color_tif":  f"{base}_fn01_wgs84_color.tif"
    }
    
    # 3. Construcción de Rutas (Absolutas vs Relativas)
    # El relativo se calcula desde la ejecución actual (os.getcwd) o la raíz del proyecto
    dict_abs = {k: str(path_fn01_absolute / v) for k, v in names.items()}
    dict_rel = {k: os.path.relpath(path_fn01_absolute / v, start=os.getcwd()) for k, v in names.items()}
    
    return {
        "folder_relative": str_fn01_relative,
        "folder_absolute": str(path_fn01_absolute),
        "dict_file_name_fn01": names,
        "dict_file_path_absolute_fn01": dict_abs,
        "dict_file_path_relative_fn01": dict_rel,
        "dict_file_exists_fn01": {k: False for k in names.keys()},
        "is_done": False
    }

######################################################################################################
# PLANNER PRINCIPAL
######################################################################################################

def gen_plan_processing_ONE_DAY_LSTF(year, day):
    sat = get_goes_satellite(year, day)
    day_str = str(day).zfill(3)
    product = "ABI-L2-LSTF"
    bucket = f"noaa-goes{sat}"
    
    # AQUÍ EL CAMBIO CLAVE: Usamos proc_core01
    path_proc_base = Path(get_my_path("proc_core01"))
    
    download_json_path = get_str_file_path_json_planner_download(year, day, product)
    if not download_json_path: return None
    with open(download_json_path, 'r', encoding='utf-8') as f:
        download_data = json.load(f)

    processing_files = {}
    for file_key, d_info in download_data["download_files"].items():
        raw_file_name = d_info.get("file_name") or "PENDING_DOWNLOAD"
        
        processing_files[file_key] = {
            "pos_file": d_info["pos_file"],
            "time_metadata": {
                "hour": d_info["hour"], "minutes": d_info["minutes"], "s_time": d_info["s_time"]
            },
            "inputs": {
                "raw_nc": {
                    "file_name": raw_file_name,
                    "path_relative": d_info["path_relative"],
                    "path_absolute": d_info["path_absolute"],
                    "ready": d_info.get("file_exist_local", False)
                }
            },
            "outputs": {
                "fn01": gen_dict_outputs_fn01(raw_file_name, bucket, product, year, day_str, path_proc_base)
            }
        }

    return {
        "prod_info": download_data["prod_info"],
        "summary": {
            "is_done": False,
            "total_files": len(download_data["download_files"]),
            "time_file_creation": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - System time",
            "time_last_mod": None
        },
        "processing_files": processing_files
    }
