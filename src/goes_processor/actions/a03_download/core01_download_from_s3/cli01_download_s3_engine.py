"""
Path: src/goes_processor/actions/a03_download/core01_download_from_s3/cli01_download_s3_engine.py
Version: 1.1.2 (Fixed Imports for goes_prod.py)
"""
import click
import sys

# Colores ANSI para la Legion
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

# --- IMPORTS SINCRONIZADOS ---
try:
    from .code01_download_s3_engine import execute_s3_download
    # Importamos la tupla pública de tu SoT
    from goes_processor.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError:
    try:
        from goes_processor.actions.a03_download.core01_download_from_s3.code01_download_s3_engine import execute_s3_download
        from goes_processor.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
    except ImportError as e:
        print(f"{RED}❌ Critical Import Error:{RESET} {e}")
        execute_s3_download = None
        AVAILABLE_GOES_PRODUCTS = None

@click.command(name="run-download-s3")
@click.option('--sat-position', required=True, type=click.Choice(['east', 'west']))
@click.option('--product', required=True, help="Product name or 'ALL'")
@click.option('--year', required=True, type=int)
@click.option('--day', required=True, type=str)
@click.option('--overwrite', required=True, type=bool)
@click.option('--threads', default=4, type=int)
def download_s3_command(sat_position, product, year, day, threads, overwrite):
    """
    Ejecuta la descarga usando los planes JSON. Soporta --product ALL.
    """
    if execute_s3_download is None:
        click.echo(f"{RED}🚫 Logic engine (code01) is unavailable.{RESET}", err=True)
        return

    # 1. EXPANSIÓN DE 'ALL'
    if product.upper() == "ALL":
        if AVAILABLE_GOES_PRODUCTS:
            products_to_process = list(AVAILABLE_GOES_PRODUCTS)
            click.echo(f"📦 {GREEN}EXPANDING 'ALL':{RESET} Found {len(products_to_process)} products in SoT.")
        else:
            click.echo(f"{RED}❌ No products found in SoT/goes_prod.py{RESET}", err=True)
            return
    else:
        products_to_process = [product]

    # 2. INFO INICIAL
    status_msg = f"{YELLOW}FORCING OVERWRITE{RESET}" if overwrite else f"{GREEN}SKIP IF EXISTS{RESET}"
    click.echo(f"🚀 Initializing download session for {year}-{day}")
    click.echo(f"🛠️  Mode: {status_msg} | Workers: {threads}\n")

    # 3. EJECUCIÓN SERIAL POR PRODUCTO (INTERNO MULTI-THREAD)
    for current_prod in products_to_process:
        try:
            # El motor (code01) ya tiene los checks verdes y el manejo de errores
            execute_s3_download(sat_position, current_prod, year, day, threads, overwrite)
        except Exception as e:
            click.echo(f"{RED}💥 Failed to process {current_prod}:{RESET} {e}", err=True)
            continue

    click.echo(f"\n🏁 {GREEN}Full session completed successfully.{RESET}")
