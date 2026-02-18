import click
from .core.download_goes_files import download_goes_files

@click.group(name="download")
def download():
    """GOES satellite data download management."""
    pass

@download.command(name="goes-files")
@click.option('--satellite', required=True, type=click.Choice(["16", "17", "18", "19"]))
@click.option('--product', required=True)
@click.option('--year', required=True)
@click.option('--day', required=True)
@click.option('--hour', required=True)
@click.option('--minute', required=True)
@click.option('--output-dir', required=True)
@click.option('--overwrite', type=click.Choice(['yes', 'no']), required=True)
def download_files_cli(satellite, product, year, day, hour, minute, output_dir, overwrite):
    """v.0.3.0 - Strict download with Legion validation."""
    
    # --- PUNTOS DE CONTROL LEGION ---
    if hour != "all":
        try:
            h_int = int(hour)
            if not (0 <= h_int <= 23): raise ValueError
            hour = str(h_int).zfill(2)
        except ValueError:
            click.secho(f"\n[LEGION-VALIDATION-ERROR] Invalid Hour: '{hour}'. Must be 00-23 or 'all'.", fg="red", bold=True)
            return # Detiene la ejecución de forma segura

    if minute != "all":
        try:
            m_int = int(minute)
            if not (0 <= m_int <= 59): raise ValueError
            minute = str(m_int).zfill(2)
        except ValueError:
            click.secho(f"\n[LEGION-VALIDATION-ERROR] Invalid Minute: '{minute}'. Must be 00-59 or 'all'.", fg="red", bold=True)
            return

    day_padded = day.zfill(3)
    should_overwrite = (overwrite == 'yes')

    # --- EXECUTION ---
    try:
        click.echo(f"\n[*] Initializing download for {product} (GOES-{satellite})...")
        download_goes_files(
            satellite=satellite,
            product=product,
            year=year,
            day_of_year=day_padded,
            hour=hour,
            minute=minute,
            overwrite=should_overwrite,
            output_dir=output_dir
        )
        click.secho("\n✅ Download process finished successfully.", fg="green", bold=True)
    except Exception as e:
        click.secho(f"\n[LEGION-SYSTEM-ERROR] {e}", fg="yellow", bold=True)
