# src/goes_processor/processing/bulk_cli.py

import click
import time
from pathlib import Path
from datetime import datetime, timedelta
from .logic_crawler.crawler import find_files
from .logic_how.lst import process_file as run_lst
from .logic_how.truecolor import process_file as run_truecolor
from .logic_how.fdc import process_file as run_fdc

@click.command(name="bulk")
@click.option('--satellite', required=True, type=click.Choice(['16', '17', '18', '19']), help="Satellite number (e.g., 19)")
@click.option('--product', required=True, help="Product type: ABI-L2-LSTF or ABI-L2-MCMIPF or ABI-L2-FDCF")
@click.option('--year', required=True, help="Year YYYY or all")
@click.option('--day', required=True, help="Day JJJ or all")
@click.option('--hour', required=True, help="Hour HH or all")
@click.option('--minute', required=True, help="Minute MM or all")
@click.option('--input-dir', required=True, type=click.Path(exists=True))
@click.option('--output-dir', required=True, type=click.Path())
@click.option('--format', required=True, type=click.Choice(['png', 'tiff', 'both']))
@click.option('--overwrite', required=True, type=click.Choice(['yes', 'no']))
def bulk_cmd(satellite, product, year, day, hour, minute, input_dir, output_dir, format, overwrite):
    """
    Bulk processing with real-time ETA, percentage progress, and detailed final reporting.
    """
    
    # 1. SEARCH FOR FILES
    files = find_files(input_dir, satellite, product, year, day, hour, minute)
    
    if not files:
        click.secho(f"No files found for G{satellite} - {product} on {year}/{day}", fg="yellow")
        return

    # 2. PATH RESOLUTION (Fix subpath errors)
    total_files = len(files)
    input_path = Path(input_dir).resolve() 
    output_path = Path(output_dir).resolve()
    should_overwrite = (overwrite == 'yes')
    tab = "    "

    # Header and BULK Start Time
    bulk_start_dt = datetime.now()
    bulk_start_ts = time.time()

    click.echo(f"\n{'='*60}")
    click.echo(f"📊 BULK DETECTED: {total_files} files")
    click.echo(f"🛰️  Satellite: G{satellite} | 📦 Product: {product}")
    click.echo(f"📅 Start Time: {bulk_start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"{'='*60}\n")

    # 3. PROCESSING LOOP
    for index, f in enumerate(files, start=1):
        counter_prefix = f"[{index:03d}/{total_files:03d}]"
        click.secho(f"{counter_prefix} 🛰️  PROCESSING: {f.name}", fg="cyan", bold=True)
        
        try:
            # Execution based on product type
            if "LST" in product:
                run_lst(f, input_path, output_path, format, should_overwrite, indent=tab)
            elif "MCMIP" in product or "Rad" in product:
                run_truecolor([f], input_path, output_path, format, should_overwrite, indent=tab)
            elif "FDC" in product:
                run_fdc([f], input_path, output_path, format, should_overwrite, indent=tab)
                
            # --- PROGRESS & ETA CALCULATION ---
            elapsed_bulk = time.time() - bulk_start_ts
            avg_time_per_file = elapsed_bulk / index
            remaining_files = total_files - index
            
            if remaining_files > 0:
                eta_seconds = avg_time_per_file * remaining_files
                eta_str = str(timedelta(seconds=int(eta_seconds)))
                percent = (index / total_files) * 100
                
                click.secho(f"{tab}📈 Bulk Progress: {percent:.1f}% | ETA: {eta_str} remaining", fg="green")
                click.echo(f"{tab}{'-'*50}")

        except Exception as e:
            click.secho(f"{tab}❌ ERROR in file {index}: {e}", fg="red", bold=True)

    # 4. FINAL DETAILED REPORT
    bulk_end_dt = datetime.now()
    total_duration_sec = time.time() - bulk_start_ts
    total_duration_str = str(timedelta(seconds=int(total_duration_sec)))
    
    click.echo(f"\n{'='*60}")
    click.echo(f"✅ BULK COMPLETED")
    click.echo(f"{'='*60}")
    click.echo(f"📦 Product processed: {product}")
    click.echo(f"🔢 Total files:      {total_files}")
    click.echo(f"📅 Initial time:     {bulk_start_dt.strftime('%H:%M:%S')}")
    click.echo(f"📅 Final time:       {bulk_end_dt.strftime('%H:%M:%S')}")
    click.echo(f"⏱️  Total duration:   {total_duration_str} ({round(total_duration_sec/60, 2)} minutes)")
    click.echo(f"{'='*60}\n")
