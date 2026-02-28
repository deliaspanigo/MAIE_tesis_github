"""
Path: src/goes_processor/actions/a03_download/a03_download_cli.py
Description: Action-level orchestrator for data acquisition.
"""
import click
import sys

try:
    from goes_processor.actions.a03_download.core01_download_from_s3.cli01_download_s3_engine import download_s3_command
except ImportError as e:
    print(f"❌ Error importing download-s3: {e}")
    download_s3_command = None

@click.group(name="download")
def download_group():
    """Actions for satellite data acquisition. Action ID: a03"""
    pass

if download_s3_command:
    download_group.add_command(download_s3_command)
