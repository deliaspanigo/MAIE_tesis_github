# --- 1. System Libraries ---
import click
import re
import time
import os
import json
from pathlib import Path

# --- 2. My Libraries ---
# Importamos la función que procesa el archivo individual (Satpy, etc.)
from .core01_proc_each_file.ABI_L2_LSTF import process_lstf_single_file
from goes_processor.HARDCODED_FOLDERS import get_my_path

# --- 3. CONFIGURATION ---
# Mapeamos productos a sus funciones de procesamiento real
PRODUCT_STRATEGY = {
    "ABI-L2-LSTF": process_lstf_single_file,
}

PRODUCT_OPTIONS = list(PRODUCT_STRATEGY.keys()) + ["ALL"]

# --- 4. VALIDATORS ---
def validate_year(ctx, param, value):
    if not re.match(r'^\d{4}$', value):
        raise click.BadParameter('Year must be exactly 4 digits.')
    return value

def validate_julian_day(ctx, param, value):
    if not re.match(r'^\d{3}$', value):
        raise click.BadParameter('Day must be exactly 3 digits.')
    return value

# --- 5. CLI COMMAND ---

@click.command(name="run-each-file")
@click.option('--product', type=click.Choice(PRODUCT_OPTIONS, case_sensitive=False), required=True)
@click.option('--year', callback=validate_year, required=True)
@click.option('--day', callback=validate_julian_day, required=True)
@click.option('--overwrite', type=click.Choice(['True', 'False'], case_sensitive=False), default='False')
def run_processor_each_file_cmd(product, year, day, overwrite):
    """v.0.5.1 - Ejecutor de Procesamiento Individual"""
    start_ts = time.time()
    overwrite_bool = overwrite.lower() == 'true'
    day_str = str(day).zfill(3)
    
    target = product.upper()
    prods_to_process = list(PRODUCT_STRATEGY.keys()) if target == "ALL" else [target]
    
    click.secho(f"\n🚀 EXECUTION MODE: {target} | {year}-{day_str}", fg='magenta', bold=True)
    click.echo("="*65)

    for p_name in prods_to_process:
        # 1. Buscar el JSON del Plan de Procesamiento
        plan_folder = get_my_path("plan_processing")
        # El planner los guarda en: sat_bucket / year / day / planner_processing_...
        # Buscamos el archivo que generamos antes
        search_pattern = f"**/planner_processing_{year}_{day_str}_{p_name}.json"
        plan_files = list(Path(plan_folder).rglob(search_pattern))

        if not plan_files:
            click.secho(f"📦 Task {p_name}: ❌ No planning JSON found.", fg='red')
            continue

        # 2. Cargar la data del plan
        with open(plan_files[0], 'r', encoding='utf-8') as f:
            plan_data = json.load(f)

        inventory = plan_data.get("processing_inventory", {})
        click.secho(f"📦 Task {p_name}: Found {len(inventory)} processes in inventory.", fg='white')

        proc_func = PRODUCT_STRATEGY[p_name]

        # 3. Iterar sobre el Inventario y Procesar
        for proc_key, task_data in inventory.items():
            # Verificamos si el input existe físicamente
            input_nc = Path(task_data["inputs"]["raw_nc"]["path_absolute"])
            
            if not input_nc.exists():
                click.secho(f"  ⏩ {proc_key}: Skipped (Input NC missing)", fg='yellow')
                continue

            click.echo(f"  ⚙️  Processing {proc_key}...")
            
            try:
                # Llamamos a ABI_L2_LSTF.py -> fn01_lstf_generate_products
                # Pasamos la data de la tarea, el overwrite y un indent para el print
                result = proc_func(task_data, overwrite=overwrite_bool, indent="     ")
                
                if result.get("stage_01"):
                    click.secho(f"     ✅ Success", fg='green')
                else:
                    click.secho(f"     ❌ Failed", fg='red')

            except Exception as e:
                click.secho(f"     💥 Error: {e}", fg='red')

    duration = round(time.time() - start_ts, 2)
    click.echo("="*65)
    click.secho(f"✨ Total execution time: {duration}s.\n", fg='green', bold=True)
