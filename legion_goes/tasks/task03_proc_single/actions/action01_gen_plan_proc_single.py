# =============================================================================
# PATH: src/legion_goes/tasks/task03_proc_single/actions/action01_gen_plan_proc_single.py
# Version: 1.8.9 (Ultra-Resilient Path Discovery)
# =============================================================================

import json
from pathlib import Path
from datetime import datetime
import importlib
import importlib.resources

# Imports internos
from .fn01_file_name_plan_proc_single import generate_plan_proc_single_file_path
from legion_goes.tasks.task02_download.actions.fn01_file_name_plan_download import generate_plan_download_file_path

def run_action01_gen_plan_proc_single(
    year, day, sat_id, product_id, fnp_tag,
    output_folder_base_data_raw, 
    output_folder_base_data_proc, 
    output_folder_base_data_plan,
    dict_output_schema
):
    ctx = f"[Action 01 - {fnp_tag}]"
    
    if None in [output_folder_base_data_raw, output_folder_base_data_proc, output_folder_base_data_plan]:
        print(f"❌ {ctx} Error: Una de las rutas base es None.")
        return None

    raw_root  = Path(str(output_folder_base_data_raw)).resolve()
    proc_root = Path(str(output_folder_base_data_proc)).resolve()
    plan_root = Path(str(output_folder_base_data_plan)).resolve()
    
    # 1. IMPORT DOWNLOAD PLAN
    file_path_json_plan_download = generate_plan_download_file_path(
        year=year, day=day, sat_id=sat_id, 
        product_id=product_id, output_folder_base=plan_root
    )
    
    if not file_path_json_plan_download or not file_path_json_plan_download.exists():
        print(f"❌ {ctx} Error: No se encuentra el plan de descarga en {file_path_json_plan_download}")
        return None

    try:
        with open(file_path_json_plan_download, 'r') as archivo:
            dict_plan_download = json.load(archivo)
    except Exception as e:
        print(f"❌ {ctx} Error leyendo el JSON: {e}")
        return None

    download_inventory = dict_plan_download.get('download_inventory', {})
    str_year, str_day = str(year), str(day).zfill(3)
    bucket_name = dict_plan_download.get('self_info', {}).get('bucket_name', 'noaa-goes19')

    # 2. SCANNING DATA (Lógica Mejorada)
    # Escaneamos el disco REAL para tener una lista de la verdad
    files_on_disk = {f.name: f for f in raw_root.rglob("*.nc")}
    found_files_data = []

    for item_id, info in download_inventory.items():
        file_name = info.get('file_name')
        
        # Si el nombre es genérico ("data_raw") o nulo, lo intentamos sacar de path_absolute
        if not file_name or file_name == "data_raw":
            file_name = Path(info.get('path_absolute', '')).name

        # Verificamos si ese nombre existe en nuestro escaneo de disco
        if file_name in files_on_disk:
            found_files_data.append(files_on_disk[file_name])
        else:
            # Búsqueda desesperada: ¿el item_id es el nombre del archivo?
            if item_id in files_on_disk:
                found_files_data.append(files_on_disk[item_id])

    if not found_files_data:
        # Fallback final: Si el inventario no sirvió, pero hay archivos .nc en la carpeta, úsalos
        if files_on_disk:
            print(f"⚠️  {ctx} Inventario de descarga corrupto. Usando {len(files_on_disk)} archivos encontrados en disco.")
            found_files_data = list(files_on_disk.values())
        else:
            print(f"⚠️  {ctx} No se encontraron archivos NetCDF válidos en {raw_root}")
            return None

    # 3. BUILD DETAILED INVENTORY
    proc_inventory = {}
    for i, file_path in enumerate(sorted(found_files_data), 1):
        file_id = f"proc_{i:04d}"
        hour_folder = file_path.parent.name if file_path.parent.name.isdigit() else "00"
        s_time = ""
        target_folder = proc_root / bucket_name / product_id / str_year / str_day / hour_folder / fnp_tag 
        
        mapped_outputs = {}
        for key, template in dict_output_schema.items():
            final_out_path = target_folder / template
            mapped_outputs[key] = {
                "file_name": template,
                "path_absolute": str(final_out_path.resolve()),
                "exists": False
            }

        proc_inventory[file_id] = {
            "time_stamp": f"{str_year}-{str_day}-{hour_folder}",
            "ref_input": {
                "file_name": file_path.name,
                "path_absolute": str(file_path.resolve()),
                "product_id": product_id
            },
            "ref_output": {
                "folder_absolute": str(target_folder.resolve()),
                "outputs": mapped_outputs
            },
            "status": {"is_processed": False, "audit_verified": False, "error": None, "exists_input": True}
        }

    # 4. CONSTRUCT FINAL PLAN
    path_plan = generate_plan_proc_single_file_path(year, day, sat_id, product_id, fnp_tag, plan_root)
    plan_dict = {
        "self_info": {
            "version_github": "v.0.0.1",
            "fnp_tag": fnp_tag,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "path_absolute": str(path_plan.resolve())
        },
        "paths": {"raw_base": str(raw_root), "proc_base": str(proc_root), "plan_base": str(plan_root)},
        "proc_inventory": proc_inventory
    }

    # 5. SAVE TO DISK
    try:
        path_plan.parent.mkdir(parents=True, exist_ok=True)
        with open(path_plan, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=4)
        print(f"✅ {ctx} Plan generated: {path_plan.name} ({len(proc_inventory)} items)")
        return path_plan
    except Exception as e:
        print(f"❌ {ctx} Error guardando plan: {e}")
        return None

