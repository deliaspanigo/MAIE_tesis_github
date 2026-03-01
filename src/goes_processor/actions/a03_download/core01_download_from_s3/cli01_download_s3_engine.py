"""
Path: src/goes_processor/actions/a03_download/core01_download_from_s3/cli01_download_s3_engine.py
Description: CLI for downloading GOES data based on existing JSON plans.
"""
import click
import sys

# Intentamos importar la lógica del motor
try:
    from .code01_download_s3_engine import execute_s3_download
except ImportError as e:
    # Si falla la importación relativa, intentamos la absoluta por si acaso
    try:
        from goes_processor.actions.a03_download.core01_download_from_s3.code01_download_s3_engine import execute_s3_download
    except ImportError as e2:
        print(f"❌ Critical Import Error in 'cli01_download_s3_engine.py': {e2}")
        execute_s3_download = None

@click.command(name="run-download-s3")
@click.option('--sat-position', required=True, type=click.Choice(['east', 'west']))
@click.option('--product', required=True)
@click.option('--year', required=True, type=int)
@click.option('--day', required=True, type=str)
@click.option('--threads', default=4, type=int, help='Number of parallel downloads')
def download_s3_command(sat_position, product, year, day, threads):
    """
    Executes the download process using a previously generated plan.
    """
    if execute_s3_download is None:
        click.echo("🚫 Logic engine (code01) is unavailable. Check imports.", err=True)
        return

    click.echo(f"🚀 Initializing download: {product} ({sat_position}) for {year}-{day}")
    
    try:
        execute_s3_download(sat_position, product, year, day, threads)
    except Exception as e:
        click.echo(f"💥 Execution Error: {e}", err=True)
