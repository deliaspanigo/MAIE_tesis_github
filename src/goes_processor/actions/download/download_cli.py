import click
# Import logic from the new core directory
from .core.download_goes_files import download_goes_files

@click.group(name="download")
def download():
    """GOES satellite data download management."""
    pass

@download.command(name="goes-files")
@click.option('--satellite', 
              default="19", 
              type=click.Choice(["16", "17", "18", "19"]), 
              help='GOES Satellite number (16, 17, 18, 19).')
@click.option('--product', 
              required=True, 
              help='Product name (e.g., ABI-L2-LSTF, GLM-L2-LCFA).')
@click.option('--year', 
              required=True, 
              help='Year in YYYY format.')
@click.option('--day', 
              required=True, 
              help='Day of the year in DDD format.')
@click.option('--hour', 
              default="all", 
              help='Hour (HH) or "all".')
@click.option('--minute', 
              default="all", 
              help='Minute (MM) or "all".')
@click.option('--output-dir', 
              default="data/raw", 
              help='Target root directory for downloads.')
@click.option('--overwrite', 
              type=click.Choice(['yes', 'no']), 
              default='no', 
              help='Force download even if file exists (yes/no).')
              
              
def download_files_cli(satellite, product, year, day, hour, minute, overwrite, output_dir):
    """
    Download NetCDF files from NOAA S3 with weight validation.
    Maintains structure: output_dir/noaa-goesX/product/year/day/hour/
    """
    
    # 1. Validate Hour format
    if hour != "all":
        try:
            h_int = int(hour)
            if not (0 <= h_int <= 23):
                raise ValueError
            hour = str(h_int).zfill(2)
        except ValueError:
            raise click.BadParameter("Hour must be between 00 and 23.")

    # 2. Validate Minute format
    if minute != "all":
        try:
            m_int = int(minute)
            if not (0 <= m_int <= 59):
                raise ValueError
            minute = str(m_int).zfill(2)
        except ValueError:
            raise click.BadParameter("Minute must be between 00 and 59.")

    # 3. Format Day of Year (DDD)
    day_padded = day.zfill(3)

    # 4. Convert overwrite string to Boolean for the core function
    should_overwrite = (overwrite == 'yes')

    # --- EXECUTION ---
    try:
        click.echo(f"\n[*] Initializing download for {product} (GOES-{satellite})...")
        
        # Call the core logic now located in core/download_goes_files.py
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
        click.secho(f"\n[!] CRITICAL CLI ERROR: {e}", fg="red", bold=True)
