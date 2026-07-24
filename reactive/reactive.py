import re
from tools import check_occupancy, dispatch_maintenance, issue_compensation


def reactive_agent(user_message: str) -> str:

    message = user_message.lower()
    room_match = re.search(r"room (\d{3})", message)
    room_number = room_match.group(1) if room_match else "UNKNOWN"

    if "occupancy" in message or "available" in message:
        result = check_occupancy()
        return f"Resolution: {result}"
    elif "ac" in message or "air conditioning" in message or "shower" in message:
        if room_number == "UNKNOWN":
            return "Resolution: Failed. Room number is required for maintenance."
        result = dispatch_maintenance(room_number, "Generic maintenance requested via text")
        return f"Resolution: {result}"

    elif "compensation" in message or "unhappy" in message or "refund" in message:
        if room_number == "UNKNOWN":
            return "Resolution: Failed. Room number is required for compensation."
        result = issue_compensation(room_number, "Standard $20 Voucher")
        return f"Resolution: {result}"

    else:
        return "Resolution: Escalated to human front desk agent."


if __name__ == "__main__":
    test_messages = [
        "Room 402 has no air conditioning.",
        "Room 310 has a broken shower. Please send maintenance.",
        "Guest in room 105 is unhappy and deserves compensation.",
        "Can you check hotel occupancy?"
    ]

    print("=== RUNNING REACTIVE AGENT ===")
    for msg in test_messages:
        print(f"\nGuest: {msg}")
        result = reactive_agent(msg)
        print(f"Final Answer: {result}")