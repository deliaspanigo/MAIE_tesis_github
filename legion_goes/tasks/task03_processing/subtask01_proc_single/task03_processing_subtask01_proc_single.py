# =============================================================================
# FILE PATH: legion_goes/tasks/task03_processing/subtask01_proc_single/task03_processing_subtask01_proc_single.py
# Version: 1.0.0 (The Trinity: Generate -> Audit -> Run)
# =============================================================================

import time

# --- IMPORTACIÓN DE ACCIONES ---
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.action01_generate_plan_proc_single import run_action as action_01
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.action02_update_plan_audit_files import run_action as action_02
from legion_goes.tasks.task03_processing.subtask01_proc_single.actions.action03_run_executor_proc_single import run_action as action_03

def run_subtask_01(sat_id: str, product_id: str, year: str, day: str, fnp_tag: str = "fnp01") -> bool:
    """
    Orquestador Maestro: Ejecuta el pipeline completo de planificación y procesamiento.
    """
    ctx = "[SUBTASK 01 - MASTER]"
    start_all = time.time()
    
    print("\n" + f" INICIANDO PROCESAMIENTO COMPLETO: {product_id} G{sat_id} ".center(80, "="))
    print(f"📅 Fecha: Year {year}, Day {day} | Tag: {fnp_tag}")

    try:
        # --- PASO 1: GENERAR PLAN (THEORETICAL) ---
        print(f"\n🔹 [PASO 1/3] Generando/Verificando Plan JSON...")
        if not action_01(sat_id, product_id, year, day, fnp_tag):
            print(f"❌ {ctx} Falló la creación del plan. Abortando.")
            return False
        
        # --- PASO 2: AUDITAR DISCO (REALITY CHECK) ---
        print(f"\n🔹 [PASO 2/3] Auditando archivos en disco...")
        if not action_02(sat_id, product_id, year, day, fnp_tag):
            print(f"❌ {ctx} Falló la auditoría de archivos. Abortando.")
            return False

        # --- PASO 3: EJECUTAR (ACTION) ---
        print(f"\n🔹 [PASO 3/3] Despachando tareas al Executor...")
        if not action_03(sat_id, product_id, year, day, fnp_tag):
            print(f"❌ {ctx} Falló el despacho de ejecución.")
            return False

        # --- CIERRE ---
        total_time = round(time.time() - start_all, 2)
        print("\n" + f" ✨ PIPELINE FINALIZADO CON ÉXITO EN {total_time}s ".center(80, "=") + "\n")
        return True

    except Exception as e:
        print(f"\n💥 {ctx} ERROR CRÍTICO NO CONTROLADO: {e}")
        return False

# =============================================================================
# MAIN: EJECUCIÓN DEL DÍA COMPLETO
# =============================================================================
if __name__ == "__main__":
    # Parámetros para procesar todo el día 003 de LSTF
    params = {
        "sat_id": "19", 
        "product_id": "ABI-L2-LSTF", 
        "year": "2026", 
        "day": "003", 
        "fnp_tag": "fnp01"
    }
    
    run_subtask_01(**params)
