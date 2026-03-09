"""
Path: src/legion_goes/task/task03_processing/subtask01_proc_single/cli02_check_plan_proc_single.py
Version: 1.6.5 (Strict Audit Mode)
Description: CLI para auditar la integridad de archivos antes del procesamiento.
             Sincroniza el Plan de Descarga (Task 02) con el de Proceso (Task 03).
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

# Importación de la acción de auditoría (Task 03)
from .actions.action02_check_plan_proc_single import run_integrity_check_by_params

# --- COLORES PARA TERMINAL ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

@click.command(name="check-plan-proc")
@click.option('--sat-position', 'sat_id', required=True, 
              type=click.Choice(['east', 'west'], case_sensitive=False),
              help="Posición del satélite (east/west)")
@click.option('--product', required=True, 
              help="ID del producto (ej: ABI-L2-MCMIPF)")
@click.option('--year', required=True, type=int, help="Año YYYY")
@click.option('--day', required=True, type=int, help="Día juliano (1-366)")
@click.option('--tag', default="fnp01", help="Tag del algoritmo (fnp01, fnp02)")
def check_plan_proc_command(sat_id, product, year, day, tag):
    """
    🔍 AUDITOR DE INTEGRIDAD DE PROCESAMIENTO
    Cruza el inventario del plan con la existencia física de los archivos .nc
    """
    product_input = product.strip().upper()
    
    # 1. Validación contra SoT
    if product_input not in AVAILABLE_GOES_PRODUCTS:
        click.echo(f"\n{RED}❌ ERROR: El producto '{product_input}' no es válido en el SoT.{RESET}")
        return

    sat_pos_clean = sat_id.lower()

    click.echo(f"\n{CYAN}--- 🛠️  INICIANDO AUDITORÍA DE ARCHIVOS ---{RESET}")
    click.echo(f"📦 Producto: {product_input} | Tag: {tag}")
    click.echo(f"📅 Fecha: {year}-{str(day).zfill(3)} | Sat: {sat_pos_clean.upper()}")
    click.echo(f"{CYAN}------------------------------------------{RESET}")

    try:
        # 2. Ejecución de la Acción 02
        # Esta función abre el JSON del plan y actualiza 'is_ready_to_proc'
        run_integrity_check_by_params(
            year=year,
            day=day,
            sat_pos=sat_pos_clean,
            product_id=product_input,
            fnp_tag=tag
        )
        
        click.echo(f"\n{GREEN}✅ Auditoría finalizada. Plan actualizado y listo.{RESET}\n")

    except Exception as e:
        click.echo(f"\n{RED}💥 Error crítico durante la auditoría: {e}{RESET}")

if __name__ == "__main__":
    check_plan_proc_command()
