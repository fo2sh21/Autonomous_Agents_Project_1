def reactive_agent(user_message: str) -> str:

    message = user_message.lower()

    if "vip" in message or "tier" in message or "status" in message:
        return "check_guest_tier"

    elif "occupancy" in message or "available room" in message:
        return "check_occupancy"

    elif (
        "ac" in message
        or "air conditioner" in message
        or "broken" in message
        or "maintenance" in message
        or "shower" in message
    ):
        return "dispatch_maintenance"

    elif (
        "refund" in message
        or "voucher" in message
        or "compensation" in message
        or "discount" in message
    ):
        return "issue_compensation"

    else:
        return "escalate"
