import os
from pathlib import Path
from dotenv import load_dotenv
from reactive_agent import reactive_agent
from routing_agent import routing_agent
from constrained_react import constrained_react_agent
from unconstrained_react import run_unconstrained_agent

# Load API Key
script_dir = Path(__file__).resolve().parent
env_path = script_dir / ".env"

if env_path.exists():
    load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")

# Shared Test Cases

TEST_CASES = [
    "Room 402 has no air conditioning.",
    "Room 310 has a broken shower. Please send maintenance.",
    "Guest in room 105 is unhappy and deserves compensation.",
    "Can you check hotel occupancy?",
    "Room 999 has no AC.",
    "Room ABC has no air conditioning.",
    "I want a free vacation.",
    "",
    "asdfghjkl",
    "Room 220 has no electricity and water."
]

# Runner
def print_header(title):
    print(title)
  
for i, message in enumerate(TEST_CASES, 1):

    print_header(f"TEST CASE {i}")
    print("INPUT:")
    print(message if message else "<EMPTY MESSAGE>")

    # Reactive
    print("\nReactive Agent")
    try:
        print(reactive_agent(message))
    except Exception as e:
        print("ERROR:", e)

    # Routing
    print("\nRouting Agent")
    try:
        print(routing_agent(message))
    except Exception as e:
        print("ERROR:", e)

    # Constrained ReAct
    print("\nConstrained ReAct Agent")
    try:
        print(constrained_react_agent(message))
    except Exception as e:
        print("ERROR:", e)
      
    # Unconstrained ReAct
    print("\nUnconstrained ReAct Agent")
    try:
        print(run_unconstrained_agent(message, api_key))
    except Exception as e:
        print("ERROR:", e)
print("ALL TESTS FINISHED")
