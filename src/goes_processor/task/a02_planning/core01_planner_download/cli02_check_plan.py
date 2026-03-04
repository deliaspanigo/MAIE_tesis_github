"""
Path: src/goes_processor/actions/a02_planning/core01_planner_download/cli02_check_plan.py
Version: 1.0.1 (Stable - ALL keyword support)
Description: CLI to verify the status of generated JSON plans. 
             Supports batch checking using the 'ALL' keyword.
"""

# =============================================================================
# 1. SYSTEM LIBRARY PROTECTION
# =============================================================================
try:
    import click
    import sys
    from pathlib import Path
except ImportError as e:
    print(f"\n❌ [CRITICAL ERROR] Missing core system libraries: {e}")
    raise SystemExit(1)

# =============================================================================
# 2. INTERNAL MODULE PROTECTION
# =============================================================================
try:
    # Source of Truth
    from goes_processor.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
    
    # Logic Engine
    try:
        from .code02_check_plan_download import execute_check_plan
    except (ImportError, ValueError):
        from goes_processor.actions.a02_planning.core01_planner_download.code02_check_plan_download import execute_check_plan

except ImportError as e:
    print("\n" + "!"*80)
    print(f" [CRITICAL ERROR] - Internal Module Mismatch")
    print("!"*80)
    print(f" Could not find components: {e}")
    print(f" Verify that 'src' is in your PYTHONPATH.")
    print("!"*80 + "\n")
    execute_check_plan = None

# =============================================================================
# 3. CLI COMMAND DEFINITION
# =============================================================================

@click.command(name="check-plan-download")
@click.option('--sat-position', required=True, type=click.Choice(['east', 'west']),
              help='Satellite position (east/west)')
@click.option('--product', required=True, 
              help="Product ID or 'ALL' to check every generated plan.")
@click.option('--year', required=True, type=int, help='Year (YYYY)')
@click.option('--day', required=True, type=str, help='Julian Day (DDD)')
def check_plan_command(sat_position, product, year, day):
    """
    Check if download plans exist and verify their internal status.
    """

    if execute_check_plan is None:
        click.echo(click.style("🚫 Logic engine (code02) is unavailable.", fg='red', bold=True))
        sys.exit(1)

    # --- A. Normalization & Validation ---
    product_input = product.strip().upper()
    
    if product_input == "ALL":
        products_to_process = AVAILABLE_GOES_PRODUCTS
        click.echo(click.style(f"🔍 Checking all available plans for {year}-{day}...", fg='cyan'))
    elif product_input in AVAILABLE_GOES_PRODUCTS:
        products_to_process = [product_input]
    else:
        click.echo(click.style(f"❌ ERROR: '{product}' is not a valid GOES product.", fg='red', bold=True))
        click.echo(f"🔍 Valid Options: {', '.join(AVAILABLE_GOES_PRODUCTS)} or 'ALL'")
        return

    # --- B. Status Audit Loop ---
    click.echo(f"📍 Satellite: {sat_position} | Date: {year}-{day}\n")

    for current_prod in products_to_process:
        click.echo(click.style(f"🧐 AUDIT: {current_prod}", fg='yellow', bold=True))
        
        try:
            # Call the checker engine
            execute_check_plan(
                sat_position=sat_position, 
                product=current_prod, 
                year=year, 
                day=day
            )
        except Exception as e:
            # If a JSON is missing, we catch the error here to allow the loop to continue
            click.echo(click.style(f"⚠️  Plan not found or corrupted for {current_prod}:", fg='red'))
            click.echo(f"   Details: {e}")
        
        click.echo("-" * 50)

    click.echo(click.style("🏁 Status check completed for all requested products.", reverse=True))

if __name__ == "__main__":
    check_plan_command()
