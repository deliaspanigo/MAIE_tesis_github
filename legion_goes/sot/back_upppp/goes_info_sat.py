# =============================================================================
# FILE PATH: src/legion_goes/sot/goes_info_sat.py
# Version: 1.1.0 (Atomic Object-Driven SoT)
# =============================================================================
import sys
from types import MappingProxyType
from datetime import datetime

# ===================================================================
# CONFIGURATION & HISTORICAL TRANSITIONS
# ===================================================================
AVAILABLE_GOES_SAT_POSITIONS = ("east", "west")

# Exact operational transition dates (Source: NOAA)
TRANSITIONS = {
    "east_16_to_19": datetime(2025, 4, 7),   # GOES-19 declared operational GOES-East on April 7, 2025
    "west_17_to_18": datetime(2023, 1, 4),   # GOES-18 assumed GOES-West
    "east_13_to_16": datetime(2017, 12, 18)  # Historical GOES-13 to GOES-16
}

_PRIVATE_SAT_INFO = {
    "16": {"id": "16", "bucket": "noaa-goes16", "name01": "16", "name02": "G16", "name03": "GOES16", "position": "east"},
    "17": {"id": "17", "bucket": "noaa-goes17", "name01": "17", "name02": "G17", "name03": "GOES17", "position": "west"},
    "18": {"id": "18", "bucket": "noaa-goes18", "name01": "18", "name02": "G18", "name03": "GOES18", "position": "west"},
    "19": {"id": "19", "bucket": "noaa-goes19", "name01": "19", "name02": "G19", "name03": "GOES19", "position": "east"}
}

AVAILABLE_GOES_ID = tuple(_PRIVATE_SAT_INFO.keys())

# ===================================================================
# IMMUTABILITY ENGINE
# ===================================================================
def _make_deep_immutable(obj):
    if isinstance(obj, dict):
        return MappingProxyType({k: _make_deep_immutable(v) for k, v in obj.items()})
    elif isinstance(obj, (list, tuple)):
        return tuple(_make_deep_immutable(i) for i in obj)
    return obj

SAVED_INFO_SAT_GOES = _make_deep_immutable(_PRIVATE_SAT_INFO)

