# =============================================================================
# FILE PATH:
# src/goes_processor/goes_info/goes_sat.py
#
# Purpose: Standardized and protected information for GOES-R satellites.
# Contains satellite IDs, AWS buckets, names, positions, status, and transition dates.
# This is the single source of truth for determining the active satellite for a given date.
# Data is immutable after loading (MappingProxyType) to prevent accidental changes.
#
# Features:
#   - Required fields validation on module import
#   - Read-only public interface (SAVED_INFO_SAT_GOES)
#   - Safe getter functions for satellite ID, info, and bucket
#   - Date-based logic to determine active satellite (east/west transitions)
#
# Official sources:
# - NOAA GOES-R Series Data Book: https://www.goes-r.gov/downloads/resources/documents/GOES-R_Series_Data_Book.pdf
# - GOES-R Series Transition Timeline: https://www.goes-r.gov/about/goes-r-series-satellites.html
# - AWS Public GOES Buckets: https://registry.opendata.aws/noaa-goes/
# =============================================================================

from pathlib import Path
from types import MappingProxyType
from datetime import datetime
import re


# ===================================================================
# REQUIRED FIELDS FOR EACH SATELLITE ENTRY
# ===================================================================
REQUIRED_FIELDS = frozenset({
    "bucket",
    "name01", "name02", "name03", "name04", "name05", "name06",
    "default_position",
    "status",
    "first_date",
    "last_date"
})


# ===================================================================
# PRIVATE SOURCE OF TRUTH (mutable only in this file)
# ===================================================================
_PRIVATE_SAT_INFO = {
    "meta": {
        "version": "0.1.4",
        "series": "GOES-R",
        "description": "Master Config - NOAA GOES Identity and Transitions",
        "transitions": {
            "east_16_to_19": datetime(2025, 4, 1),
            "west_17_to_18": datetime(2023, 1, 4)
        }
    },
    "16": {
        "bucket": "noaa-goes16",
        "name01": "16", 
        "name02": "g16", 
        "name03": "goes16",
        "name04": "goes-east", 
        "name05": "goes16-east",
        "name06": "GOES16",
        "default_position": "east",
        "status": "standby",
        "first_date": "2016-12-18",
        "last_date": None
    },
    "17": {
        "bucket": "noaa-goes17",
        "name01": "17", "name02": "g17", "name03": "goes17",
        "name04": "goes-west", "name05": "goes17-west", "name06": "GOES17",
        "default_position": "west",
        "status": "standby",
        "first_date": "2018-02-12",
        "last_date": None
    },
    "18": {
        "bucket": "noaa-goes18",
        "name01": "18", "name02": "g18", "name03": "goes18",
        "name04": "goes-west", "name05": "goes18-west", "name06": "GOES18",
        "default_position": "west",
        "status": "active",
        "first_date": "2022-03-01",
        "last_date": None
    },
    "19": {
        "bucket": "noaa-goes19",
        "name01": "19", "name02": "g19", "name03": "goes19",
        "name04": "goes-east", "name05": "goes19-east", "name06": "GOES19",
        "default_position": "east",
        "status": "active",
        "first_date": "2024-06-25",
        "last_date": None
    }
}


