"""
Path: src/legion_goes/task/task03_processing/subtask01_proc_single/subtask01_proc_single.py
Version: 1.5.1
Description: CLI unificado compatible con Catálogo fn02 y Actions v.2.1.4.
"""

import click
import sys
from pathlib import Path

# Configuración de rutas
sys.path.append(str(Path(__file__).resolve().parent))

try:
    # Importación de Actions
    from actions.action01_gen_plan_proc_single import gen_and_save_plan_proc_single
    from actions.action02_check_plan_proc_single import run_integrity_check_by_params
    from actions.action03_run_plan_proc_single import orchestrate_full_product, CATALOGO_PRODUCTOS
    
    # SoT
    from legion_goes.SoT.goes_hardcoded_folders import get_my_path
except ImportError as e:
    print(f"\033[91m❌ Error de infraestructura: {e}\033[0m")
    sys.exit(1)

# --- COLORES ---
MAGENTA = "\033[95m"
RESET = "\033[0m"

@click.group(name="proc-single")
def proc_single_group():
    """🌊 TASK 03.01: Procesamiento Unitario"""
    pass

# --- 1. GENERAR PLAN ---
@proc_single_group.command(name="gen-plan")
@click.option('--product', required=True)
@click.option('--day', required=True, type=int)
@click.option('--year', required=True, type=int)
@click.option('--sat', required=True, type=click.Choice(['east', 'west']))
@click.option('--tag', default="fnp01", help="ID del proceso en el catálogo (fnp01, fnp02...)")
@click.option('--overwrite', required=True, type=bool)
def gen_plan(product, day, year, sat, tag, overwrite):
    """📂 Genera el JSON del plan."""
    path_base = get_my_path("data_raw")
    
    # Buscamos el schema en el catálogo importado de Action03
    prod_id = product.replace("ABI-L2-", "") # Limpieza por si acaso
    try:
        schema = CATALOGO_PRODUCTOS[prod_id]['fnps'][tag]['schema']
    except KeyError:
        click.echo(f"❌ Error: {prod_id} o {tag} no encontrados en el catálogo.")
        return

    gen_and_save_plan_proc_single(
        year=year, day=day, sat_pos=sat.lower(),
        product_id=product.upper(), # Usamos el ID completo para la ruta
        output_folder_base=str(path_base),
        dict_output_names=schema,
        fnp_tag=tag,
        overwrite=overwrite
    )

# --- 2. AUDITAR (EL QUE FALLABA) ---
@proc_single_group.command(name="check-plan")
@click.option('--product', required=True)
@click.option('--day', required=True, type=int)
@click.option('--year', required=True, type=int)
@click.option('--sat', required=True, type=click.Choice(['east', 'west']))
@click.option('--tag', default="fnp01", help="Tag a auditar")
def check_plan(product, day, year, sat, tag):
    """🔍 Verifica integridad física del plan."""
    run_integrity_check_by_params(
        year=year,
        day=day,
        sat_pos=sat.lower(),
        product_id=product.upper(),
        fnp_tag=tag # <-- ARGUMENTO AÑADIDO PARA CORREGIR EL TYPEERROR
    )

# --- 3. RUN FULL ---
@proc_single_group.command(name="run-full")
@click.option('--product', required=True)
@click.option('--day', required=True, type=int)
@click.option('--year', required=True, type=int)
@click.option('--sat', required=True, type=click.Choice(['east', 'west']))
@click.option('--tag', default=None, help="Tag específico o None para todos")
@click.option('--overwrite', required=True, type=bool)
def run_full(product, day, year, sat, tag, overwrite):
    """🚀 Ejecuta Plan + Audit + Process."""
    path_base = get_my_path("data_raw")
    
    orchestrate_full_product(
        product_name=product.upper().replace("ABI-L2-", ""),
        year=year,
        day=day,
        sat_pos=sat.lower(),
        output_folder_base=str(path_base),
        overwrite=overwrite,
        fnp_tag=tag
    )

if __name__ == "__main__":
    proc_single_group()
