"""
Path: src/legion_goes/task/task02_download/cli01_gen_plan_download.py
Version: 1.7.0 (Strict Explicit Mode)
Description: CLI para generar planes con parámetros obligatorios y explícitos.
"""

import click
import sys

# --- IMPORTACIONES SOT ---
try:
    from legion_goes.SoT.goes_hardcoded_folders import get_my_path
    from legion_goes.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
except ImportError as e:
    print(f"\n❌ [ERROR SOT]: {e}")
    sys.exit(1)

from .actions.action01_gen_plan_download import gen_and_save_plan_download

@click.command(name="gen-plan-download")
@click.option('--sat-position', required=True, type=click.Choice(['east', 'west']))
@click.option('--product', required=True, help="Producto o 'ALL'")
@click.option('--year', required=True, type=int)
@click.option('--day', required=True, type=int)
# --- CAMBIO CLAVE: Ahora es un BOOLEAN obligatorio, NO un flag ---
@click.option('--overwrite', 
              required=True, 
              type=bool, 
              help="Obligatorio: True para sobrescribir, False para respetar existente.")
def gen_plan_command(sat_position, product, year, day, overwrite):
    """
    🛰️ GENERADOR DE PLANES (Modo Estricto)
    Requiere validación explícita de overwrite.
    """
    product_input = product.strip().upper()
    
    # Validación de productos
    if product_input == "ALL":
        products_to_process = list(AVAILABLE_GOES_PRODUCTS)
    elif product_input in AVAILABLE_GOES_PRODUCTS:
        products_to_process = [product_input]
    else:
        click.echo(f"❌ Producto '{product_input}' no válido.")
        return

    # Ruta desde SoT
    raw_base = get_my_path("data_raw")

    for current_prod in products_to_process:
        click.echo(f"🔍 Planning Download {current_prod} (Overwrite: {overwrite})...", nl=False)
        
        success = gen_and_save_plan_download(
            sat_pos=sat_position.lower(),
            year=year,
            day=day,
            prod_id=current_prod,
            output_folder_base=str(raw_base),
            overwrite=overwrite # Se pasa el Booleano explícito
        )
        
        if success:
            click.echo(" ✅ OK")
        else:
            click.echo(" ❌ FAILED")

if __name__ == "__main__":
    gen_plan_command()
