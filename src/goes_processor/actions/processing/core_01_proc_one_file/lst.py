# Version: v.0.5.0 (LST Orchestrator - Path Refactoring with Hourly Folders)
import sys
import json
import warnings
import numpy as np
import time
import os
import matplotlib
# Force non-interactive backend to prevent Tcl/Tkinter thread errors in CLI
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from satpy import Scene, config as satpy_config
from pyresample.geometry import AreaDefinition

warnings.filterwarnings("ignore")

class SmartIndentedOutput:
    """
    Captures output and applies double indentation for library logs.
    """
    def __init__(self, original_stream, base_indent):
        self.original_stream = original_stream
        self.base_indent = base_indent
        self.extra_indent = "    "
        self.newline = True

    def write(self, text):
        for line in text.splitlines(keepends=True):
            if self.newline and line.strip():
                if not any(icon in line for icon in ["⏰", "📁", "📂", "🧠", "📦", "📸", "🗺️", "🔄", "💾", "✅", "🏁", "⏱️", "❌"]):
                    self.original_stream.write(self.base_indent + self.extra_indent + line)
                else:
                    self.original_stream.write(self.base_indent + line)
            else:
                self.original_stream.write(line)
            self.newline = line.endswith('\n')

    def flush(self):
        self.original_stream.flush()

# --- ORCHESTRATOR ---

def process_lst_single_file(input_file, input_base: Path, output_base: Path, overwrite=False, indent=""):
    """
    Sequential Orchestrator for LST Module.
    Structure: output / satellite / product / year / day / hour / time_lapse / filename
    """
    file_path = Path(input_file).resolve()
    base_name = file_path.stem
    
    # 1. CENTRALIZED PATH LOGIC (GOES-R Filename Parsing)
    parts = base_name.split('_')
    # noaa-goes19, noaa-goes18, etc.
    sat_name = f"noaa-goes{parts[2].replace('G', '')}"
    # ABI-L2-LSTF (rsplit used to avoid breaking names with internal 'M')
    product_raw = parts[1]
    product_clean = product_raw.rsplit('-M', 1)[0] if '-M' in product_raw else product_raw
    
    # Time parsing from part 3: sYYYYJJJHHMMSS (e.g., s20260031430...)
    time_str = parts[3]
    year = time_str[1:5]
    day  = time_str[5:8]
    hour = time_str[8:10] # Extracting HH

    # Common root path with the new Hourly hierarchy
    # Path: output/noaa-goes19/ABI-L2-LSTF/2026/003/14/time_lapse_01hour/OR_ABI...
    product_out_root = output_base / sat_name / product_clean / year / day / hour / "time_lapse_01hour" / base_name
    
    success_report = {"stage_01": False}
    
    # Execute Stage 01
    success_report["stage_01"] = fn01_lst_generate_products(
        file_path, product_out_root, overwrite, indent
    )
    
    return success_report

# --- STAGE FUNCTIONS ---


