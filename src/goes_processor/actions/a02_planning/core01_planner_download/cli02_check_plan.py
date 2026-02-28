# =============================================================================
# FILE PATH: src/goes_processor/actions/a02_planning/core01_planner_download/cli02_check_plan.py
# Version: 0.1.9 (Legion Shielded - Sincronizado con code01)
# =============================================================================

MY_NAME = "cli02_check_plan.py"

# 1. CAPA DE SISTEMA
try:
    import click
    import time
    import json
    from pathlib import Path
except ImportError as e:
    print(f"\n [SYSTEM ERROR] - In {MY_NAME}: {e}\n")
    raise SystemExit(1)

# 2. CAPA DE PROYECTO
try:
    from .code01_gen_plan_download import generate_download_plan_day
    from .code02_check_plan_download import check_dict_download_plan_day
    from .fn01_file_name_plan_download import get_plan_download_file_name, get_plan_download_file_path

    from goes_processor.SoT.goes_prod import AVAILABLE_GOES_PRODUCTS
    from goes_processor.SoT.goes_sat import AVAILABLE_GOES_SAT_POSITIONS

    PROD_CHOICES = ["ALL"] + list(AVAILABLE_GOES_PRODUCTS)
    SAT_CHOICES = ["ALL"] + list(AVAILABLE_GOES_SAT_POSITIONS)

except ImportError as e:
    print(f"\n [PROJECT LIB ERROR] - File: {MY_NAME}: {e}\n")
    raise SystemExit(1)

# =============================================================================
# SCHEMA PROTECTION
# =============================================================================
class StrictDict(dict):
    def __init__(self, data):
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = StrictDict(value)
        super().__init__(data)

    def __setitem__(self, key, value):
        if key not in self:
            raise KeyError(f"\n[STRICT ERROR] Key '{key}' not allowed.\n")
        super().__setitem__(key, value)

# =============================================================================
# PERSISTENCE LOGIC
# =============================================================================
def save_plan_dict_as_json(plan_dict: dict, year: str, day: str):
    """Guarda el plan usando los datos validados del CLI."""
    
    p_info = plan_dict.get("sat_prod_info", {})
    s_info = plan_dict.get("plan_download_self_info", {})
    
    # Extraemos el ID del satélite de "GOES-19" -> "19"
    sat_raw = str(p_info.get("satellite", "19"))
    sat_id_raw = sat_raw.replace("GOES-", "").replace("goes", "")
    
    # Usamos los parámetros year/day que vienen del comando Click (son los más seguros)
    sat_pos = p_info.get("sat_position", "unknown")
    prod = p_info.get("product_id", "unknown")

    try:
        # Generar nombres y rutas oficiales
        file_name = get_plan_download_file_name(year, day, sat_id_raw, sat_pos, prod)
        path_abs = get_plan_download_file_path(year, day, sat_id_raw, sat_pos, prod)
        
        path_abs.parent.mkdir(parents=True, exist_ok=True)
        
        # Actualizar la metadata interna del JSON antes de guardar
        if "plan_download_self_info" in plan_dict:
            plan_dict["plan_download_self_info"]["file_name"] = file_name
            plan_dict["plan_download_self_info"]["path_absolute"] = str(path_abs.resolve())

        with open(path_abs, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=4, ensure_ascii=False)
        
        click.secho(f"    🔄 Updated & Saved: {file_name}", fg='blue')
        return True
    except Exception as e:
        click.secho(f"    ❌ Save Error: {e}", fg='red')
        return False

# =============================================================================
# CLI COMMAND
# =============================================================================
@click.command(name="check-plan-download")
@click.option('--sat-position', type=click.Choice(SAT_CHOICES, case_sensitive=False), required=True)
@click.option('--product', type=click.Choice(PROD_CHOICES, case_sensitive=False), required=True)
@click.option('--year', required=True)
@click.option('--day', required=True)
def check_plan_cmd(product, year, day, sat_position):
    """🔍 CHECKER: Cruza planes JSON contra archivos reales en disco."""
    start_ts = time.time()
    
    click.secho(f"\n" + "="*60, fg='blue')
    click.secho(f"🔍 CHECKING PLANS: {product} | {year}-{day} | {sat_position}", fg='blue', bold=True)
    click.secho("="*60, fg='blue')

    try:
        prods = list(AVAILABLE_GOES_PRODUCTS) if product.upper() == "ALL" else [product.upper()]
        poses = [p.lower() for p in AVAILABLE_GOES_SAT_POSITIONS] if sat_position.upper() == "ALL" else [sat_position.lower()]

        updated_count = 0

        for p in prods:
            for s in poses:
                click.echo(f"  👉 Checking local files: {p} on GOES-{s}...")
                
                # 1. Generar plan base (usando tu code01)
                plan = generate_download_plan_day(sat_position=s, product_id=p, year=year, day=day)

                # 2. Escanear disco (usando tu code02)
                updated_plan = check_dict_download_plan_day(plan)
                
                # 3. Guardar pasando year y day explícitamente para evitar el error de "unknown"
                strict_plan = StrictDict(updated_plan)
                if save_plan_dict_as_json(strict_plan, year, day):
                    updated_count += 1

        if updated_count > 0:
            click.secho(f"\n✨ Success: {updated_count} plan(s) synchronized.", fg='green', bold=True)
        else:
            click.secho(f"\n⚠️ Warning: No plans were updated.", fg='yellow')

    except Exception as e:
        click.secho(f"\n💥 [RUNTIME ERROR] {e}", fg='red', bold=True)
        raise SystemExit(1)

    duration = round(time.time() - start_ts, 2)
    click.echo(f"⏱️ Finished in {duration}s.\n")

if __name__ == '__main__':
    check_plan_cmd()
