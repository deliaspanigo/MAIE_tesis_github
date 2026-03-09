# =============================================================================
# FILE PATH: legion_goes/tasks/task02_download/actions/fn_act02/update_dict_plan_download.py
# Version: 1.7.0 (Dual Path Logic: Plan vs Raw Data)
# =============================================================================
import os
import json  

from legion_goes.tasks.task02_download.actions.fn_act02.step02_update_dict_parts.update_dict03_inventory import update_dict03_inventory
from legion_goes.tasks.task02_download.actions.fn_act02.step02_update_dict_parts.update_dict04_summary   import update_dict04_summary

########################################################################################



def update_dict_plan_download(
    dict_plan: dict
):
    """
    Main entry point to check local integrity.
    Locates the JSON in the CONTROL folder (data_plan).
    """
    
    dict_plan = update_dict03_inventory(dict_plan = dict_plan)
    dict_plan = update_dict04_summary(dict_plan = dict_plan)
    
    return dict_plan
