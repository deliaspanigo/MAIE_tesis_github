import click
from legion_goes.tasks.task01_init import run_task01_init

@click.group()
def cli():
    """LEGION Processor: GOES Satellite Data Pipeline for MAIE Thesis 2026."""
    pass

@cli.command()
def run():
    """Execute the full processing pipeline."""
    # Step 1: Initialize System
    run_task01_init()
    
    # Future steps will be added here:
    # run_task02_download()
    # run_task03_processing()
    print("Pipeline execution finished.")

if __name__ == "__main__":
    cli()
