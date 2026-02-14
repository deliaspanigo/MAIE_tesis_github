El proyecto se maneja principalmente a través del comando CLI goes19.
### 1. Descargar datos
Descargar una banda específica (ej: banda 02 visible):
goes19 download --year 2026 --day 043 --hour 12 --product ABI-L1b-RadF --band 02
Descargar todos los archivos de una hora:
goes19 download --year 2026 --day 043 --hour 12 --product ABI-L2-LSTF --all
Descargar un archivo específico por nombre:
goes19 download --year 2026 --day 043 --hour 12 --product ABI-L1b-RadF 
--file-name OR_ABI-L1b-RadF-M6C02_G19_s20260431200212_e20260431209520_c20260431209573.nc
Forzar sobreescritura si ya existe:
goes19 download --year 2026 --day 043 --hour 12 --product ABI-L2-LSTF --overwrite
Descargar rango de horas (ej: de 11:00 a 13:00):
goes19 download --year 2026 --day 043 --hour 12 --product ABI-L2-LSTF 
--start-time 2026-02-12_11:00 --end-time 2026-02-12_13:00
### 2. Ejecutar el scheduler automático
Para que el sistema descargue y procese automáticamente según los horarios definidos:
python -m goes19_processor.scheduler
Esto inicia el planificador en segundo plano.
Los intervalos actuales incluyen:
- True Color / bandas visibles: cada 10 minutos
- LST (temperatura de superficie): cada 1 hora
- Otros productos: cada 5–60 minutos (configurable en el futuro)
Para producción, configurarlo como servicio systemd (ver docs/deployment.md).
### 3. Ver ayuda completa
goes19 --help
goes19 download --help
Los archivos se guardan en data/raw/noaa-goes19/... con estructura organizada por producto/año/día/hora.# goes19-sat-processor
# goes19-sat-processor
# goes19-sat-processor
# MAIE_tesis_github
