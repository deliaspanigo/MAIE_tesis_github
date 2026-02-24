# src/goes_processor/actions/download/download.py

import fsspec
from pathlib import Path
import os
import shutil
from typing import List
import socket
import time
from datetime import datetime


# Inicializamos el diccionario maestro
_info_ABI_L2_LSTF_ = {
    "metadata": {
        "version": "0.0.1",
        "description": "Details for ABI-L2-LSTF"
    },
    "product_name": "ABI-L2-LSTF",
      "standard_info" = {
            "time_step_standard": "01hour",
            "list_hour": [f"{h:02d}" for h in range(24)],
            "list_minute": ["00"],
            "list_second": ["00"],
            "pixel_goes_standard": "2 km",
            "shape_full_disk": "1086px_1086py",
            "time_step_mod": None,
        }
}

_info_ABI_L2_MCMIPF_ = {
    "metadata": {
        "version": "0.0.1",
        "description": "Details for ABI-L2-MCMIPF"
    },
    "product_name": "ABI-L2-MCMIPF",
    "standard_info" = {
        "time_step_standard": "10minutes",
        "list_hour": [f"{h:02d}" for h in range(24)],
        "list_minutes": [f"{m:02d}" for m in range(0, 60, 10)],
        "list_second": ["00"],
        "pixel_goes_standard": "2 km",
        "shape_full_disk": "1086px_1086py",
        "shape_wgs84": "3600px_1800py"
        },
    "mod_info"= {
        "time_step_standard": "01hour",
        "list_hour": [f"{h:02d}" for h in range(24)],
        "list_minutes": ["00"],
        "list_second": ["00"],
        "pixel_goes_standard": "2 km",
        "shape_full_disk": "1086px_1086py",
        "shape_wgs84": "3600px_1800py"
        },
}


_info_ABI_L2_FDCF_ = {
    "metadata": {
        "version": "0.0.1",
        "description": "Details for ABI-L2-FDCF"
    },
    "product_name": "ABI-L2-FDCF",
    "standard_info" = {
        "time_step_standard": "10minutes",
        "list_hour": [f"{h:02d}" for h in range(24)],
        "list_minutes": [f"{m:02d}" for m in range(0, 60, 10)],
        "list_second": ["00"],
        "pixel_goes_standard": "2 km",
        "shape_full_disk": "5424px_5424py",
        "shape_wgs84": "3600px_1800py"
        },
    "mod_info"= {
        "time_step_standard": "01hour",
        "list_hour": [f"{h:02d}" for h in range(24)],
        "list_minutes": ["00"],
        "list_second": ["00"],
        "pixel_goes_standard": "2 km",
        "shape_full_disk": "1086px_1086py",
        "shape_wgs84": "3600px_1800py"
        },
}


_info_GLM_L2_LCFA_ = {
    "metadata": {
        "version": "0.0.1",
        "description": "Details for GLM_L2_LCFA"
    },
    "product_name": "GLM_L2_LCFA",
    "standard_info" = {
        "time_step_standard": "10minutes",
        "list_hour": [f"{h:02d}" for h in range(24)],
        "list_minutes": [f"{m:02d}" for m in range(0, 60, 10)],
        "list_second": ["00"],
        "pixel_goes_standard": "2 km",
        "shape_full_disk": "5424px_5424py",
        "shape_wgs84": "3600px_1800py"
        },
    "mod_info"= {
        "time_step_standard": "01hour",
        "list_hour": [f"{h:02d}" for h in range(24)],
        "list_minutes": ["00"],
        "list_second": ["00"],
        "pixel_goes_standard": "2 km",
        "shape_full_disk": "1086px_1086py",
        "shape_wgs84": "3600px_1800py"
        },
}