# --- Funciones de soporte (Get FNPs y Bundles) ---
def get_available_fnps_for_product(product_id):
    fnp_root_pkg = "legion_goes.tasks.task03_proc_single.actions.fnp"
    prod_prefix = f"{product_id.replace('-', '_')}_SP_single_"
    try:
        with importlib.resources.path(fnp_root_pkg, "__init__.py") as p:
            fnp_dir = p.parent
        tags = [d.name.replace(prod_prefix, "") for d in fnp_dir.iterdir() 
                if d.is_dir() and d.name.startswith(prod_prefix)]
        return sorted(tags)
    except Exception:
        return []

def get_fnp_bundle(product_id, fnp_tag):
    prod_clean = product_id.replace('-', '_')
    base_pkg = f"legion_goes.tasks.task03_proc_single.actions.fnp.{prod_clean}_SP_single_{fnp_tag}"
    try:
        mod_code = importlib.import_module(f"{base_pkg}.fn01_python_code")
        mod_exec = importlib.import_module(f"{base_pkg}.fn02_executor")
        return {
            "schema": getattr(mod_code, "dict_output_schema"),
            "executor": getattr(mod_exec, "run_executor")
        }
    except Exception:
        return None

def run_action01_gen_all_product_plans(
    year, day, sat_id, product_id,
    output_folder_base_data_raw, 
    output_folder_base_data_proc, 
    output_folder_base_data_plan
):
    ctx = "[Action 01 Multi-FNP]"
    tags = get_available_fnps_for_product(product_id)
    if not tags:
        print(f"⚠️  No se encontraron FNPs para {product_id}")
        return []

    print(f"🚀 {ctx} Procesando {len(tags)} FNPs para {product_id}...")
    generated_plans = []

    for tag in tags:
        bundle = get_fnp_bundle(product_id, tag)
        if not bundle: continue
        
        path_plan = run_action01_gen_plan_proc_single(
            year=year, day=day, sat_id=sat_id, 
            product_id=product_id, fnp_tag=tag,
            dict_output_schema=bundle["schema"],
            output_folder_base_data_raw=str(output_folder_base_data_raw or ""),
            output_folder_base_data_proc=str(output_folder_base_data_proc or ""),
            output_folder_base_data_plan=str(output_folder_base_data_plan or "")
        )
        if path_plan:
            generated_plans.append(path_plan)
            
    return generated_plans
