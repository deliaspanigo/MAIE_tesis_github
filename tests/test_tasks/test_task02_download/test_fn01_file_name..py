# tests/test_tasks/test_task02_download/test_fn01_file_name.py
import pytest
from pathlib import Path

# Importamos desde tu paquete legion_goes
from legion_goes.tasks.task02_download.actions.fn01_file_name_plan_download import (
    generate_plan_download_file_name,
    generate_plan_download_file_path,
    validate_params
)

def test_naming_convention():
    """Verifica que el nombre siga el estándar plan_01-download_YYYY_DDD_SAT_POS_PROD.json"""
    name = generate_plan_download_file_name(
        year="2026", 
        day="45", 
        sat_id="G16", 
        product_id="ABI-L2-CMIPF"
    )
    assert name.startswith("plan_01-download_")
    assert "2026_045_GOES16" in name
    assert name.endswith(".json")

def test_path_creation_and_structure(tmp_path):
    """Verifica que cree las carpetas Año/Día correctamente"""
    # tmp_path es una carpeta temporal que pytest limpia solo
    base = tmp_path / "test_data"
    
    result_path = generate_plan_download_file_path(
        year="2026",
        day="45",
        sat_id="G16",
        product_id="ABI-L2-CMIPF",
        output_folder_base=base
    )
    
    # Comprobar estructura física
    assert result_path.exists()
    assert "/2026/045/" in result_path.as_posix()

def test_guardian_catches_invalid_day():
    """Verifica que la Aduana (validate_params) rebote días inválidos"""
    with pytest.raises(ValueError, match="Invalid Julian day"):
        validate_params(day=500)
