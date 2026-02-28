# =============================================================================
# FILE PATH: src/goes_processor/actions/a02_planning/core01_planner_download/cli01_gen_plan_download.py
# Version: 0.1.8 (Fixed SoT Path)
# =============================================================================

MY_NAME = "cli01_gen_plan_download.py"

# 1. CAPA DE SISTEMA
try:
    import click
    import json
    import time
    from pathlib import Path
except ImportError as e:
    print(f"\n [SYSTEM ERROR] - In {MY_NAME}: {e}\n")
    raise SystemExit(1)

# 2. CAPA DE PROYECTO (Apuntando a la carpeta SoT)
try:
    # Lógica de generación y chequeo
    from .code01_gen_plan_download import generate_download_plan_day
    from .code02_check_plan_download import check_dict_download_plan_day

    # IMPORTACIONES CORREGIDAS A 'SoT'
    from goes_processor.SoT.goes_prod import SAVED_INFO_PROD_GOES, AVAILABLE_GOES_PRODUCTS
    from goes_processor.SoT.goes_sat import AVAILABLE_GOES_SAT_POSITIONS
    
    # Construcción dinámica de opciones para el CLI
    PROD_CHOICES = ["ALL"] + list(AVAILABLE_GOES_PRODUCTS)
    SAT_CHOICES = ["ALL"] + list(AVAILABLE_GOES_SAT_POSITIONS)

except ImportError as e:
    print("\n" + "="*80)
    print(f" [PROJECT LIB ERROR] - In {MY_NAME}")
    print(f" Failed to load SoT from 'SoT' folder: {e}")
    print("="*80 + "\n")
    raise SystemExit(1)

# =============================================================================
# STRICT DICT PROTECTION
# =============================================================================
class StrictDict(dict):
    """Protección de esquema para evitar llaves accidentales en el JSON."""
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = StrictDict(value)
        super().__init__(data)

    def __setitem__(self, key, value):
        if key not in self:
            raise KeyError(f"[STRICT ERROR] Schema Violation: Key '{key}' is not allowed.")
        super().__setitem__(key, value)

# =============================================================================
# CLI COMMAND DEFINITION
# =============================================================================

@click.command(name="gen-plan-download")
@click.option('--sat-position', 
              required=True, 
              type=click.Choice(SAT_CHOICES, case_sensitive=True), 
              help="Satellite position (east, west) or ALL.")
@click.option('--product', 
              required=True, 
              type=click.Choice(PROD_CHOICES, case_sensitive=True), 
              help="Product ID (e.g., ABI-L2-LSTF) or ALL.")
@click.option('--year', required=True, help="Year (YYYY)")
@click.option('--day', required=True, help="Julian day (001-366)")
@click.option('--overwrite', required=True, type=bool, help="Overwrite existing plan?")
@click.option('--check-local', required=True, type=bool, help="Scan local disk for files?")

def gen_plan_cmd(product, year, day, sat_position, overwrite, check_local):
    """Generate and SAVE download plans using SoT-Strict."""
    start_ts = time.time()
    
    click.secho(f"\n🚀 Planning Download | {product} | {year}-{day} | {sat_position}", fg='cyan', bold=True)

    try:
        # Resolver listas de procesamiento basándonos en SAVED_INFO_PROD_GOES (MappingProxy)
        products_to_process = list(SAVED_INFO_PROD_GOES.keys()) if product == "ALL" else [product]
        
        if sat_position == "ALL":
            positions_to_process = [p.lower() for p in AVAILABLE_GOES_SAT_POSITIONS]
        else:
            positions_to_process = [sat_position.lower()]

        saved_count = 0

        for prod in products_to_process:
            for pos in positions_to_process:
                # A. Generar plan base
                plan = generate_download_plan_day(
                    product_id=prod,
                    year=year,
                    day=day,
                    sat_position=pos
                )

                # B. Verificación de archivos locales
                if check_local:
                    plan = check_dict_download_plan_day(plan)

                # C. Bloqueo de esquema
                strict_plan = StrictDict(plan)

                # D. Guardar
                file_path = _save_single_plan(strict_plan, overwrite)
                if file_path:
                    saved_count += 1

        if saved_count > 0:
            click.secho(f"\n✨ {saved_count} plan(s) successfully generated.", fg='green', bold=True)
        else:
            click.secho(f"\n⚠️ No plans saved.", fg='yellow')

    except Exception as e:
        click.secho(f"\n💥 [CLI ERROR] {e}", fg='red', bold=True)
        raise SystemExit(1)

    duration = round(time.time() - start_ts, 2)
    click.secho(f"⏱️ Finished in {duration}s.\n", fg='white', dim=True)

def _save_single_plan(plan_dict: dict, overwrite: bool) -> Path | None:
    info = plan_dict.get("plan_download_self_info", {})
    path_str = info.get("path_absolute")
    file_name = info.get("file_name", "unknown.json")

    if not path_str:
        return None

    path_absolute = Path(path_str)

    if path_absolute.exists() and not overwrite:
        click.secho(f"    ⏩ Skipped: {file_name}", fg='yellow')
        return None

    try:
        path_absolute.parent.mkdir(parents=True, exist_ok=True)
        with open(path_absolute, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=4, ensure_ascii=False)
        
        click.secho(f"    ✅ Saved: {file_name}", fg='green')
        return path_absolute
    except Exception as e:
        click.secho(f"    ❌ Error saving {file_name}: {e}", fg='red')
        return None

if __name__ == '__main__':
    gen_plan_cmd()
