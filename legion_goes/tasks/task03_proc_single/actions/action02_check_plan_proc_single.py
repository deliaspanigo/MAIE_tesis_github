# =============================================================================
# PATH: src/legion_goes/tasks/task03_proc_single/actions/action02_check_plan_proc_single.py
# Version: 1.7.7 (Audit for Detailed Ref Schema)
# =============================================================================

import json
from pathlib import Path
from datetime import datetime

def run_action02_check_plan_proc_single(path_plan_json):
    """
    Audits the processing plan using the ref_input/ref_output structure.
    Checks for the existence of ALL files in the output schema.
    """
    ctx = "[Action 02 Proc - Detailed Audit]"
    path_p = Path(path_plan_json)

    if not path_p.exists():
        print(f"❌ {ctx} Error: Plan file not found at {path_p}")
        return False

    with open(path_p, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    inventory = plan.get('proc_inventory', {})
    stats = {
        "ready_to_process": 0,
        "already_exists_full": 0, # Todos los archivos del schema existen
        "already_exists_partial": 0, # Algunos archivos existen
        "missing_input": 0
    }

    # --- 1. PHYSICAL AUDIT ON DISK ---
    for fid, item in inventory.items():
        # Acceso usando las nuevas llaves 'ref_input' y 'ref_output'
        in_path = Path(item['ref_input']['path_absolute'])
        outputs = item['ref_output']['outputs']

        # A. Verificar Entrada (RAW)
        exists_in = in_path.exists()
        item['status']['exists_input'] = exists_in

        # B. Verificar Salidas (SCHEMA)
        # Auditamos cada archivo definido en el dict_output_schema
        existing_outputs_count = 0
        total_outputs_expected = len(outputs)

        for out_key, out_info in outputs.items():
            out_file_path = Path(out_info['path_absolute'])
            exists_out = out_file_path.exists()
            out_info['exists'] = exists_out # Guardamos estado individual
            if exists_out:
                existing_outputs_count += 1

        # C. Determinar estado del item
        if not exists_in:
            stats["missing_input"] += 1
            item['status']['is_processed'] = False
        elif existing_outputs_count == total_outputs_expected:
            stats["already_exists_full"] += 1
            item['status']['is_processed'] = True
        elif existing_outputs_count > 0:
            stats["already_exists_partial"] += 1
            item['status']['is_processed'] = False # Se marca falso para forzar re-proceso
        else:
            stats["ready_to_process"] += 1
            item['status']['is_processed'] = False

    # --- 2. UPDATE METADATA ---
    if 'summary' not in plan: plan['summary'] = {}
    plan['summary']['last_audit'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plan['summary']['stats'] = stats

    # --- 3. SAVE UPDATED PLAN ---
    with open(path_p, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=4)

    # --- 4. VISUAL REPORT ---
    print(f"\n{'='*50}")
    print(f"📊 {ctx} Audit Report")
    print(f"{'='*50}")
    print(f"✅ Ready (to process):  {stats['ready_to_process']}")
    print(f"✨ Complete (full):     {stats['already_exists_full']}")
    print(f"🌗 Partial (incomplete): {stats['already_exists_partial']}")
    print(f"⚠️  Missing Input:      {stats['missing_input']}")
    print(f"{'='*50}\n")

    return True
