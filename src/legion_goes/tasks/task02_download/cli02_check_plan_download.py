"""
Path: src/legion_goes/task/task02_download/cli02_check_plan_download.py
Version: 1.6.1 (Parameter & SoT Sync)
Description: CLI para auditar la integridad local. Sincronizado con Action 02 v.0.3.8.
"""

import click
import sys

# --- IMPORTACIONES DESDE EL SOT ---
try:
    from legion_goes.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError:
    # Mantenemos tu fallback pero el SoT debería dominar
    AVAILABLE_GOES_PRODUCTS = ["ABI-L2-LSTF", "ABI-L2-MCMIPF"]

# Importación de la acción
from .actions.action02_check_plan_download import execute_action_check_plan

# --- COLORES PARA TERMINAL ---
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

@click.command(name="check-plan-download")
@click.option('--sat-position', 'sat_id', required=True, 
              type=click.Choice(['east', 'west'], case_sensitive=False),
              help="Posición del satélite (east/west)")
@click.option('--product', required=True, 
              help="ID del producto (ej: ABI-L2-LSTF) o 'ALL'")
@click.option('--year', required=True, type=int, help="Año (YYYY)")
@click.option('--day', required=True, type=int, help="Día del año (1-366)")
# Quitamos flags innecesarios para mantener el comando limpio
def check_plan_command(sat_id, product, year, day):
    """
    🔍 AUDITOR DE INTEGRIDAD (Task 02)
    Cruza el JSON del Plan con los archivos físicos .nc en la Legion.
    """
    product_input = product.strip().upper()
    
    # 1. Validación de productos
    if product_input == "ALL":
        products_to_process = list(AVAILABLE_GOES_PRODUCTS)
    elif product_input in AVAILABLE_GOES_PRODUCTS:
        products_to_process = [product_input]
    else:
        click.echo(f"\n{RED}❌ ERROR: El producto '{product_input}' no es válido.{RESET}")
        return

    # Normalización de strings para la acción
    sat_pos_clean = sat_id.lower()

    click.echo(f"\n🔍 {CYAN}AUDITING LOCAL STORAGE{RESET} | Sat: {sat_pos_clean.upper()} | Day: {year}-{str(day).zfill(3)}")

    # 2. Bucle de Auditoría
    for current_prod in products_to_process:
        try:
            click.echo(f"  📂 Checking {current_prod}...", nl=False)
            
            # --- CAMBIO CRÍTICO: Sincronización de argumentos con Action 02 v.0.3.8 ---
            # Tu Acción 02 define: (sat_pos, year, day, product_id)
            success = execute_action_check_plan(
                sat_pos=sat_pos_clean,
                year=year,
                day=day,
                product_id=current_prod
            )
            
            if success:
                click.echo(f" {GREEN}VERIFIED{RESET}")
            else:
                click.echo(f" {YELLOW}PLAN NOT FOUND{RESET}")
                
        except Exception as e:
            click.echo(f"\n{RED}💥 Audit Error in {current_prod}: {e}{RESET}")

    click.echo(f"🏁 {GREEN}Audit session finished.{RESET}\n")

if __name__ == "__main__":
    check_plan_command()
