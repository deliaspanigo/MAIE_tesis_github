# task01_init.py
from legion_goes.tasks.task01_init.actions.action01_welcome import run_action as action01_welcome
from legion_goes.tasks.task01_init.actions.action02_create_folder_structure import run_action as action02_create_folder_structure

def run_task(verbose: bool = True):
    """
    Ejecuta la inicialización completa del proyecto:
    - Muestra bienvenida
    - Crea/verifica carpetas por defecto
    """
    action01_welcome()
    action02_create_folder_structure(verbose=verbose)  # Pasa verbose a la acción de carpetas
    if verbose:
        print("\nInicialización completa. ¡Proyecto listo para usar!")

# ===================================================================
# MAIN EXECUTION (Entry point)
# ===================================================================
if __name__ == "__main__":
    print("\n" + "=== LEGION GOES - TASK 01: PROJECT INITIALIZATION ===".center(80, "="))
    print("Ejecutando inicialización completa del proyecto...\n")
    
    try:
        # Ejecuta la función de inicialización
        run_task(verbose=True)  # ← Pasa verbose=True aquí
        
        print("\n" + "=== INICIALIZACIÓN FINALIZADA EXITOSAMENTE ===".center(80, "="))
        print("Puedes continuar trabajando en notebooks o scripts.")
        print("Carpeta actual: " + os.getcwd())
    
    except Exception as e:
        print("\n" + "=== ERROR DURANTE LA INICIALIZACIÓN ===".center(80, "="))
        print(f"Detalles: {e}")
        print("Revisa los logs o la consola para más información.")
        raise  # Para que se vea el traceback completo si hay error
    
    print("=" * 80 + "\n")
