# src/goes_processor/actions/a02_planner/cli_core01_p01_download.py

# =============================================================================
# FILE PATH:
# src/goes_processor/actions/a02_planner/cli_core01_p01_download.py
#
# Purpose: CLI commands for GOES L2 download planning and checking.
#          - gen-plan: Generates plans + check + save
#          - check-plan: Only checks local existence and updates existing plans
#
# Features:
#   - All arguments are explicit, mandatory, and closed-choice (no flags)
#   - Strict True/False (case-sensitive: only "True" or "False" accepted)
#   - Supports "ALL" for product and sat-position
#   - Uses generic planner and check functions
#   - Saves files with clear naming: plan_download_YYYY_DDD_GXX_pos_PRODUCT.json
#   - StrictDict protection
#   - Automatic validation of product choices against GOES_PRODUCTS
#
# Usage examples:
#   goes-processor gen-plan --product ALL --year 2026 --day 003 --sat-position ALL --save True --overwrite True --check-local True
#   goes-processor check-plan --product ALL --year 2026 --day 003 --sat-position ALL
# =============================================================================

import click
import time
from pathlib import Path

# --- My Libraries ---
from .core01_planner01_download.gen_plan import generate_download_plan_day
from .core01_planner01_download.check_plan import check_local_file_existence
from goes_processor.HARDCODED_FOLDERS import get_my_path
from goes_processor.info.goes_prod import AVAILABLE_PRODUCTS


# --- STRICT DICT ---
class StrictDict(dict):
    """Strict dictionary that prevents adding new keys after creation."""
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = StrictDict(value)
        super().__init__(data)

    def __setitem__(self, key, value):
        if key not in self:
            raise KeyError(f"[STRICT ERROR] Cannot add new key: '{key}'")
        super().__setitem__(key, value)


# --- SAVE FUNCTION ---
def save_plan_dict_as_json(plan_dict: dict, overwrite: bool):
    """
    Saves the plan as a JSON file with descriptive name.
    """
    base_output_dir = get_my_path("plan_download")
    
    p_info = plan_dict.get("prod_info", {})
    year = p_info.get("year", "unknown")
    day = p_info.get("day", "unknown")
    sat_id = p_info.get("satellite", "unknown").replace("GOES-", "")
    sat_position = p_info.get("sat_position", "unknown")
    product = p_info.get("product", "unknown")

    file_name = f"plan_download_{year}_{day}_{sat_id}_{sat_position}_{product}.json"
    
    target_dir = base_output_dir / year / day
    target_dir.mkdir(parents=True, exist_ok=True)
    
    path_absolute = target_dir / file_name

    if path_absolute.exists() and not overwrite:
        click.secho(f"   ⏩ Skipped (already exists): {file_name}", fg='yellow')
        return True

    try:
        path_relative = str(path_absolute.relative_to(Path.cwd()))
        
        plan_dict["planner_download_info"]["file_name"] = file_name
        plan_dict["planner_download_info"]["path_relative"] = path_relative
        plan_dict["planner_download_info"]["path_absolute"] = str(path_absolute.resolve())

        with open(path_absolute, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=4, ensure_ascii=False)
        
        click.secho(f"   ✅ Saved: {path_relative}", fg='green')
        return True
    except Exception as e:
        click.secho(f"   ❌ Error saving {file_name}: {e}", fg='red')
        return False


# --- COMMAND 1: Generate Plan ---
@click.command(name="gen-plan")
@click.option('--product', type=click.Choice(AVAILABLE_PRODUCTS, case_sensitive=False), 
              required=True, 
              help="Product to process or ALL")
@click.option('--year', required=True, help="Year (YYYY)")
@click.option('--day', required=True, help="Julian day (DDD)")
@click.option('--sat-position', type=click.Choice(['east', 'west', 'ALL'], case_sensitive=False), 
              required=True, 
              help="Satellite position")
@click.option('--save', type=click.Choice(['True', 'False'], case_sensitive=True), 
              required=True, 
              help="Save plans to disk: True or False (exact case)")
@click.option('--overwrite', type=click.Choice(['True', 'False'], case_sensitive=True), 
              required=True, 
              help="Overwrite existing plans: True or False (exact case)")
@click.option('--check-local', type=click.Choice(['True', 'False'], case_sensitive=True), 
              required=True, 
              help="Check local file existence before saving: True or False (exact case)")
def run_gen_plan_cmd(product, year, day, sat_position, save, overwrite, check_local):
    """Generate download plans for GOES L2 products."""
    start_ts = time.time()
    
    click.secho(f"\n🚀 Generating Plans - Product: {product} | Year: {year} | Day: {day} | Position: {sat_position}", 
                fg='cyan', bold=True)

    try:
        plans = generate_download_plan_day(
            product_id=product,
            year=year,
            day=day,
            sat_position=sat_position
        )

        if isinstance(plans, dict):
            plans = [plans]

        # Optional: Check local existence
        if check_local == 'True':
            plans = check_local_file_existence(plans)

        saved_paths = []

        for plan_dict in plans:
            strict_plan = StrictDict(plan_dict)
            
            if save == 'True':
                file_path = save_plan_dict_as_json(strict_plan, overwrite == 'True')
                if file_path:
                    saved_paths.append(file_path)
            else:
                click.echo(json.dumps(strict_plan, indent=4))

        if save == 'True' and saved_paths:
            click.secho(f"\nAll plans saved to: {get_my_path('plan_download')}", fg='green')

    except Exception as e:
        click.secho(f"   💥 Critical Error: {e}", fg='red')

    duration = round(time.time() - start_ts, 2)
    click.secho(f"\n✨ Finished in {duration}s.\n", fg='green', bold=True)


# --- COMMAND 2: Check Existing Plans ---
@click.command(name="check-plan")
@click.option('--product', type=click.Choice(AVAILABLE_PRODUCTS, case_sensitive=False), 
              required=True, 
              help="Product to check or ALL")
@click.option('--year', required=True, help="Year (YYYY)")
@click.option('--day', required=True, help="Julian day (DDD)")
@click.option('--sat-position', type=click.Choice(['east', 'west', 'ALL'], case_sensitive=False), 
              required=True, 
              help="Satellite position")
def run_check_plan_cmd(product, year, day, sat_position):
    """Check local existence on existing plans and update them (always overwrites)."""
    start_ts = time.time()
    
    click.secho(f"\n🔍 Checking Plans - Product: {product} | Year: {year} | Day: {day} | Position: {sat_position}", 
                fg='blue', bold=True)

    try:
        plans = generate_download_plan_day(
            product_id=product,
            year=year,
            day=day,
            sat_position=sat_position
        )

        if isinstance(plans, dict):
            plans = [plans]

        updated_count = 0

        for plan_dict in plans:
            updated_plan = check_local_file_existence(plan_dict)
            strict_plan = StrictDict(updated_plan)
            if save_plan_dict_as_json(strict_plan, overwrite=True):
                updated_count += 1

        if updated_count == 0:
            click.secho("   ℹ️ No plans were updated (possibly no files found or no changes).", fg='yellow')

    except Exception as e:
        click.secho(f"   💥 Critical Error: {e}", fg='red')

    duration = round(time.time() - start_ts, 2)
    click.secho(f"\n✨ Check finished in {duration}s.\n", fg='green', bold=True)


# Register both commands in the group
cli = click.Group()
cli.add_command(run_gen_plan_cmd)
cli.add_command(run_check_plan_cmd)

if __name__ == "__main__":
    cli()
