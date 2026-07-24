# agent.py
import re
import os
from google import genai
from tools import TOOL_MAP
from pathlib import Path
from dotenv import load_dotenv

SYSTEM_PROMPT = """
You are an autonomous operations agent for Aurelia Hotels & Resorts.
Your job is to resolve guest issues by reasoning step-by-step and using tools.

Available Tools:
- check_guest_tier(room_number): Check guest loyalty status.
- check_occupancy(): Check available room inventory.
- dispatch_maintenance(room_number, issue): Send maintenance to fix an issue.
- issue_compensation(room_number, comp_type): Grant free vouchers/credits.

You MUST use the following format:

Thought: Reason about what to do next.
Action: tool_name(arg_name="value")
PAUSE

Once an Action is submitted, you will receive an Observation.
When you have completely resolved the issue, output:
Final Answer: A summary of all actions taken to solve the guest's issue.
"""


def extract_action(text: str):
    match = re.search(r"Action:\s*(\w+)\((.*)\)", text)
    if not match:
        return None, None
    tool_name = match.group(1)
    args_raw = match.group(2)

    args = {}
    for param in args_raw.split(","):
        if "=" in param:
            k, v = param.split("=", 1)
            args[k.strip()] = v.strip().strip("'\"")
    return tool_name, args


def run_unconstrained_agent(user_issue: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)
    prompt = f"{SYSTEM_PROMPT}\n\nGuest Issue: {user_issue}\n"
    print("=== STARTING UNCONSTRAINED REACT LOOP ===")

    while True:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
        )
        model_output = response.text
        print(model_output)
        prompt += model_output + "\n"

        # Check for completion
        if "Final Answer:" in model_output:
            return model_output.split("Final Answer:")[1].strip()

        tool_name, tool_args = extract_action(model_output)
        if tool_name and tool_name in TOOL_MAP:
            try:
                observation = TOOL_MAP[tool_name](**tool_args)
            except Exception as e:
                observation = f"Error executing tool {tool_name}: {str(e)}"

            obs_str = f"Observation: {observation}\n"
            print(obs_str)
            prompt += obs_str
        elif "PAUSE" in model_output:
            obs_str = "Observation: Failed to parse tool call format. Make sure to use: Action: tool_name(arg=\"value\")\n"
            print(obs_str)
            prompt += obs_str


if __name__ == "__main__":

    test_case = "Room 402 AC is leaking heavily and making loud noises."
    #needed to get .env file if placed in project root directory
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("GEMINI_API_KEY")
    print(api_key)
    result = run_unconstrained_agent(test_case, api_key)
    print(f"\nFinal Result:\n{result}")