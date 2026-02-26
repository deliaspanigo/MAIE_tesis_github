import click
import time
import json
from pathlib import Path

# --- My Libraries ---
from .gen_plan import generate_download_plan_day
from .check_plan import check_local_file_existence
from goes_processor.HARDCODED_FOLDERS import get_my_path

# 🛠️ CORRECCIÓN: Eliminada la referencia a 'goes_info' y unificada a 'info'
from goes_processor.info.goes_prod import AVAILABLE_PRODUCTS
from goes_processor.utils.file_names import get_plan_file_name


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
            raise KeyError(
                f"\n[STRICT ERROR] Attempted to add new key: '{key}'.\n"
                f"Only existing keys defined in the plan template are allowed."
            )
        super().__setitem__(key, value)


# --- SAVE FUNCTION ---
def save_plan_dict_as_json(plan_dict: dict, overwrite: bool = True):
    """
    Saves (or overwrites) the plan using the centralized naming convention (name06).
    """
    base_output_dir = get_my_path("plan_download")
    
    p_info = plan_dict.get("prod_info", {})
    year = p_info.get("year", "unknown")
    day = p_info.get("day", "unknown")
    
    # Limpiamos el sat_id para asegurar que sea solo el número (ej: '19')
    sat_id_raw = str(p_info.get("satellite", "unknown")).replace("GOES-", "").replace("goes", "")
    sat_position = p_info.get("sat_position", "unknown")
    product = p_info.get("product", "unknown")

    # 🔄 Usamos la utilidad maestra que genera 'plan_download_..._GOES19_...'
    file_name = get_plan_file_name(
        year=year, 
        day=day, 
        sat_id=sat_id_raw, 
        sat_position=sat_position, 
        product_id=product
    )
    
    target_dir = base_output_dir / year / day
    target_dir.mkdir(parents=True, exist_ok=True)
    path_absolute = target_dir / file_name

    try:
        try:
            path_display = str(path_absolute.relative_to(Path.cwd()))
        except ValueError:
            path_display = str(path_absolute)
        
        # Actualizamos la info interna del JSON
        plan_dict["planner_download_info"]["file_name"] = file_name
        plan_dict["planner_download_info"]["path_relative"] = path_display
        plan_dict["planner_download_info"]["path_absolute"] = str(path_absolute.resolve())

        with open(path_absolute, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=4, ensure_ascii=False)
        
        click.secho(f"    🔄 Updated: {path_display}", fg='blue')
        return True
    except Exception as e:
        click.secho(f"    ❌ Error updating {file_name}: {e}", fg='red')
        return False


# --- CLI COMMAND ---
@click.command(name="check-plan-download")
@click.option('--product', type=click.Choice(AVAILABLE_PRODUCTS, case_sensitive=False), 
              required=True, help="Product to check or ALL")
@click.option('--year', required=True, help="Year (YYYY)")
@click.option('--day', required=True, help="Julian day (DDD)")
@click.option('--sat-position', type=click.Choice(['east', 'west', 'ALL'], case_sensitive=False), 
              required=True, help="Satellite position")
def check_plan_cmd(product, year, day, sat_position):
    """Check local existence on existing plans and update them."""
    start_ts = time.time()
    
    click.secho(f"\n🔍 Checking Plans - Product: {product} | Year: {year} | Day: {day} | Position: {sat_position}", 
                fg='blue', bold=True)

    try:
        products_to_process = [p for p in AVAILABLE_PRODUCTS if p != "ALL"] if product == "ALL" else [product]
        positions_to_process = ["east", "west"] if sat_position == "ALL" else [sat_position.lower()]

        updated_count = 0

        for prod in products_to_process:
            for pos in positions_to_process:
                # Generamos el plan base
                plan = generate_download_plan_day(
                    product_id=prod,
                    year=year,
                    day=day,
                    sat_position=pos
                )

                # Verificamos archivos locales (.nc)
                updated_plan = check_local_file_existence(plan)
                
                # Protegemos estructura
                strict_plan = StrictDict(updated_plan)
                
                # Guardamos con el nombre unificado
                if save_plan_dict_as_json(strict_plan, overwrite=True):
                    updated_count += 1

        if updated_count == 0:
            click.secho("    ℹ️ No plans were updated.", fg='yellow')

    except Exception as e:
        click.secho(f"    💥 Critical Error: {e}", fg='red')

    duration = round(time.time() - start_ts, 2)
    click.secho(f"\n✨ Check finished in {duration}s.\n", fg='green', bold=True)

if __name__ == "__main__":
    check_plan_cmd()
