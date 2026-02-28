# =============================================================================
# FILE PATH: src/goes_processor/actions/a02_planning/a02_planning_cli.py
# Version: 0.1.8 (Final Naming Sync)
# =============================================================================

import click

# IMPORTACIONES PROTEGIDAS
try:
    from .core01_planner_download.cli01_gen_plan_download import gen_plan_cmd
    from .core01_planner_download.cli02_check_plan import check_plan_cmd
except ImportError as e:
    click.secho(f"\n💥 [ROUTER ERROR] Could not find CLI modules: {e}", fg='red', bold=True)
    raise SystemExit(1)

@click.group()
def planning_group():
    """MASTER PLANNING INTERFACE - GOES Processor"""
    pass

# --- REGISTRO CON EL NOMBRE QUE TÚ QUIERES ---
# Al poner name="gen-plan-download", Click esperará esa frase exacta en la terminal
planning_group.add_command(gen_plan_cmd, name="gen-plan-download")
planning_group.add_command(check_plan_cmd, name="check-plan-download")

# Alias para el main.py
planning = planning_group

if __name__ == '__main__':
    planning_group()
