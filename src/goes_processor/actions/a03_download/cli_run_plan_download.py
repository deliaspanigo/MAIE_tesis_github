# src/goes_processor/actions/a03_download/cli_run_plan_download.py
import click
import time
import re
from datetime import datetime
from .core01_run_plan_download.download import run_plan_download, PRODUCT_STRATEGY

# --- VALIDATORS ---
def validate_year(ctx, param, value):
    if not re.match(r'^\d{4}$', value):
        raise click.BadParameter('Year must be 4 digits (e.g., 2026)')
    return value

def validate_day(ctx, param, value):
    if not re.match(r'^\d{3}$', value):
        raise click.BadParameter('Day must be 3 digits (e.g., 003)')
    return value

def validate_hour(ctx, param, value):  # <--- Asegúrate que se llame así
    val = value.upper()
    if val == "ALL":
        return val
    if not re.match(r'^\d{2}$', val):
        raise click.BadParameter('Hour must be 2 digits (00-23) or "ALL"')
    hour_int = int(val)
    if not (0 <= hour_int <= 23):
        raise click.BadParameter('Hour must be between 00 and 23')
    return val

def validate_minute(ctx, param, value): # <--- Asegúrate que se llame así
    val = value.upper()
    if val == "ALL":
        return val
    if not re.match(r'^\d{2}$', val):
        raise click.BadParameter('Minute must be 2 digits or "ALL"')
    if val not in ['00', '10', '20', '30', '40', '50']:
        raise click.BadParameter('Minute must be 00, 10, 20, 30, 40, 50 or "ALL"')
    return val

# --- CLI COMMAND ---
@click.command(name="run-plan-download")
@click.option('--product', 
              type=click.Choice(list(PRODUCT_STRATEGY.keys()) + ["ALL"], case_sensitive=False), 
              required=True)
@click.option('--year', required=True, callback=validate_year)
@click.option('--day', required=True, callback=validate_day)
@click.option('--hour', type=str, required=True, callback=validate_hour, help="HH (00-23) or ALL")
@click.option('--minute', type=str,required=True, callback=validate_minute, help="mm (00-50) or ALL")
@click.option('--overwrite', required=True, type=click.Choice(['True', 'False'], case_sensitive=False))
@click.option('--check-again', required=True, type=click.Choice(['True', 'False'], case_sensitive=False))
def run_download_cmd(product, year, day, hour, minute, overwrite, check_again):
    """v.0.5.9.2 - Orchestrator with ALL/ALL Time Support"""
    
    start_ts = time.time()
    start_dt = datetime.now()
    
    target = product.upper()
    target_hour = hour.upper()
    target_min = minute.upper()
    
    overwrite_bool = overwrite.lower() == 'true'
    check_again_bool = check_again.lower() == 'true'
    
    tasks = list(PRODUCT_STRATEGY.keys()) if target == "ALL" else [target]
    
    # Header
    click.secho("\n" + "="*50, fg='cyan')
    click.secho("🚀 SATELLITE DOWNLOADER CLI v.0.5.9.2", fg='cyan', bold=True)
    click.echo(f"📅 System Start: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} - System Time")
    click.echo(f"📂 Target: {target} | Date: {year}-{day} | Time: {target_hour}:{target_min} UTC")
    click.echo(f"🔧 Config: Overwrite={overwrite_bool} | CheckAgain={check_again_bool}")
    click.secho("="*50 + "\n", fg='cyan')

    for p_name in tasks:
        #click.secho(f"📦 Downloading Product: {p_name}", fg='yellow', bold=True)
        try:
            # Se pasan hour y minute al core
            run_plan_download(
                year=year, 
                day=day, 
                hour=target_hour,
                minute=target_min,
                product=p_name,
                overwrite=overwrite_bool, 
                check_again=check_again_bool
            )
        except Exception as e:
            click.secho(f"❌ Critical Error in {p_name}: {str(e)}", fg='red', bold=True)

    # Footer Telemetry
    end_dt = datetime.now()
    total_diff = round(time.time() - start_ts, 2)

    click.secho("\n" + "="*50, fg='cyan')
    click.secho("🏁 CLOSING DOWNLOADER CLI", fg='cyan', bold=True)
    click.echo(f"📅 System Start: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} - System Time")
    click.echo(f"📅 System End:   {end_dt.strftime('%Y-%m-%d %H:%M:%S')} - System Time")
    click.echo(f"🕒 Duration: {total_diff} seconds")
    click.secho("✨ Operation completed successfully", fg='green', bold=True)
    click.secho("="*50 + "\n", fg='cyan')
