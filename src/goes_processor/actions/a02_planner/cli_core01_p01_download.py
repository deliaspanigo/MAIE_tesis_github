# src/goes_processor/actions/a02_planner/cli_core01_p01_download.py

# --- 1. System Libraries ---
import click
import re
import time
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# --- 2. My Libraries ---
from .core01_planner01_download.lstf   import gen_plan_download_ONE_DAY_LSTF
from .core01_planner01_download.mcmipf import gen_plan_download_ONE_DAY_MCMIPF
from .core01_planner01_download.fdcf   import gen_plan_download_ONE_DAY_FDCF
from .core01_planner01_download.lcfa   import gen_plan_download_ONE_DAY_LCFA
from goes_processor.HARDCODED_FOLDERS  import get_my_path



# --- 3. CONFIGURATION & STRATEGY ---
PRODUCT_STRATEGY = {
    "ABI-L2-LSTF":   (gen_plan_download_ONE_DAY_LSTF,   "ABI-L2-LSTF"),
    "ABI-L2-MCMIPF": (gen_plan_download_ONE_DAY_MCMIPF, "ABI-L2-MCMIPF"),
    "ABI-L2-FDCF":   (gen_plan_download_ONE_DAY_FDCF,   "ABI-L2-FDCF"),
    "GLM-L2-LCFA":   (gen_plan_download_ONE_DAY_LCFA,   "GLM-L2-LCFA"),
}

# Creamos la lista de opciones dinámicamente
PRODUCT_OPTIONS = list(PRODUCT_STRATEGY.keys()) + ["ALL"]




# --- 4. STRICT VALIDATORS ---

def validate_year(ctx, param, value):
    if not re.match(r'^\d{4}$', value):
        raise click.BadParameter('Year must be exactly 4 digits (e.g., 2026).')
    return value

def validate_julian_day(ctx, param, value):
    if not re.match(r'^\d{3}$', value):
        raise click.BadParameter('Day must be exactly 3 digits (e.g., 003).')
    return value

# --- 5. HELPER FUNCTIONS ---
class StrictDict(dict):
    def __init__(self, data):
        # Convertimos sub-diccionarios a StrictDict de forma recursiva
        # El diccionario puede cambiar el contenido asocaidoa sus llaves, pero no peude crear neuvas llaves.
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
        
############################################################################################################################
def save_and_verify_json_plan(dict_plan, overwrite):
    """
    Saves the planner JSON using the new nested structure.
    """
    
    # Output first door.
    base_output_dir = get_my_path("plan_download")
    base_path = Path(base_output_dir)
    
    # Subfolders
    p_info = dict_plan.get("prod_info", {})
    sat_bucket = p_info.get("bucket", "unknown")  # Example: noaa-goes19
    year = p_info.get("year", "unknown")  # Example: 2026
    day  = p_info.get("day", "unknown")   # Example: 003
    
    # Target outptu folder path
    target_dir = base_path / sat_bucket / year / day
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # File name and file path
    file_name = dict_plan["planner_download_info"]["file_name"]
    path_absolute = target_dir / file_name
    
    if path_absolute.exists() and not overwrite:
        click.secho(f"   ⏩ Skipped: {file_name} already exists.", fg='yellow')
        return True

    try:
        # Usamos os.path.relpath para evitar errores de subpath de pathlib
        path_relative = os.path.relpath(path_absolute, start=os.getcwd())
        
        # Guardamos rutas en el diccionario antes de escribir el archivo
        dict_plan["planner_download_info"]["path_relative"] = path_relative
        dict_plan["planner_download_info"]["path_absolute"] = str(path_absolute.resolve())

        with open(path_absolute, 'w', encoding='utf-8') as f:
            json.dump(dict_plan, f, indent=4, ensure_ascii=False)
        
        click.secho(f"   ✅ Saved: {path_relative}", fg='green')
        return True
    except Exception as e:
        click.secho(f"   ❌ Error saving {file_name}: {e}", fg='red')
        return False

# --- 4. CLI COMMAND ---

@click.command(name="gen-plan-download")
@click.option('--product', type=click.Choice(PRODUCT_OPTIONS, case_sensitive=False), required=True, help="Product to process (from PRODUCT_STRATEGY keys)")
@click.option('--year', callback=validate_year, required=True)
@click.option('--day', callback=validate_julian_day, required=True)
@click.option('--overwrite', type=click.Choice(['True', 'False'], case_sensitive=False), default='False')
def run_planner_download_cmd(product, year, day, overwrite):
    """v.0.5.0 - Compatible con estructura de bloques y StrictDict"""
    start_ts = time.time()
    overwrite_bool = overwrite.lower() == 'true'
    
    target = product.upper()
    prods_to_process = list(PRODUCT_STRATEGY.keys()) if target == "ALL" else [target]
    
    click.secho(f"\n🚀 Planner Mode: {target} | Year: {year} | Day: {day} ", fg='cyan', bold=True)

    for p_name in prods_to_process:
        click.echo(f"📦 Task: {p_name}...")
        gen_func, _ = PRODUCT_STRATEGY[p_name]

        try:
            # 1. Generar el diccionario base desde la lógica de negocio
            raw_data = gen_func(year, day)
            
            if isinstance(raw_data, str) and "Error" in raw_data:
                click.secho(f"   ❌ {raw_data}", fg='red')
                continue

            # --- APLICACIÓN DEL STRICTDICT ---
            # Convertimos a StrictDict para bloquear la creación de nuevas keys
            # Esto protege tanto el nivel raíz como los sub-bloques (prod_info, etc.)
            dict_plan = StrictDict(raw_data)

            # 2. Inyectar nombre del archivo en el bloque correcto
            # Si 'prod_info' o 'year' no existieran en el template, esto fallaría aquí mismo.
            str_year = dict_plan["prod_info"]["year"]
            str_day  = dict_plan["prod_info"]["day"]
            file_name = f"planner_download_{str_year}_{str_day}_{p_name}.json"
            
            # Actualizamos el valor (permitido porque la key ya existe en el template)
            dict_plan["planner_download_info"]["file_name"] = file_name

            # 3. Guardar y verificar
            # El execute_save_and_verify ahora recibe un objeto StrictDict
            save_and_verify_json_plan(dict_plan, overwrite_bool)

        except KeyError as ke:
            click.secho(f"   🛑 Structure Error in {p_name}: {ke}", fg='magenta', bold=True)
        except Exception as e:
            click.secho(f"   💥 Critical Error {p_name}: {e}", fg='red')

    duration = round(time.time() - start_ts, 2)
    click.secho(f"\n✨ Finished in {duration}s.\n", fg='green', bold=True)
