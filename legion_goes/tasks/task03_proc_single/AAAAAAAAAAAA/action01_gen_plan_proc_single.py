import json
from datetime import datetime
from pathlib import Path

# Importamos tus generadores recién probados
from .fn01_file_name_plan_proc_single import generate_plan_proc_single_file_path

# Importamos el buscador del Task 02 para saber qué se descargó
from legion_goes.tasks.task02_download.actions.fn01_file_name_plan_download import generate_plan_download_file_path

def generate_dict_plan_proc_single(year: str, day: str, sat_id: str, product_id: str, 
                                  fnp_tag: str, dict_output_schema: dict,
                                  path_download_base: str):
    """
    LÓGICA MAESTRA: 
    1. Localiza el plan de descarga.
    2. Lee qué archivos .nc existen realmente.
    3. Construye el plan de procesamiento con rutas dinámicas.
    """
    
    # A. Localizar el Source of Truth (Plan de Descarga)
    path_plan_down = generate_plan_download_file_path(
        year=year, day=day, sat_id=sat_id, 
        product_id=product_id, output_folder_base=path_download_base
    )
    
    if not path_plan_down.exists():
        raise FileNotFoundError(f"❌ No se encontró plan de descarga en: {path_plan_down}")

    with open(path_plan_down, 'r') as f:
        plan_down = json.load(f)

    down_inventory = plan_down.get('download_inventory', {})
    sat_prod_info = plan_down.get('sat_prod_info', {})
    
    proc_inventory = {}

    # B. Mapeo de inventario
    for i, (fid, info) in enumerate(down_inventory.items(), 1):
        # Datos del archivo original
        ts = info['time_stamp']
        nc_local = info['file_local']
        
        # Generar ID de proceso único
        new_fid = f"proc_{ts}" 
        
        # --- Construcción de Rutas de Salida ---
        # Usamos la lógica de tu v.1.5.0: /f02_processed/bucket/product/year/day/HH/sTS/tag/
        # Pero esta vez, lo hacemos dinámico.
        
        hour_folder = ts[7:9]
        base_proc = Path(path_download_base).parent / "f02_processed"
        deep_path = (
            base_proc / sat_prod_info['bucket_name'] / product_id / 
            year / day.zfill(3) / hour_folder / f"s{ts}" / fnp_tag
        )

        # C. Generar nombres de salida basados en el esquema del FNP
        out_refs = {
            "file_names": {},
            "paths_absolute": {},
            "output_folder": str(deep_path.resolve())
        }

        for key, template in dict_output_schema.items():
            # Limpiamos el nombre original para el output
            clean_name = nc_local['init_name'].replace(".nc", "")
            f_name = template.replace("{init_name}", clean_name).replace("{fnp_tag}", fnp_tag)
            
            out_refs["file_names"][key] = f_name
            out_refs["paths_absolute"][key] = str(deep_path / f_name)

        proc_inventory[new_fid] = {
            "time_stamp": ts,
            "status": {"is_ready_to_proc": False, "is_done": False, "error": None},
            "input_ref": {
                "file_name": nc_local['file_name_real'],
                "path_absolute": nc_local['path_absolute'],
                "file_exists": Path(nc_local['path_absolute']).exists() if nc_local['path_absolute'] else False
            },
            "output_ref": out_refs
        }

    return {
        "plan_info": {"fnp_tag": fnp_tag, "created_at": datetime.now().isoformat()},
        "sat_prod_info": sat_prod_info,
        "proc_single_inventory": proc_inventory
    }