# ===================================================================
# AUTOMATIC VALIDATION ON MODULE IMPORT
# ===================================================================
def _validate_satellite_data():
    """
    Internal validation: ensure all satellites have exactly the required fields
    and valid date formats.
    """
    date_regex = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    for sat_id, data in _PRIVATE_SAT_INFO.items():
        if sat_id == "meta":
            continue

        missing = REQUIRED_FIELDS - set(data.keys())
        extra = set(data.keys()) - REQUIRED_FIELDS

        if missing:
            raise ValueError(
                f"CRITICAL CONFIGURATION ERROR\n"
                f"File: {Path(__file__).resolve()}\n"
                f"Satellite ID: {sat_id}\n"
                f"Missing required fields: {missing}\n"
                f"Required fields: {REQUIRED_FIELDS}\n"
                f"Action: Add missing fields to maintain consistency."
            )

        if extra:
            raise ValueError(
                f"CRITICAL CONFIGURATION ERROR\n"
                f"File: {Path(__file__).resolve()}\n"
                f"Satellite ID: {sat_id}\n"
                f"Extra fields found (not allowed): {extra}\n"
                f"Only these fields are permitted: {REQUIRED_FIELDS}\n"
                f"Action: Remove extra fields."
            )

        # Validate date format for first_date and last_date
        for key in ["first_date", "last_date"]:
            value = data.get(key)
            if value and not date_regex.match(value):
                raise ValueError(
                    f"DATE FORMAT ERROR\n"
                    f"File: {Path(__file__).resolve()}\n"
                    f"Satellite ID: {sat_id}\n"
                    f"Field: {key}\n"
                    f"Invalid value: '{value}'\n"
                    f"Expected format: YYYY-MM-DD"
                )


# Run validation immediately when module is imported
_validate_satellite_data()


# ===================================================================
# PROTECTED, IMMUTABLE PUBLIC INTERFACE
# ===================================================================
SAVED_INFO_SAT_GOES = MappingProxyType({
    k: MappingProxyType(v) if isinstance(v, dict) else v
    for k, v in _PRIVATE_SAT_INFO.items()
})


# ===================================================================
# PUBLIC ACCESS METHODS (safe getters)
# ===================================================================
def get_goes_id_by_date(year: str, day: str, sat_position: str = "east") -> str | None:
    """
    Main entry point: Get the operational satellite ID for a given date and position.
    """
    # Validate inputs
    allowed_positions = ["east", "west"]
    pos = sat_position.lower()
    if pos not in allowed_positions:
        raise ValueError(f"Invalid sat_position '{sat_position}'. Allowed: {allowed_positions}")

    if not re.match(r'^\d{4}$', year):
        raise ValueError(f"Invalid year '{year}': must be YYYY (4 digits).")

    if not re.match(r'^\d{3}$', day):
        raise ValueError(f"Invalid day '{day}': must be DDD (3 digits, 001–366).")

    day_int = int(day)
    if not (1 <= day_int <= 366):
        raise ValueError(f"Day '{day}' out of range: must be 001–366.")

    # Convert to date object
    date_obj = datetime.strptime(f"{year}-{day}", "%Y-%j")

    transitions = SAVED_INFO_SAT_GOES["meta"]["transitions"]
    if pos == "east":
        return "16" if date_obj < transitions["east_16_to_19"] else "19"
    elif pos == "west":
        return "17" if date_obj < transitions["west_17_to_18"] else "18"
    return None


def get_satellite_info(sat_id: str) -> MappingProxyType | None:
    """Return metadata for a specific satellite ID (read-only)."""
    return SAVED_INFO_SAT_GOES.get(str(sat_id))


def get_goes_bucket(sat_id: str) -> str | None:
    """Return the AWS S3 bucket name for a satellite ID."""
    sat_data = get_satellite_info(sat_id)
    return sat_data["bucket"] if sat_data else None


# ===================================================================
# Example usage (runs only if file is executed directly)
# ===================================================================
if __name__ == "__main__":
    print("Available GOES satellites:")
    for sat_id, info in SAVED_INFO_SAT_GOES.items():
        if sat_id == "meta":
            continue
        print(f" - {sat_id}: {info['name03']} ({info['default_position']}) - Status: {info['status']}")

    print("\nExample: Get active GOES-East satellite for 2026 day 003:")
    sat_id = get_goes_id_by_date("2026", "003", sat_position="east")
    print(f" → Satellite ID: {sat_id}")
    print(f" → Bucket: {get_goes_bucket(sat_id)}")

    print("\nDetailed info for GOES-19:")
    info = get_satellite_info("19")
    if info:
        for key, value in info.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
