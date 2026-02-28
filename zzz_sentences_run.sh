#!/bin/bash

# ==============================================================================
# MAIE Tesis - Master Orchestrator
# Executes all processing scripts for Core 01 and Core 02
# ==============================================================================

# Colores para el reporte
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Full GOES Processing Pipeline...${NC}\n"

# 1. Asegurar permisos de ejecución en todas las carpetas de scripts
chmod +x z_scripts_02_proc_core_01_one_fille/*.sh
chmod +x z_scripts_02_proc_core_02_one_fille/*.sh

# --- SECCIÓN 01: CORE 01 (Individual File Processing) ---
echo -e "${GREEN}📦 Stage 1: Running Core 01 (Individual Processing)...${NC}"

./z_scripts_02_proc_core_01_one_fille/proc_FDC_one_file.sh
./z_scripts_02_proc_core_01_one_fille/proc_LCFA_one_file.sh
./z_scripts_02_proc_core_01_one_fille/proc_LST_one_file.sh
./z_scripts_02_proc_core_01_one_fille/proc_MCMIP_one_file.sh

echo -e "${GREEN}✅ Core 01 Completed.${NC}\n"

# --- SECCIÓN 02: CORE 02 (Accumulations) ---
echo -e "${GREEN}📊 Stage 2: Running Core 02 (Accumulations)...${NC}"

# FDC Accumulations
./z_scripts_02_proc_core_02_one_fille/proc_FDC_accumulate_10minutes.sh
./z_scripts_02_proc_core_02_one_fille/proc_FDC_accumulate_01hour.sh
./z_scripts_02_proc_core_02_one_fille/proc_FDC_accumulate_01day.sh

# GLM (LCFA) Accumulations
./z_scripts_02_proc_core_02_one_fille/proc_LCFA_accumulate_10minutes.sh
./z_scripts_02_proc_core_02_one_fille/proc_LCFA_accumulate_01hour.sh
./z_scripts_02_proc_core_02_one_fille/proc_LCFA_accumulate_01day.sh

echo -e "${GREEN}✅ Core 02 Completed.${NC}\n"

echo -e "${BLUE}🏁 All processes finished successfully!${NC}"
