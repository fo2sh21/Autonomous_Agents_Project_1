import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found.")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """
Classify the user's request into ONLY one label.

Labels:
CHECK_GUEST_TIER
CHECK_OCCUPANCY
DISPATCH_MAINTENANCE
ISSUE_COMPENSATION
GENERAL

Return only the label.
"""


def classify_intent_with_llm(user_message: str) -> str:

    response = model.generate_content(
        f"{SYSTEM_PROMPT}\nUser: {user_message}"
    )

    return response.text.strip().upper()
    def routing_agent(user_message: str):

    intent = classify_intent_with_llm(user_message)

    if intent == "CHECK_GUEST_TIER":
        return "check_guest_tier"

    elif intent == "CHECK_OCCUPANCY":
        return "check_occupancy"

    elif intent == "DISPATCH_MAINTENANCE":
        return "dispatch_maintenance"

    elif intent == "ISSUE_COMPENSATION":
        return "issue_compensation"

    else:
        return "general_support"
        if __name__ == "__main__":

    test_messages = [
        "Room 402 has no air conditioning.",
        "Can you check hotel occupancy?",
        "Guest in room 310 deserves compensation.",
        "What is the VIP status of room 402?",
        "Hello, I need some help."
    ]

    for msg in test_messages:

        print("User:", msg)

        action = routing_agent(msg)

        print("Predicted Action:", action)
