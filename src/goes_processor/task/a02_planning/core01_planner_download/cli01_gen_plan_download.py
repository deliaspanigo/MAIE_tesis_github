"""
Path: src/goes_processor/actions/a02_planning/core01_planner_download/cli01_gen_plan_download.py
Version: 1.0.1 (Corrected SoT Path)
"""

try:
    import click
    import sys
    from pathlib import Path
except ImportError as e:
    print(f"\n❌ [CRITICAL ERROR] Missing core system libraries: {e}")
    raise SystemExit(1)

try:
    # --- CORRECTED IMPORT PATH ---
    # We changed 'info' to 'SoT' to match your folder structure
    from goes_processor.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
    
    try:
        from .code01_gen_plan_download import execute_gen_plan
    except (ImportError, ValueError):
        from goes_processor.actions.a02_planning.core01_planner_download.code01_gen_plan_download import execute_gen_plan

except ImportError as e:
    print("\n" + "!"*80)
    print(f" [CRITICAL ERROR] - Internal Module Mismatch")
    print("!"*80)
    print(f" Could not find: {e}")
    print(f" Current Directory: {Path.cwd()}")
    print(" Verify that 'src' is in your PYTHONPATH.")
    print("!"*80 + "\n")
    execute_gen_plan = None

@click.command(name="gen-plan-download")
@click.option('--sat-position', required=True, type=click.Choice(['east', 'west']))
@click.option('--product', required=True)
@click.option('--year', required=True, type=int)
@click.option('--day', required=True, type=str)
@click.option('--overwrite', default=False, type=bool)
@click.option('--check-local', default=True, type=bool)
def gen_plan_download_command(sat_position, product, year, day, overwrite, check_local):
    """GOES Download Planning Interface."""

    if execute_gen_plan is None:
        click.echo(click.style("🚫 Planning engine is unavailable.", fg='red', bold=True))
        sys.exit(1)

    product_input = product.strip().upper()
    
    if product_input == "ALL":
        products_to_process = AVAILABLE_GOES_PRODUCTS
        click.echo(click.style(f"📦 'ALL' mode active. Queueing {len(products_to_process)} products.", fg='cyan'))
    elif product_input in AVAILABLE_GOES_PRODUCTS:
        products_to_process = [product_input]
    else:
        click.echo(click.style(f"❌ ERROR: '{product}' is not valid.", fg='red', bold=True))
        click.echo(f"🔍 Valid Options: {', '.join(AVAILABLE_GOES_PRODUCTS)} or 'ALL'")
        return

    for current_prod in products_to_process:
        click.echo(click.style(f"🛠️  Planning: {current_prod}", fg='green', bold=True))
        try:
            execute_gen_plan(sat_position, current_prod, year, day, overwrite, check_local)
            click.echo(f"✅ Success: {current_prod} plan ready.\n")
        except Exception as e:
            click.echo(click.style(f"💥 Error in {current_prod}: {e}", fg='red'), err=True)

if __name__ == "__main__":
    gen_plan_download_command()
