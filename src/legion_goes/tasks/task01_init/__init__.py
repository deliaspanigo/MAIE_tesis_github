# src/legion_goes/tasks/task01_init/__init__.py

from .actions.action01_welcome import show_welcome_banner
from .actions.action02_folders import create_folder_structure

def run_task01_init():
    """Orquestador de la Fase 01: Inicialización"""
    
    # 1. Mostrar Banner y Diagnóstico
    show_welcome_banner()
    
    # 2. Crear Carpetas (Lógica movida a action02)
    create_folder_structure()
