# src/goes_processor/processing/bulk_cli.py

import click
import time
from pathlib import Path
from datetime import datetime, timedelta
from .logic_crawler.crawler import find_files
from .logic_how.lst import process_file as run_lst
from .logic_how.truecolor import process_file as run_truecolor
from .logic_how.fdc import process_file as run_fdc
from .logic_how.glm_heatmap import process_heatmap as run_heatmap

@click.command(name="bulk")
@click.option('--satellite', required=True, type=click.Choice(['16', '17', '18', '19']))
@click.option('--product', required=True, help="ABI-L2-LSTF, GLM-L2-LCFA, etc.")
@click.option('--year', required=True)
@click.option('--day', required=True)
@click.option('--hour', required=True)
@click.option('--minute', required=True)
@click.option('--input-dir', required=True, type=click.Path(exists=True))
@click.option('--output-dir', required=True, type=click.Path())
@click.option('--format', required=True, type=click.Choice(['png', 'tiff', 'both']))
@click.option('--overwrite', required=True, type=click.Choice(['yes', 'no']))
def bulk_cmd(satellite, product, year, day, hour, minute, input_dir, output_dir, format, overwrite):
    tab = "    "
    bulk_start_ts = time.time()
    should_overwrite = True if overwrite == 'yes' else False
    
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()

    click.echo(f"\n============================================================")
    click.secho(f"🚀 STARTING BULK PROCESSING", fg="cyan", bold=True)
    click.echo(f"============================================================")
    
    # Encontrar archivos
    files = find_files(input_path, satellite, product, year, day, hour, minute)
    total_files = len(files)
    
    if total_files == 0:
        click.secho(f"{tab}❌ No files found.", fg="yellow")
        return

    click.echo(f"{tab}📦 Product: {product}")
    click.echo(f"{tab}🔢 Files found: {total_files}")
    click.echo(f"{tab}📂 Output: {output_path}")
    click.echo(f"{'-'*60}")

    # Bucle de procesamiento UNIFICADO
    for index, f in enumerate(files, 1):
        try:
            current_file = Path(f)
            click.echo(f"\n{tab}📄 Processing [{index}/{total_files}]: {current_file.name}")
            
            # Decisión de procesamiento según producto
            if "GLM" in product:
                # Procesamos ARCHIVO POR ARCHIVO
                run_heatmap(f, input_path, output_path, indent=tab)
            elif "LST" in product:
                run_lst([f], input_path, output_path, format, should_overwrite, indent=tab)
            elif "MCMIP" in product:
                run_truecolor([f], input_path, output_path, format, should_overwrite, indent=tab)
            elif "FDC" in product:
                run_fdc([f], input_path, output_path, format, should_overwrite, indent=tab)

            # Cálculo de ETA
            elapsed = time.time() - bulk_start_ts
            avg = elapsed / index
            rem = total_files - index
            if rem > 0:
                eta = str(timedelta(seconds=int(avg * rem)))
                click.secho(f"{tab}📈 Progress: {(index/total_files)*100:.1f}% | ETA: {eta}", fg="green")

        except Exception as e:
            click.secho(f"{tab}❌ ERROR in file {index}: {e}", fg="red")

    _finish_report(bulk_start_ts, total_files, product)

def _finish_report(start_ts, total, product):
    duration = str(timedelta(seconds=int(time.time() - start_ts)))
    click.echo(f"\n{'='*60}")
    click.secho(f"✅ BULK COMPLETED", fg="cyan", bold=True)
    click.echo(f"{'='*60}")
    click.echo(f"⏱️  Duration: {duration}")
    click.echo(f"{'='*60}\n")
