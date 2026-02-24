# src/goes_processor/actions/a02_planner/cli_core01_p01_download.py

import click
import re
import time
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# Business Logic Imports
from .core01_planner01_download.lstf   import gen_plan_download_ONE_DAY_LSTF
from .core01_planner01_download.mcmipf import gen_plan_download_ONE_DAY_MCMIPF
from .core01_planner01_download.fdcf   import gen_plan_download_ONE_DAY_FDCF
from .core01_planner01_download.lcfa   import gen_plan_download_ONE_DAY_LCFA

# --- 1. CONFIGURATION & STRATEGY ---

PRODUCT_STRATEGY = {
    "ABI-L2-LSTF":   (gen_plan_download_ONE_DAY_LSTF,   "ABI-L2-LSTF"),
    "ABI-L2-MCMIPF": (gen_plan_download_ONE_DAY_MCMIPF, "ABI-L2-MCMIPF"),
    "ABI-L2-FDCF":   (gen_plan_download_ONE_DAY_FDCF,   "ABI-L2-FDCF"),
    "GLM-L2-LCFA":   (gen_plan_download_ONE_DAY_LCFA,   "GLM-L2-LCFA"),
}

# --- 2. STRICT VALIDATORS ---

def validate_year(ctx, param, value):
    if not re.match(r'^\d{4}$', value):
        raise click.BadParameter('Year must be exactly 4 digits (e.g., 2026).')
    return value

def validate_julian_day(ctx, param, value):
    if not re.match(r'^\d{3}$', value):
        raise click.BadParameter('Day must be exactly 3 digits (e.g., 003).')
    return value

# --- 3. HELPER FUNCTIONS ---

def execute_save_and_verify(planner_dict, base_output_dir, overwrite):
    """
    Saves the planner JSON using the new nested structure.
    Fixed version to avoid 'is not in the subpath' error.
    """
    p_info = planner_dict.get("prod_info", {})
    # noaa-goes19
    sat_bucket = p_info.get("bucket", "unknown")
    year = p_info.get("year", "unknown")
    day  = p_info.get("day", "unknown")
    
    # Construcción de rutas usando Path para asegurar compatibilidad
    base_path = Path(base_output_dir)
    target_dir = base_path / sat_bucket / year / day
    target_dir.mkdir(parents=True, exist_ok=True)
    
    filename = planner_dict["planner_download_info"]["file_name"]
    full_path = target_dir / filename
    
    if full_path.exists() and not overwrite:
        click.secho(f"   ⏩ Skipped: {filename} already exists.", fg='yellow')
        return True

    try:
        # Usamos os.path.relpath para evitar errores de subpath de pathlib
        rel_path = os.path.relpath(full_path, start=os.getcwd())
        
        # Guardamos rutas en el diccionario antes de escribir el archivo
        planner_dict["planner_download_info"]["path_relative"] = rel_path
        planner_dict["planner_download_info"]["path_absolute"] = str(full_path.resolve())

        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(planner_dict, f, indent=4, ensure_ascii=False)
        
        click.secho(f"   ✅ Saved: {rel_path}", fg='green')
        return True
    except Exception as e:
        click.secho(f"   ❌ Error saving {filename}: {e}", fg='red')
        return False

# --- 4. CLI COMMAND ---

@click.command(name="gen-plan-download")
@click.option('--product', type=click.Choice(['ABI-L2-LSTF', 'ABI-L2-MCMIPF', 'ABI-L2-FDCF', 'GLM-L2-LCFA', 'ALL'], case_sensitive=False), required=True)
@click.option('--year', callback=validate_year, required=True)
@click.option('--day', callback=validate_julian_day, required=True)
@click.option('--output-dir', type=click.Path(), default="data_planner/p01_download")
@click.option('--overwrite', type=click.Choice(['True', 'False'], case_sensitive=False), default='False')
def run_planner_download_cmd(product, year, day, output_dir, overwrite):
    """v.0.5.0 - Compatible con estructura de bloques (prod_info)"""
    start_ts = time.time()
    overwrite_bool = overwrite.lower() == 'true'
    
    target = product.upper()
    prods_to_process = list(PRODUCT_STRATEGY.keys()) if target == "ALL" else [target]
    
    click.secho(f"\n🚀 Planner Mode: {target} | Year: {year} | Day: {day} ", fg='cyan', bold=True)

    for p_name in prods_to_process:
        click.echo(f"📦 Task: {p_name}...")
        gen_func, _ = PRODUCT_STRATEGY[p_name]

        try:
            # 1. Generar el diccionario base (ya viene con prod_info y planner_download_info)
            planner_dict = gen_func(year, day)
            
            if isinstance(planner_dict, str) and "Error" in planner_dict:
                click.secho(f"   ❌ {planner_dict}", fg='red')
                continue

            # 2. Inyectar nombre del archivo en el bloque correcto
            # Usamos los datos de prod_info para el nombre
            str_year = planner_dict["prod_info"]["year"]
            str_day  = planner_dict["prod_info"]["day"]
            filename = f"planner_download_{str_year}_{str_day}_{p_name}.json"
            
            planner_dict["planner_download_info"]["file_name"] = filename

            # 3. Guardar y verificar
            execute_save_and_verify(planner_dict, output_dir, overwrite_bool)

        except Exception as e:
            click.secho(f"   💥 Critical Error {p_name}: {e}", fg='red')

    duration = round(time.time() - start_ts, 2)
    click.secho(f"\n✨ Finished in {duration}s.\n", fg='green', bold=True)
