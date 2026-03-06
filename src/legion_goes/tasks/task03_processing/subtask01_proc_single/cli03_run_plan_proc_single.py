"""
Path: src/legion_goes/task/task03_processing/subtask01_proc_single/cli03_run_plan_proc_single.py
Version: 1.9.5 (Strict Execution Mode)
Description: CLI para ejecutar el motor de procesamiento Satpy/FNP.
             Sincronizado con la Action 03 Maestro (v.2.1.3).
"""

import click
import sys
from pathlib import Path

# --- IMPORTACIONES SOT ---
try:
    from legion_goes.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError as e:
    print(f"\n\033[91m❌ [ERROR SOT]: No se pudo cargar AVAILABLE_GOES_PRODUCTS: {e}\033[0m")
    sys.exit(1)

# Importación del Orquestador de Ejecución (Task 03)
from .actions.action03_run_plan_proc_single import execute_proc_single_by_product
from .actions.fn01_file_name_plan_proc_single import get_plan_proc_single_file_path

# --- COLORES PARA TERMINAL ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

@click.command(name="run-plan-proc")
@click.option('--sat-position', 'sat_id', required=True, 
              type=click.Choice(['east', 'west'], case_sensitive=False),
              help="Posición del satélite.")
@click.option('--product', required=True, 
              help="ID del producto (ej: MCMIPF).")
@click.option('--year', required=True, type=int, help="Año YYYY.")
@click.option('--day', required=True, type=int, help="Día juliano (1-366).")
@click.option('--tag', default="fnp01", help="Tag del algoritmo (fnp01, fnp02).")
@click.option('--overwrite', required=True, type=bool,
              help="True para forzar re-procesamiento, False para saltar archivos ya creados.")
def run_plan_proc_command(sat_id, product, year, day, tag, overwrite):
    """
    🚀 MOTOR DE EJECUCIÓN DE PROCESAMIENTO
    Lee el plan auditado y dispara los algoritmos FNP correspondientes.
    """
    product_input = product.strip().upper()
    
    # 1. Validación contra SoT
    if product_input not in AVAILABLE_GOES_PRODUCTS:
        click.echo(f"\n{RED}❌ ERROR: El producto '{product_input}' no es válido.{RESET}")
        return

    sat_pos_clean = sat_id.lower()

    # 2. Localizar el Plan
    path_plan = get_plan_proc_single_file_path(
        year=str(year),
        day=str(day).zfill(3),
        sat_id=sat_pos_clean,
        product_id=product_input,
        proc_tag=tag
    )

    if not path_plan.exists():
        click.echo(f"\n{YELLOW}⚠️  ERROR: No existe un plan para este día. Ejecuta primero el CLI 01.{RESET}")
        return

    click.echo(f"\n{MAGENTA}🚀 INICIANDO PROCESAMIENTO SATELITAL{RESET}")
    click.echo(f"📦 Producto: {product_input} | Tag: {tag}")
    click.echo(f"🔄 Modo Overwrite: {overwrite}")
    click.echo(f"{CYAN}------------------------------------------{RESET}")

    try:
        # 3. Disparar el Motor (Action 03)
        # Aquí es donde ocurre la magia y el log: [001/144] ... OK
        execute_proc_single_by_product(
            product_name=product_input,
            path_plan_proc=path_plan,
            overwrite=overwrite
        )
        
        click.echo(f"\n{GREEN}✨ Procesamiento completado con éxito.{RESET}\n")

    except Exception as e:
        click.echo(f"\n{RED}💥 Error crítico en el motor de ejecución: {e}{RESET}")

if __name__ == "__main__":
    run_plan_proc_command()
