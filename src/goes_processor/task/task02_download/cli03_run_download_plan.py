"""
Path: src/goes_processor/task/task02_download/cli03_run_download_plan.py
Version: 1.9.4 (Import Path Fixed - Legion Stable)
Description: CLI para ejecución de descargas S3 -> Legion. 
             Soporta 'ALL' y tiene importaciones relativas corregidas.
"""

import click
import sys

# --- IMPORTACIONES SOT ---
try:
    from goes_processor.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError as e:
    print(f"\n❌ [ERROR SOT]: No se pudo cargar la lista de productos: {e}")
    sys.exit(1)

# Importación de la Acción 03 y la utilidad de rutas (RUTA CORREGIDA)
from .actions.action03_run_download_plan import execute_action_run_download
from .actions.fn01_file_name_plan_download import get_plan_download_file_path

# --- COLORES PARA TERMINAL ---
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

@click.command(name="run-plan-download")
@click.option('--sat-position', 'sat_id', 
              required=True, 
              type=click.Choice(['east', 'west'], case_sensitive=False),
              help="OBLIGATORIO: Posición del satélite (east/west).")
@click.option('--product', 
              required=True, 
              help="OBLIGATORIO: ID del producto (ej: ABI-L2-LSTF) o 'ALL'.")
@click.option('--year', 
              required=True, 
              type=int, 
              help="OBLIGATORIO: Año en formato YYYY.")
@click.option('--day', 
              required=True, 
              type=int, 
              help="OBLIGATORIO: Día del año (1-366).")
@click.option('--overwrite', 
              required=True, 
              type=bool,
              help="OBLIGATORIO: True para re-descargar archivos, False para saltar existentes.")
@click.option('--threads', 
              required=True, 
              type=int,
              help="OBLIGATORIO: Número de hilos concurrentes (ej: 4, 8, 16).")
def download_s3_command(sat_id, product, year, day, overwrite, threads):
    """
    🚀 EJECUTOR DE DESCARGA (Task 02)
    --------------------------------
    Sincroniza archivos desde Amazon S3 a la Legion.
    Realiza una auditoría atómica (Check-per-file) automáticamente.
    """
    product_input = product.strip().upper()
    
    # 1. Determinación de productos a procesar
    if product_input == "ALL":
        products_to_process = list(AVAILABLE_GOES_PRODUCTS)
    else:
        if product_input not in AVAILABLE_GOES_PRODUCTS:
            click.echo(f"\n{RED}❌ ERROR: El producto '{product_input}' no existe en el SoT.{RESET}")
            return
        products_to_process = [product_input]

    # Normalización para logs
    sat_pos_clean = sat_id.lower()
    day_str = str(day).zfill(3)

    click.echo(f"\n{MAGENTA}=== GOES DOWNLOAD SESSION ==={RESET}")
    click.echo(f"🛰️  Sat: {sat_pos_clean.upper()} | 📅  Date: {year}-{day_str}")
    click.echo(f"🧵  Threads: {threads} | 🔄 Overwrite: {overwrite}")
    click.echo(f"{CYAN}-------------------------------------------{RESET}")

    # 2. Bucle de ejecución
    for current_prod in products_to_process:
        click.echo(f"\n📦 Processing Product: {current_prod}")
        try:
            # Llamada a la acción corregida (con contador interno)
            success = execute_action_run_download(
                sat_pos=sat_pos_clean,
                year=year,
                day=day,
                product_id=current_prod,
                threads=threads,
                overwrite=overwrite
            )

            if not success:
                click.echo(f"\n{YELLOW}⚠️  Aviso: Se encontraron algunos errores o falta el plan para {current_prod}.{RESET}")

        except Exception as e:
            click.echo(f"\n{RED}💥 CRITICAL FAILURE in {current_prod}: {e}{RESET}")

    click.echo(f"\n🏁 {GREEN}Full download session completed.{RESET}\n")

if __name__ == "__main__":
    download_s3_command()
