import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from tools import check_guest_tier, dispatch_maintenance, issue_compensation, check_occupancy

script_dir = Path(__file__).resolve().parent
env_path = script_dir.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found.")

client = genai.Client(api_key=api_key)

class IssueCategory(str, Enum):
    MAINTENANCE_NEEDED = "MAINTENANCE_NEEDED"
    COMPENSATION_REQUEST = "COMPENSATION_REQUEST"
    INFO_REQUEST = "INFO_REQUEST"
    GENERAL = "GENERAL"

class RoutingClassification(BaseModel):
    category: IssueCategory
    room_number: str = Field(description="The room number, or 'UNKNOWN' if not provided.")
    issue_summary: str = Field(description="A 3-5 word summary of the problem.")


def classify_intent_with_llm(user_message: str) -> RoutingClassification:

    prompt = f"""
    You are the triage system for Aurelia Hotels.
    Classify the guest's message into one of the exact categories provided.
    Extract the room number if present. Summarize the issue.

    Guest Message: "{user_message}"
    """

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RoutingClassification,
            temperature=0.0
        )
    )

    return response.parsed


def routing_agent(user_message: str) -> str:

    print(f"\n--- Processing: {user_message} ---")
    classification = classify_intent_with_llm(user_message)
    print(f"LLM Classification: {classification.category.value} | Room: {classification.room_number}")


    if classification.category == IssueCategory.MAINTENANCE_NEEDED:
        if classification.room_number == "UNKNOWN":
            return "Action required: We need your room number to dispatch maintenance."

        action_result = dispatch_maintenance(classification.room_number, classification.issue_summary)
        return f"Resolution: {action_result}"

    elif classification.category == IssueCategory.COMPENSATION_REQUEST:
        if classification.room_number == "UNKNOWN":
            return "Action required: We need your room number to check your profile for compensation."

        tier_info = check_guest_tier(classification.room_number)
        if "VIP" in tier_info:
            comp_result = issue_compensation(classification.room_number, "Premium Spa Pass")
            return f"VIP Protocol Triggered. {tier_info}. {comp_result}"
        else:
            comp_result = issue_compensation(classification.room_number, "Standard Free Drink")
            return f"Standard Protocol. {tier_info}. {comp_result}"

    elif classification.category == IssueCategory.INFO_REQUEST:
        status = check_occupancy()
        return f"Information provided: {status}"

    else:
        return "Resolution: Forwarded to human front desk agent for review."


if __name__ == "__main__":
    test_messages = [
        "Room 402 has no air conditioning.",
        "Guest in room 105 is unhappy and deserves compensation.",
        "Can you check hotel occupancy?"
    ]

    for msg in test_messages:
        result = routing_agent(msg)
        print(f"Final Answer: {result}")