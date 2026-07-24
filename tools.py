#example data for the tools
GUEST_DATABASE = {
    "402": {"name": "Eleanor Vance", "tier": "Platinum VIP"},
    "105": {"name": "Marcus Wright", "tier": "Standard Guest"},
    "310": {"name": "Sophia Lin", "tier": "Gold VIP"}
}

OCCUPANCY_STATUS = {
    "occupancy_rate": 0.98,
    "available_rooms": ["102"],  # Standard room only
    "suites_available": 0
}

def check_guest_tier(room_number: str) -> str:
    guest = GUEST_DATABASE.get(str(room_number))
    if guest:
        return f"Room {room_number}: Guest {guest['name']}, Status: {guest['tier']}"
    return f"Room {room_number} is currently vacant or unlisted."

def check_occupancy() -> str:
    return (
        f"Occupancy Rate: {OCCUPANCY_STATUS['occupancy_rate']*100}%. "
        f"Available standard rooms: {OCCUPANCY_STATUS['available_rooms']}. "
        f"Suites available: {OCCUPANCY_STATUS['suites_available']}."
    )

def dispatch_maintenance(room_number: str, issue: str) -> str:
    return f"Maintenance ticket created for Room {room_number}. Issue: '{issue}'. Priority assigned."

def issue_compensation(room_number: str, comp_type: str) -> str:
    return f"Successfully applied '{comp_type}' voucher to the guest in Room {room_number}."

TOOL_MAP = {
    "check_guest_tier": check_guest_tier,
    "check_occupancy": check_occupancy,
    "dispatch_maintenance": dispatch_maintenance,
    "issue_compensation": issue_compensation
}