def classify_intent_with_llm(user_message: str) -> str:
    """
    Temporary simulation of an LLM.
    Replace with a real LLM later.
    """

    message = user_message.lower()

    if "refund" in message or "money back" in message:
        return "BILLING"

    elif "booking" in message or "reservation" in message:
        return "BOOKING"

    elif "wifi" in message or "internet" in message or "ac" in message:
        return "TECHNICAL"

    elif "clean" in message or "dirty" in message or "towel" in message:
        return "HOUSEKEEPING"

    elif "food" in message or "breakfast" in message:
        return "ROOM_SERVICE"

    else:
        return "GENERAL"


def routing_agent(user_message: str):

    intent = classify_intent_with_llm(user_message)

    if intent == "BILLING":
        return "Billing Department"

    elif intent == "BOOKING":
        return "Front Desk"

    elif intent == "TECHNICAL":
        return "Technical Maintenance"

    elif intent == "HOUSEKEEPING":
        return "Housekeeping"

    elif intent == "ROOM_SERVICE":
        return "Room Service"

    else:
        return "Customer Service"
