# --- 1. System Libraries ---
import click
import re
import time
import os
import json
from datetime import datetime
from pathlib import Path

# --- 2. My Libraries ---
# Importamos la lógica de generación del plan de procesamiento
from .core02_planner_processing.lstf import gen_plan_processing_ONE_DAY_LSTF
# from .core02_planner_processing.fdcf import gen_plan_processing_ONE_DAY_FDCF
from goes_processor.HARDCODED_FOLDERS import get_my_path

# --- 3. CONFIGURATION & STRATEGY ---
PRODUCT_STRATEGY = {
    "ABI-L2-LSTF": gen_plan_processing_ONE_DAY_LSTF,
    # "ABI-L2-FDCF": gen_plan_processing_ONE_DAY_FDCF,
}

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

# --- 5. HELPER CLASSES ---

class StrictDict(dict):
    """
    Protege la estructura del diccionario impidiendo nuevas llaves.
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

def save_and_verify_json_processing_plan(dict_plan, overwrite):
    """
    Guarda el JSON del plan de procesamiento en la carpeta data_planner/p02_processing.
    """
    # 1. Obtener ruta base del planner de procesamiento
    base_output_dir = get_my_path("plan_processing")
    base_path = Path(base_output_dir)
    
    # 2. Extraer info del producto para la ruta de carpetas
    p_info = dict_plan.get("prod_info", {})
    sat_bucket = p_info.get("bucket", "unknown")
    year = str(p_info.get("year", "unknown"))
    day  = str(p_info.get("day", "unknown")).zfill(3)
    p_name = p_info.get("product", "unknown")
    
    # 3. Crear directorio destino: satelite/año/dia
    target_dir = base_path / sat_bucket / year / day
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 4. Nombre del archivo y rutas
    file_name = f"planner_processing_{year}_{day}_{p_name}.json"
    path_absolute = target_dir / file_name
    
    if path_absolute.exists() and not overwrite:
        click.secho(f"    ⏩ Skipped: {file_name} already exists.", fg='yellow')
        return True

    try:
        # 5. Inyectar metadatos finales en el bloque summary antes de guardar
        dict_plan["summary"]["file_name"] = file_name
        dict_plan["summary"]["path_absolute"] = str(path_absolute.resolve())
        dict_plan["summary"]["path_relative"] = os.path.relpath(path_absolute, start=os.getcwd())
        dict_plan["summary"]["time_last_mod"] = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - System"

        with open(path_absolute, 'w', encoding='utf-8') as f:
            json.dump(dict_plan, f, indent=4, ensure_ascii=False)
        
        click.secho(f"    ✅ Saved: {file_name}", fg='green')
        return True
    except Exception as e:
        click.secho(f"    ❌ Error saving {file_name}: {e}", fg='red')
        return False

# --- 6. CLI COMMAND ---

@click.command(name="gen-plan-processing")
@click.option('--product', type=click.Choice(PRODUCT_OPTIONS, case_sensitive=False), required=True, help="Product to process")
@click.option('--year', callback=validate_year, required=True)
@click.option('--day', callback=validate_julian_day, required=True)
@click.option('--overwrite', type=click.Choice(['True', 'False'], case_sensitive=False), default='False')
def run_planner_processing_cmd(product, year, day, overwrite):
    """v.0.8.6 - Generador de Planes de Procesamiento (LSTF, etc.)"""
    start_ts = time.time()
    overwrite_bool = overwrite.lower() == 'true'
    
    target = product.upper()
    prods_to_process = [k for k in PRODUCT_STRATEGY.keys()] if target == "ALL" else [target]
    
    click.secho(f"\n🚀 PROCESSING PLANNER | Target: {target} | {year}-{day}", fg='cyan', bold=True)
    click.echo("="*65)

    for p_name in prods_to_process:
        click.secho(f"📦 Task: {p_name}...", fg='white')
        gen_func = PRODUCT_STRATEGY.get(p_name)

        if not gen_func:
            click.secho(f"    ❌ Strategy not implemented for {p_name}", fg='red')
            continue

        try:
            # 1. Generar la data base
            raw_data = gen_func(year, day)
            
            if raw_data is None or (isinstance(raw_data, str) and "Error" in raw_data):
                click.secho(f"    ❌ Failed to generate data for {p_name}", fg='red')
                continue

            # 2. Asegurar que las llaves de metadatos existan para StrictDict
            # Esto evita el KeyError al intentar inyectarlas en save_and_verify
            for key in ["file_name", "path_absolute", "path_relative", "time_last_mod"]:
                if key not in raw_data["summary"]:
                    raw_data["summary"][key] = None

            # 3. Aplicar StrictDict para proteger la integridad
            dict_plan = StrictDict(raw_data)

            # 4. Guardar y verificar
            save_and_verify_json_processing_plan(dict_plan, overwrite_bool)

        except KeyError as ke:
            click.secho(f"    🛑 Structure Error in {p_name}: {ke}", fg='magenta', bold=True)
        except Exception as e:
            click.secho(f"    💥 Critical Error {p_name}: {e}", fg='red')

    duration = round(time.time() - start_ts, 2)
    click.echo("="*65)
    click.secho(f"✨ Finished in {duration}s.\n", fg='green', bold=True)
