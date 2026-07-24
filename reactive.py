def reactive_agent(user_message: str) -> str:
   
    message = user_message.lower()

    # Billing
    if "refund" in message or "money back" in message or "charge" in message:
        return "Billing Department"

    # Booking
    elif "booking" in message or "reservation" in message or "check in" in message:
        return "Front Desk"

    # Technical
    elif (
        "wifi" in message
        or "internet" in message
        or "ac" in message
        or "air conditioner" in message
        or "tv" in message
    ):
        return "Technical Maintenance"

    # Housekeeping
    elif (
        "clean" in message
        or "dirty" in message
        or "towel" in message
        or "soap" in message
        or "bed" in message
    ):
        return "Housekeeping"

    # Room Service
    elif (
        "food" in message
        or "breakfast" in message
        or "lunch" in message
        or "dinner" in message
        or "room service" in message
    ):
        return "Room Service"

    # Default
    else:
        return "Customer Service"
