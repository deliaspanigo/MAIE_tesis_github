# =============================================================================
# FILE PATH:
# src/goes_processor/actions/a02_planning/core01_planner_download/gen_plan_cli.py
#
# Purpose: CLI command to generate download plans for GOES L2 products.
# Handles "ALL" logic (loop over products/positions), generates plans,
# optionally checks local files, and saves them to disk.
# Uses the generic planner from gen_plan.py.
#
# Features:
#   - All arguments are explicit and mandatory (no flags)
#   - Closed choices for product and sat-position
#   - Strict True/False (case-sensitive: only "True" or "False" accepted)
#   - Supports "ALL" for product and sat-position
#   - Saves files with consistent naming via utils/file_names.py
#   - StrictDict protection before saving
#   - Optional local file existence check before saving
#
# Usage examples:
#   goes-processor planning gen-plan-download --product ALL --year 2026 --day 003 --sat-position ALL --save True --overwrite True --check-local True
#   goes-processor planning gen-plan-download --product ABI-L2-LSTF --year 2026 --day 003 --sat-position east --save False --overwrite False --check-local False
# =============================================================================

import click
import json
import time
from pathlib import Path

# --- My Libraries ---
from .gen_plan import generate_download_plan_day
from .check_plan import check_local_file_existence
from goes_processor.utils.file_names import get_plan_path
from goes_processor.info.goes_prod import AVAILABLE_PRODUCTS
from goes_processor.HARDCODED_FOLDERS import get_my_path


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


# --- CLI COMMAND ---
@click.command(name="gen-plan-download")
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
def gen_plan_cmd(product, year, day, sat_position, save, overwrite, check_local):
    """Generate download plans for GOES L2 products."""
    start_ts = time.time()
    
    click.secho(f"\n🚀 Generating Plans - Product: {product} | Year: {year} | Day: {day} | Position: {sat_position}", 
                fg='cyan', bold=True)

    try:
        # Handle "ALL" logic in the CLI only
        if product == "ALL":
            products_to_process = [p for p in AVAILABLE_PRODUCTS if p != "ALL"]
        else:
            products_to_process = [product]

        if sat_position == "ALL":
            positions_to_process = ["east", "west"]
        else:
            positions_to_process = [sat_position.lower()]

        saved_paths = []

        for prod in products_to_process:
            for pos in positions_to_process:
                # Generate single plan
                plan = generate_download_plan_day(
                    product_id=prod,
                    year=year,
                    day=day,
                    sat_position=pos
                )

                # Optional: Check local existence
                if check_local == 'True':
                    plan = check_local_file_existence(plan)

                # Protect with StrictDict
                strict_plan = StrictDict(plan)

                # Save if requested
                if save == 'True':
                    file_path = _save_single_plan(strict_plan, year, day, prod, pos, overwrite == 'True')
                    if file_path:
                        saved_paths.append(file_path)
                else:
                    # Print to console
                    click.echo(json.dumps(strict_plan, indent=4))

        if save == 'True' and saved_paths:
            click.secho(f"\nAll plans saved to: {get_my_path('plan_download')}", fg='green')

    except Exception as e:
        click.secho(f"   💥 Critical Error: {e}", fg='red')

    duration = round(time.time() - start_ts, 2)
    click.secho(f"\n✨ Finished in {duration}s.\n", fg='green', bold=True)


def _save_single_plan(plan_dict: dict, year: str, day: str, product_id: str, sat_position: str, overwrite: bool) -> Path | None:
    """
    Saves a single plan as a JSON file using the centralized file name generator.
    Returns the absolute path if saved, None if skipped or failed.
    """
    # Use centralized function to get the path
    file_path = get_plan_path(
        year=year,
        day=day,
        sat_id=plan_dict['prod_info']['satellite'].replace("GOES-", ""),
        sat_position=sat_position,
        product_id=product_id
    )

    if file_path.exists() and not overwrite:
        click.secho(f"   ⏩ Skipped (already exists): {file_path.name}", fg='yellow')
        return None

    try:
        path_relative = str(file_path.relative_to(Path.cwd()))
        
        # Update paths in the plan
        plan_dict["planner_download_info"]["file_name"] = file_path.name
        plan_dict["planner_download_info"]["path_relative"] = path_relative
        plan_dict["planner_download_info"]["path_absolute"] = str(file_path.resolve())

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=4, ensure_ascii=False)
        
        click.secho(f"   ✅ Saved: {path_relative}", fg='green')
        return file_path
    except Exception as e:
        click.secho(f"   ❌ Error saving {file_path.name}: {e}", fg='red')
        return None


# Optional: Allow direct execution for testing
if __name__ == "__main__":
    gen_plan_cmd()
