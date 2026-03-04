 # Metadata de la Tesis
 version = "0.7.0"
 last_update = "2026-03-04"

 El proyecto se maneja principalmente a través del comando CLI goes-processor.
 Esta versión incluye detección automática de satélites (GOES-16/17/18/19) según fecha y posición.

 ## 🛠️ Instalación y Setup
 bash  source venv/bin/activate  
 
 bash pip install -e . --no-cache-dir  

 ## 🛰️ 1. Ciclo de Descarga por Producto
 El sistema utiliza un flujo de tres pasos para garantizar la integridad en la Legion.

 ### Caso: Land Surface Temperature (LSTF)
 bash  
 
 # A. Generar el Plan (Detecta automáticamente GOES-19 para 2026)  
 goes-processor download gen-plan-download    --sat-position east --product ABI-L2-LSTF --year 2026 --day 003 --overwrite False    
 
 # B. Verificar Disco (Sincroniza lo que ya existe en la Legion)  
 goes-processor download check-plan-download  --sat-position east --product ABI-L2-LSTF --year 2026 --day 003    
 
 # C. Ejecutar Descarga (Solo descarga faltantes con hilos y reporte de color)  
 goes-processor download run-plan-download    --sat-position east --product ABI-L2-LSTF --year 2026 --day 003 --overwrite False --threads 4   


 ### Caso: Producto Multicanal (MCMIPF)
 bash  
 goes-processor download gen-plan-download    --sat-position east --product ABI-L2-MCMIPF --year 2026 --day 003 --overwrite False  
 goes-processor download check-plan-download  --sat-position east --product ABI-L2-MCMIPF --year 2026 --day 003  
 goes-processor download run-plan-download    --sat-position east --product ABI-L2-MCMIPF --year 2026 --day 003 --overwrite False --threads 4   

 ## 📦 2. Ejecución Masiva (ALL Products)
 Si deseas procesar todos los productos configurados para un día específico:
 bash  
 goes-processor download gen-plan-download    --sat-position east --product ALL --year 2026 --day 003 --overwrite False  
 goes-processor download check-plan-download  --sat-position east --product ALL --year 2026 --day 003  
 goes-processor download run-plan-download    --sat-position east --product ALL --year 2026 --day 003 --overwrite False --threads 8  

 ## 🧠 3. Notas de Implementación
 - Inteligencia de Satélites: El sistema decide el bucket (noaa-goes16 vs noaa-goes19) consultando el SoT (Source of Truth) interno.
 - Logs: La Action 03 (run-plan) muestra un reporte de estado tipo 📊 [STATUS] 4320/4320 y usa colores para identificar descargas exitosas.
 - Estructura de Datos: Los archivos se guardan en data/raw/{bucket}/{product}/{year}/{day}/{hour}/.

 ## 4. Ayuda Completa
 bash  goes-processor --help  goes-processor download --help 