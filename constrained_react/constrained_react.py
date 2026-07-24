import os
import json
import logging
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed
from google import genai
from google.genai import types

from tools import TOOL_MAP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("hotel_agent")

MAX_STEPS = 6
MAX_CONSECUTIVE_ERRORS_PER_ACTION = 2

ALLOWED_ACTIONS = [
    "check_guest_tier",
    "check_occupancy",
    "dispatch_maintenance",
    "issue_compensation",
    "final_answer",
    "escalate",
]

class AgentStep(BaseModel):
    thought: str
    action: Literal[
        "check_guest_tier",
        "check_occupancy",
        "dispatch_maintenance",
        "issue_compensation",
        "final_answer",
        "escalate",
    ]
    action_input: dict


script_dir = Path(__file__).resolve().parent
env_path = script_dir.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Please set it in the .env file.")

client = genai.Client(api_key=api_key)

class CheckGuestTierInput(BaseModel):
    room_number: str

class CheckOccupancyInput(BaseModel):
    pass

class DispatchMaintenanceInput(BaseModel):
    room_number: str
    issue: str

class IssueCompensationInput(BaseModel):
    room_number: str
    comp_type: str

class EscalateInput(BaseModel):
    reason: str = "Unspecified reason"
    message: str = "Escalated to a human supervisor."

class FinalAnswerInput(BaseModel):
    message: str

ACTION_INPUT_MODELS = {
    "check_guest_tier": CheckGuestTierInput,
    "check_occupancy": CheckOccupancyInput,
    "dispatch_maintenance": DispatchMaintenanceInput,
    "issue_compensation": IssueCompensationInput,
    "escalate": EscalateInput,
    "final_answer": FinalAnswerInput,
}

SYSTEM_PROMPT = f"""
You are a hotel customer service agent.

Your task is to decide the next action based on the guest's message
and the observations from previous tool calls.

Allowed actions and their descriptions:

- check_guest_tier:
    Description: Returns the guest's VIP status for a room.
    Input format:
    {{
        "room_number": "<room number>"
    }}

- check_occupancy:
    Description: Returns hotel occupancy and available rooms.
    Input format:
    {{}}

- dispatch_maintenance:
    Description: Creates a maintenance ticket.
    Input format:
    {{
        "room_number": "<room number>",
        "issue": "<short issue>"
    }}

- issue_compensation:
    Description: Applies a compensation voucher.
    Input format:
    {{
        "room_number": "<room number>",
        "comp_type": "<voucher / discount / upgrade>"
    }}

- escalate:
    Description: Escalates the issue to a human supervisor when unable to resolve.
    Input format:
    {{
        "reason": "<reason>",
        "message": "<optional message>"
    }}

- final_answer:
    Description: Completes the request with a final response message for the guest.
    Input format:
    {{
        "message": "<final response>"
    }}

Rules:

- Never invent hotel information.
- Always use previous tool observations.
- Do not skip necessary checks.
- Use only the allowed actions.
- If you cannot confidently continue, use escalate.
- End only with final_answer or escalate.

Return ONLY valid JSON in this format:

{{
    "thought": "...",
    "action": "...",
    "action_input": {{}}
}}
"""

def execute_action(action: str, action_input: dict) -> dict:
    model_cls = ACTION_INPUT_MODELS.get(action)

    if model_cls is None:
        return {"error": f"Unknown action '{action}'."}

    try:
        validated = model_cls(**action_input)
    except ValidationError as e:
        logger.warning("Invalid action_input for '%s': %s", action, e)
        return {"error": f"Invalid input: {e}"}

    if action == "final_answer":
        return {
            "status": "completed",
            "message": validated.message
        }

    if action == "escalate":
        return {
            "status": "escalated",
            "reason": validated.reason,
            "message": validated.message
        }

    tool = TOOL_MAP.get(action)
    if tool is None:
        return {"error": f"Tool implementation for '{action}' was not found in TOOL_MAP."}

    if action == "check_guest_tier":
        result = tool(validated.room_number)

    elif action == "check_occupancy":
        result = tool()

    elif action == "dispatch_maintenance":
        result = tool(
            validated.room_number,
            validated.issue
        )

    elif action == "issue_compensation":
        result = tool(
            validated.room_number,
            validated.comp_type
        )

    else:
        return {"error": "Unsupported action."}

    return {
        "action": action,
        "result": result
    }

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def generate_step(history: list[dict], user_message: str) -> AgentStep:
    history_text = "\n".join(
        f"- Thought: {h['thought']} | "
        f"Action: {h['action']} | "
        f"Input: {json.dumps(h['action_input'], ensure_ascii=False)} | "
        f"Observation: {json.dumps(h['observation'], ensure_ascii=False)}"
        for h in history
    )

    prompt = f"""{SYSTEM_PROMPT}

Guest message:
"{user_message}"

Previous steps:

{history_text if history else "No previous steps."}
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )

    try:
        return AgentStep.model_validate_json(response.text)
    except ValidationError as e:
        logger.warning(f"JSON Validation failed, retrying... Error: {e}")
        raise ValueError(f"Model returned invalid JSON structure: {e}")


def constrained_react_agent(user_message: str) -> str:
    history: list[dict] = []
    consecutive_errors_by_action: dict[str, int] = {}

    for step in range(MAX_STEPS):
        try:
            agent_step = generate_step(history, user_message)
        except Exception as e:
            logger.error("Validation failed after retries: %s", e)
            return "Request escalated due to a processing error."

        logger.info(
            "Step %d | Thought: %s",
            step + 1,
            agent_step.thought,
        )

        logger.info(
            "Step %d | Action: %s | Input: %s",
            step + 1,
            agent_step.action,
            agent_step.action_input,
        )

        if agent_step.action not in ALLOWED_ACTIONS:
            return "Action rejected: not permitted."

        observation = execute_action(
            agent_step.action,
            agent_step.action_input,
        )

        logger.info(
            "Step %d | Observation: %s",
            step + 1,
            observation,
        )

        history.append(
            {
                "thought": agent_step.thought,
                "action": agent_step.action,
                "action_input": agent_step.action_input,
                "observation": observation,
            }
        )

        if isinstance(observation, dict) and "error" in observation:
            consecutive_errors_by_action[agent_step.action] = (
                consecutive_errors_by_action.get(
                    agent_step.action,
                    0,
                )
                + 1
            )

            if (
                consecutive_errors_by_action[agent_step.action]
                >= MAX_CONSECUTIVE_ERRORS_PER_ACTION
            ):
                logger.warning(
                    "Action '%s' failed repeatedly.",
                    agent_step.action,
                )
                return (
                    f"Escalated because '{agent_step.action}' "
                    f"failed repeatedly."
                )
        else:
            consecutive_errors_by_action[
                agent_step.action
            ] = 0

        if agent_step.action in ["final_answer", "escalate"]:
            if agent_step.action == "escalate":
                return agent_step.action_input.get("message", "Escalated to human supervisor.")
            return agent_step.action_input.get("message", "Request completed.")

    return "Request escalated because MAX_STEPS was exceeded."

if __name__ == "__main__":
    test_messages = [
        "Room 402 has no air conditioning.",
        "Room 310 has a broken shower. Please send maintenance.",
        "Guest in room 105 is unhappy and deserves compensation.",
        "Can you check hotel occupancy?",
    ]

    for msg in test_messages:
        print("Guest:", msg)
        result = constrained_react_agent(msg)
        print("Final Result:", result)