# ===================================================================
# CONTROL FUNCTIONS (The Guards)
# ===================================================================
def control_position(position):
    """
    GUARD: Validates 'position' against the Source of Truth (SoT).
    Extremely strict validation for the Legion GOES system.
    
    Accepts **only** exactly 'east' or 'west' (lowercase, no spaces, exactly 4 characters).
    Any deviation raises an immediate and explicit error.
    """
    ctx = sys._getframe().f_code.co_name

    if position is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is None. A valid position is required.")
    
    if not isinstance(position, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is '{position}' ({type(position).__name__}). Expected type: str.")
    
    if " " in position:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is '{position}' and contains spaces. Provide a clean string (exactly 'east' or 'west').")
    
    if position != position.lower():
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is '{position}' and contains uppercase letters. Only lowercase is allowed (exactly 'east' or 'west').")
    
    if len(position) != 4:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' is '{position}' and does not have exactly 4 characters (must be exactly 'east' or 'west').")
    
    if position not in AVAILABLE_GOES_SAT_POSITIONS:
        valid_options = ", ".join(AVAILABLE_GOES_SAT_POSITIONS)
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'position' '{position}' is not found in the Source of Truth.\n💡 Available positions: {valid_options}")

def control_sat_id(sat_id):
    """
    GUARD: Validates 'sat_id' against the Source of Truth (SoT).
    Extremely strict validation for the Legion GOES system.
    
    Accepts **only** exactly '16', '17', '18' or '19' (exactly 2 digits, no spaces, only numeric).
    Any deviation raises an immediate and explicit error.
    """
    ctx = sys._getframe().f_code.co_name

    if sat_id is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is None. A valid satellite ID is required.")
    
    if not isinstance(sat_id, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is '{sat_id}' ({type(sat_id).__name__}). Expected type: str.")
    
    if " " in sat_id:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is '{sat_id}' and contains spaces. Provide a clean string (exactly '16', '17', '18' or '19').")
    
    if len(sat_id) != 2:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is '{sat_id}' and does not have exactly 2 characters (must be exactly '16', '17', '18' or '19').")
    
    if not sat_id.isdigit():
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' is '{sat_id}' and contains non-digit characters. Expected exactly 2 digits (e.g., '19').")
    
    if sat_id not in AVAILABLE_GOES_ID:
        valid_options = ", ".join(AVAILABLE_GOES_ID)
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'sat_id' '{sat_id}' is not found in the Source of Truth.\n💡 Available satellite IDs: {valid_options}")

def control_year(year):
    """
    GUARD: Validates 'year' against strict format requirements for the Legion GOES system.
    Extremely strict validation.
    
    Accepts **only** exactly 4-digit strings like '2026' (no spaces, only digits).
    Any deviation raises an immediate and explicit error.
    """
    ctx = sys._getframe().f_code.co_name

    if year is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' is None. A valid year is required.")
    
    if not isinstance(year, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' is '{year}' ({type(year).__name__}). Expected type: str.")
    
    if " " in year:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' '{year}' contains spaces. Provide a clean 4-digit string (exactly 'YYYY').")
    
    if len(year) != 4:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' '{year}' does not have exactly 4 characters. Expected format: 'YYYY' (e.g., '2026').")
    
    if not year.isdigit():
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'year' '{year}' contains non-digit characters. Expected exactly 4 digits (e.g., '2026').")

def control_day(day):
    """
    GUARD: Validates Julian day (day of year) against strict format for the Legion GOES system.
    Extremely strict validation.
    
    Accepts **only** exactly 3-digit strings like '001', '065', '366' (padded with zeros, only digits, no spaces).
    Rejects any deviation (integers, floats, wrong length, non-digits, out-of-range).
    """
    ctx = sys._getframe().f_code.co_name

    if day is None:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' is None. A valid Julian day is required.")
    
    if not isinstance(day, str):
        raise TypeError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' is '{day}' ({type(day).__name__}). Expected type: str only.")
    
    if " " in day:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' '{day}' contains spaces. Provide a clean 3-digit string (e.g., '065').")
    
    if len(day) != 3:
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' '{day}' does not have exactly 3 characters. Expected format: 'DDD' (e.g., '001' or '366').")
    
    if not day.isdigit():
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Argument 'day' '{day}' contains non-digit characters. Expected exactly 3 digits.")
    
    int_day = int(day)
    if not (1 <= int_day <= 366):
        raise ValueError(f"\n❌ [🛡️🛡️🛡️ GUARD ERROR - {ctx}()]: Day '{day}' ({int_day}) is out of valid Julian day range. Must be between 001 and 366.")

# ===================================================================
# PUBLIC INTERFACE (Object-Driven)
# ===================================================================
def get_SOT_goes_info_sat(sat_id: str = None) -> MappingProxyType:
    """
    Retrieves satellite metadata from the Source of Truth (SoT).
    Extremely strict access to the immutable master object.
    
    - If sat_id is None: returns the full immutable dictionary of all satellites.
    - If sat_id is provided: returns the metadata for that exact satellite ID.
    
    Includes strict integrity checks:
    - Master object must exist, not be None, not be empty.
    - Master object MUST be exactly a MappingProxyType (immutable proxy).
    
    Validates sat_id using control_sat_id() before access.
    Raises explicit RuntimeError on ANY integrity violation.
    """
    ctx = sys._getframe().f_code.co_name

    if not hasattr(sys.modules[__name__], 'SAVED_INFO_SAT_GOES'):
        raise RuntimeError(f"\n❌ [🛡️🛡️🛡️ SYSTEM INTEGRITY ERROR - {ctx}()]: The master object 'SAVED_INFO_SAT_GOES' does not exist in module namespace. Source of Truth initialization failed.")
    
    master_obj = SAVED_INFO_SAT_GOES
    
    if master_obj is None:
        raise RuntimeError(f"\n❌ [🛡️🛡️🛡️ SYSTEM INTEGRITY ERROR - {ctx}()]: The master object 'SAVED_INFO_SAT_GOES' is None. Source of Truth is not initialized.")
    
    from types import MappingProxyType
    if not isinstance(master_obj, MappingProxyType):
        raise RuntimeError(f"\n❌ [🛡️🛡️🛡️ SYSTEM INTEGRITY ERROR - {ctx}()]: The master object 'SAVED_INFO_SAT_GOES' is of type {type(master_obj).__name__}, but MUST be exactly MappingProxyType (immutable proxy). Source of Truth integrity violated - possible code tampering, import error, or concurrent modification.")
    
    if not master_obj:
        raise RuntimeError(f"\n❌ [🛡️🛡️🛡️ SYSTEM INTEGRITY ERROR - {ctx}()]: The master object 'SAVED_INFO_SAT_GOES' is empty. Source of Truth has no satellite data.")
    
    if sat_id is None:
        return master_obj
    
    try:
        control_sat_id(sat_id)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Failed to resolve satellite ID. Details from guard: {e}"
        raise type(e)(error_msg) from None
    
    return master_obj[sat_id]

def get_SOT_define_sat_id(position: str, year: str, day: str) -> str:
    """
    Determines the active satellite ID for a given position ('east' or 'west') at a specific year and Julian day.
    Uses strict TRANSITIONS logic to resolve the historical/operational satellite.
    
    Extremely strict: inputs must be exactly as validated by control_* guards.
    Returns the resolved satellite ID ('16', '17', '18', or '19') as string.
    """
    ctx = sys._getframe().f_code.co_name

    try:
        control_position(position)
        control_year(year)
        control_day(day)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Invalid input arguments. Details: {e}"
        raise type(e)(error_msg) from None

    date_str = f"{year}-{day}"
    try:
        date_obj = datetime.strptime(date_str, "%Y-%j")
    except ValueError as ve:
        raise ValueError(f"❌ [DATE PARSE ERROR in {ctx}()]: Invalid year-day combination '{date_str}'. Details: {ve}") from None

    if position == "east":
        resolved_sat_id = "19" if date_obj >= TRANSITIONS["east_16_to_19"] else "16"
    elif position == "west":
        resolved_sat_id = "18" if date_obj >= TRANSITIONS["west_17_to_18"] else "17"
    else:
        raise RuntimeError(f"❌ [🛡️🛡️🛡️ INTEGRITY ERROR in {ctx}()]: Unknown position '{position}' after guard validation - possible logic bypass.")

    try:
        control_sat_id(resolved_sat_id)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Resolved sat_id '{resolved_sat_id}' is invalid according to Source of Truth. Details: {e}"
        raise type(e)(error_msg) from None

    return resolved_sat_id

def get_SOT_define_position(sat_id: str) -> str:
    """
    Returns the operational position ('east' or 'west') for a specific satellite ID.
    Resolves directly from the Source of Truth (SoT) metadata.
    
    Extremely strict: validates input, retrieves metadata, and checks stored position.
    """
    ctx = sys._getframe().f_code.co_name

    try:
        control_sat_id(sat_id)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Invalid satellite ID. Details: {e}"
        raise type(e)(error_msg) from None

    try:
        sat_metadata = get_SOT_goes_info_sat(sat_id)
    except Exception as e:
        raise RuntimeError(f"❌ [FUNCTION ERROR in {ctx}()]: Failed to retrieve metadata from Source of Truth. Details: {e}") from None

    if "position" not in sat_metadata:
        raise RuntimeError(f"❌ [INTEGRITY ERROR in {ctx}()]: Satellite metadata for '{sat_id}' missing required field 'position' in Source of Truth.")
    
    resolved_position = sat_metadata["position"]

    try:
        control_position(resolved_position)
    except Exception as e:
        error_msg = f"❌ [FUNCTION ERROR in {ctx}()]: Resolved position '{resolved_position}' for satellite '{sat_id}' is invalid according to guards. Details: {e}"
        raise type(e)(error_msg) from None

    return resolved_position

# ===================================================================
# UNIT TESTING (Main Execution)
# ===================================================================
if __name__ == "__main__":
    print("\n" + " LEGION GOES: SATELLITE SOT UNIT TESTS ".center(80, "="))
    print("Running strict integrity and logic tests...\n")

    try:
        # Test 1: Full SoT retrieval and integrity
        all_sats = get_SOT_goes_info_sat()
        assert isinstance(all_sats, MappingProxyType), "Full SoT must be immutable proxy"
        assert len(all_sats) == 4, f"Expected 4 satellites, got {len(all_sats)}"
        print("✅ Test 1: Full SoT retrieval → OK (4 satellites mapped, immutable)")

        # Test 2: Specific satellite metadata
        g19_meta = get_SOT_goes_info_sat("19")
        assert g19_meta["bucket"] == "noaa-goes19", "GOES-19 bucket mismatch"
        assert g19_meta["position"] == "east", "GOES-19 position mismatch"
        print("✅ Test 2: Single satellite metadata ('19') → OK")

        # Test 3: East transition (using real date April 7, 2025)
        east_before = get_SOT_define_sat_id("east", "2025", "090")  # Before April 7
        east_after = get_SOT_define_sat_id("east", "2025", "100")   # After April 7
        assert east_before == "16", f"Expected '16' before transition, got '{east_before}'"
        assert east_after == "19", f"Expected '19' after transition, got '{east_after}'"
        print("✅ Test 3: East transition resolution → OK")

        # Test 4: West resolution
        west_2022 = get_SOT_define_sat_id("west", "2022", "050")
        west_2025 = get_SOT_define_sat_id("west", "2025", "050")
        assert west_2022 == "17", f"Expected '17' in 2022, got '{west_2022}'"
        assert west_2025 == "18", f"Expected '18' in 2025, got '{west_2025}'"
        print("✅ Test 4: West historical resolution → OK")

        # Test 5: Position from ID
        pos_18 = get_SOT_define_position("18")
        pos_19 = get_SOT_define_position("19")
        assert pos_18 == "west", f"Expected 'west' for sat 18, got '{pos_18}'"
        assert pos_19 == "east", f"Expected 'east' for sat 19, got '{pos_19}'"
        print("✅ Test 5: Position from ID → OK")

        # Test 6: Negative case - invalid input should raise
        try:
            get_SOT_define_sat_id("EAST", "2026", "001")  # uppercase invalid
            print("❌ Test 6: Invalid position should raise error → FAILED (no raise)")
        except Exception:
            print("✅ Test 6: Invalid input correctly raises error")

        print("\n" + " ALL TESTS PASSED SUCCESSFULLY ".center(80, "="))

    except AssertionError as ae:
        print(f"\n❌ [ASSERTION FAILED]: {ae}")
    except Exception as e:
        print(f"\n❌ [UNEXPECTED TEST FAILURE]: {e}")
    
    print("=" * 80 + "\n")
