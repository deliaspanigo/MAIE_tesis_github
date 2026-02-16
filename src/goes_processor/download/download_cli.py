# src/goes_processor/download/download_cli.py

import click
from .download import download_files

@click.group(name="download")
def download():
    """Gestión de descargas satelitales GOES."""
    pass

@download.command(name="goes-files")
@click.option('--satellite', default="19", type=click.Choice(["16", "17", "18", "19"]), help='Satélite GOES (16, 17, 18, 19).')
@click.option('--product', required=True, help='Nombre del producto (ej: ABI-L2-LSTF, ABI-L2-MCMIPF, ABI-L2-FDCF).')
@click.option('--year', required=True, help='Año (YYYY).')
@click.option('--day', required=True, help='Día del año (DDD).')
@click.option('--hour', default="all", help='Hora (HH) o "all".')
@click.option('--minute', default="all", help='Minuto (MM) o "all".')
@click.option('--output', default="data/raw", help='Carpeta de destino.')
@click.option('--overwrite', 
              type=click.Choice(['yes', 'no']), 
              default='no', 
              help='Forzar descarga aunque el peso sea correcto (yes/no).')
def download_files_cli(satellite, product, year, day, hour, minute, output, overwrite):
    """Descarga archivos NetCDF directamente desde NOAA S3 con validación de peso."""
    
    # 1. Validar Hora
    if hour != "all":
        hour = hour.zfill(2)
        if not (0 <= int(hour) <= 23):
            raise click.BadParameter("La hora debe estar entre 00 y 23.")

    # 2. Validar Minuto
    if minute != "all":
        minute = minute.zfill(2)
        if not (0 <= int(minute) <= 59):
            raise click.BadParameter("El minuto debe estar entre 00 y 59.")

    # 3. Convertir overwrite a Booleano para el núcleo
    should_overwrite = (overwrite == 'yes')

    # --- EJECUCIÓN ---
    try:
        download_files(
            product=product,
            year=year,
            day_of_year=day.zfill(3),
            hour=hour,
            minute=minute,
            output_dir=output,
            satellite=satellite,
            overwrite=should_overwrite
        )
    except Exception as e:
        click.secho(f"\n[!] ERROR CRÍTICO EN CLI: {e}", fg="red")
