"""
Path: src/legion_goes/task/task03_processing/subtask01_proc_single/cli01_gen_plan_proc_single.py
Version: 1.8.0 (Strict Processing Mode)
Description: CLI para generar planes de PROCESAMIENTO. 
             Define la estructura de salida en f02_processed.
"""

import click
import sys
from pathlib import Path

# --- IMPORTACIONES SOT ---
try:
    from legion_goes.SoT.goes_hardcoded_folders import get_my_path
    from legion_goes.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError as e:
    print(f"\n\033[91m❌ [ERROR SOT]: No se pudo cargar la configuración base: {e}\033[0m")
    sys.exit(1)

# Importación de la acción de procesamiento (Task 03)
from .actions.action01_gen_plan_proc_single import gen_and_save_plan_proc_single

# --- COLORES PARA TERMINAL ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

@click.command(name="gen-plan-proc")
@click.option('--sat-position', 'sat_pos', required=True, 
              type=click.Choice(['east', 'west'], case_sensitive=False),
              help="Posición del satélite.")
@click.option('--product', required=True, 
              help="ID del producto (ej: MCMIPF, LSTF).")
@click.option('--year', required=True, type=int, help="Año YYYY.")
@click.option('--day', required=True, type=int, help="Día juliano (1-366).")
@click.option('--tag', default="fnp01", 
              help="Tag del algoritmo de procesamiento (fnp01, fnp02, etc.).")
@click.option('--overwrite', required=True, type=bool,
              help="Obligatorio: True para sobrescribir el plan JSON existente.")
def gen_plan_proc_command(sat_pos, product, year, day, tag, overwrite):
    """
    📂 GENERADOR DE PLANES DE PROCESAMIENTO
    Establece el mapa de archivos que se crearán en f02_processed.
    """
    product_input = product.strip().upper()
    
    # 1. Validación contra SoT
    if product_input not in AVAILABLE_GOES_PRODUCTS:
        click.echo(f"\033[91m❌ Error: El producto '{product_input}' no existe en AVAILABLE_GOES_PRODUCTS.\033[0m")
        return

    # 2. Configuración de nombres de salida (Schema)
    # Estos templates se usarán para nombrar los PNG/TIF finales
    dict_output_names = {
        "mcmipf_true_color": "{init_name}_TrueColor.png",
        "mcmipf_true_color_day": "{init_name}_TrueColor_DayOnly.png",
        "mcmipf_geotiff": "{init_name}_WGS84.tif",
        "metadata_json": "{init_name}_meta.json"
    }

    # 3. Ruta base desde SoT
    # get_my_path("data_raw") nos da la base para localizar luego f02_processed
    try:
        base_path = get_my_path("data_raw")
    except Exception:
        base_path = Path(".") # Fallback local

    click.echo(f"\n{CYAN}--- GENERANDO PLAN DE PROCESAMIENTO ---{RESET}")
    click.echo(f"📦 Product: {product_input} | Tag: {tag}")
    click.echo(f"📅 Date: {year}-{str(day).zfill(3)} | Overwrite: {overwrite}")

    # 4. Ejecución de la Acción
    try:
        path_plan = gen_and_save_plan_proc_single(
            year=year,
            day=day,
            sat_pos=sat_pos.lower(),
            product_id=product_input,
            output_folder_base=str(base_path),
            dict_output_names=dict_output_names,
            fnp_tag=tag
        )
        
        click.echo(f"✅ {GREEN}Plan creado exitosamente en:{RESET}")
        click.echo(f"📍 {path_plan}")

    except Exception as e:
        click.echo(f"\n\033[91m💥 Error crítico generando el plan: {e}\033[0m")

if __name__ == "__main__":
    gen_plan_proc_command()
