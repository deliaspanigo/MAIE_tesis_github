# src/goes19_processor/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import subprocess
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_download_and_process(product: str, schedule_type: str, interval_minutes: int = None, cron_expr: str = None):
    """Run the CLI for download and process"""
    def job():
        now = datetime.datetime.now()
        year = now.strftime("%Y")
        day = now.strftime("%j")
        hour = now.strftime("%H")
        
        cmd_download = [
            "goes19", "download",
            "--product", product,
            "--year", year,
            "--day", day,
            "--hour", hour,
            # Add --all, --band, etc. if needed for this product
        ]
        logging.info(f"Running download for {product}: {cmd_download}")
        subprocess.call(cmd_download)
        
        # Assume the downloaded file path is known or latest in data/raw
        # For simplicity, process the latest downloaded (adjust as needed)
        cmd_process = [
            "goes19", "process",
            "--file", "path/to/latest/file.nc",  # Replace with logic to find latest file
            "--product", product.lower().replace("-", "_"),
        ]
        logging.info(f"Running process for {product}: {cmd_process}")
        subprocess.call(cmd_process)
    
    return job

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    
    # Example schedules
    # LST every 1 hour
    scheduler.add_job(
        run_download_and_process("ABI-L2-LSTF"),
        IntervalTrigger(minutes=60)  # every 1 hour
    )
    
    # True Color every 10 minutes
    scheduler.add_job(
        run_download_and_process("ABI-L1b-RadF"),  # Adjust for true_color composites
        IntervalTrigger(minutes=10)
    )
    
    # Fire detection every 5 minutes (example)
    scheduler.add_job(
        run_download_and_process("ABI-L2-FDC"),
        IntervalTrigger(minutes=5)
    )
    
    # Lightning every 1 minute (example)
    scheduler.add_job(
        run_download_and_process("GLM-L2-LCFA"),
        IntervalTrigger(minutes=1)
    )
    
    # Or use cron for specific times, e.g., LST at every hour on the hour
    # scheduler.add_job(
    #     run_download_and_process("ABI-L2-LSTF"),
    #     CronTrigger(hour='*', minute='0')
    # )
    
    scheduler.start()
    logging.info("Scheduler started. Press Ctrl+C to exit.")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logging.info("Scheduler stopped.")
