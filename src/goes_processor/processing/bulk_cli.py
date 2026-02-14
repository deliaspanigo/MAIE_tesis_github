import click
from pathlib import Path
from .logic_crawler.crawler import find_files
from .logic_how.lst import process_file as run_lst
from .logic_how.truecolor import process_file as run_truecolor

@click.command(name="bulk")
@click.option('--satellite', required=True, type=click.Choice(['16', '17', '18', '19']), help="Número del satélite (ej: 19)")
@click.option('--product', required=True, help="Ej: ABI-L2-LSTF o ABI-L2-MCMIPF")
@click.option('--year', required=True, help="Año YYYY o all")
@click.option('--day', required=True, help="Día JJJ o all")
@click.option('--hour', required=True, help="Hora HH o all")
@click.option('--minute', required=True, help="Minuto MM o all")
@click.option('--input-dir', required=True, type=click.Path(exists=True))
@click.option('--output-dir', required=True, type=click.Path())
@click.option('--format', required=True, type=click.Choice(['png', 'tiff', 'both']))
@click.option('--overwrite', required=True, type=click.Choice(['yes', 'no']))
def bulk_cmd(satellite, product, year, day, hour, minute, input_dir, output_dir, format, overwrite):
    """Procesamiento masivo con filtro de satélite y productos mixtos."""
    
    # El crawler filtra por la carpeta noaa-goesX usando el nuevo orden de búsqueda
    files = find_files(input_dir, satellite, product, year, day, hour, minute)
    
    if not files:
        click.secho(f"No se encontró nada para G{satellite} - {product} en {year}/{day}", fg="yellow")
        return

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    should_overwrite = (overwrite == 'yes')

    with click.progressbar(files, label=f"Procesando G{satellite}") as bar:
        for f in bar:
            try:
                # Lógica para Land Surface Temperature (LST)
                if "LST" in product:
                    run_lst(f, input_path, output_path, format, should_overwrite)
                
                # Lógica para True Color (MCMIP o Radiancias)
                elif "MCMIP" in product or "Rad" in product:
                    run_truecolor([f], input_path, output_path, format, should_overwrite)
                    
            except Exception as e:
                click.secho(f"\n[ERROR] {f.name}: {e}", fg="red")
