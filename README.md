
# Autonomous Agents Lab: Aurelia Hotels & Resorts

## The Company & The Problem

**Company:** Aurelia Hotels & Resorts, a luxury hospitality chain. 
**The Problem:** Automated In-Stay Issue Escalation. When a guest reports a physical issue (e.g., broken AC, plumbing leak) or expresses dissatisfaction, the hotel must dynamically decide how to triage the situation. This involves dispatching maintenance, checking the guest's loyalty tier, and issuing context-appropriate compensation (e.g., VIPs get premium service credits, standard guests get discount vouchers).

**Why This Requires an Agent (Not a Script):**
A rule-based script fails because the resolution sequence requires dynamic, dependent reasoning. The decision to issue compensation and what type to issue depends entirely on the dynamic result of a previous action (`check_guest_tier`). Hardcoding every permutation of room status, issue severity, and VIP tier creates an unmaintainable, brittle decision tree. 

---

## The Four Architectures

This repository contains four distinct implementations of an AI agent attempting to solve the triage problem.

1. **`reactive/` (Rule-Based Agent):** A pure `if/then` decision loop using regex for room extraction. No LLM calls.
2. **`routing/` (Deterministic Routing Agent):** Uses a single constrained LLM call (Gemini) to classify the intent into strict categories (e.g., `MAINTENANCE_NEEDED`), then passes control to standard, testable Python logic.
3. **`unconstrained_react/` (Unconstrained LLM Agent):** A free-form Reasoning-Acting (ReAct) loop. The model has full control over tool usage and stopping conditions with no hard limits.
4. **`constrained_react/` (Constrained ReAct Agent):** A ReAct loop tightly bounded by Pydantic schema validation, a rigid tool allow-list, bounded retries via Tenacity, and a strict `MAX_STEPS = 6` limit.

---

## How to Run


**Prerequisites:**
* Python 3.10+
* A Google Gemini API key (Free Tier compatible).

**Setup:**
1. Clone this repository.
2. Install the required dependencies from requirements.txt 

3. Create a `.env` file in the root directory and add your API key:
GEMINI_API_KEY=your_api_key_here

4. Run the main execution script to test all architectures against the standard test cases:
```bash
python main.py
```



*Note: The agents are currently configured to use `gemini-3.1-flash-lite`.*

---

## Architecture Comparison & Findings

The following data is based on our test suite of 10 varying inputs.

| Metric | Reactive | Routing | Constrained ReAct | Unconstrained ReAct |
| --- | --- | --- | --- | --- |
| **LLM Calls per Request** | 0 | 1 | 2-3 (Successful runs) | 2-3 (Successful runs) |
| **Token Usage / Cost** | None | Low (Single short prompt) | High (Iterative prompt injection) | High (Iterative prompt injection) |
| **Latency** | < 0.1s (Instant) | ~1.3s | ~3.5s - 5.0s | ~4.0s - 5.5s |
| **Parsing Reliability** | Poor (Regex fails easily) | High (Enforced JSON) | 100% Strict (Pydantic validated) | Fragile (Regex parsing) |

### What Broke: Tricky Inputs & Edge Cases

* **The Reactive Agent's Brittleness:** When given `"Room ABC has no air conditioning"` (Test 6) or `"I want a free vacation"` (Test 7), the regex parser failed entirely, resulting in unhelpful default escalations or system failures. Furthermore, it could not dynamically chain tools, forcing it to blindly issue a generic `$20 Voucher` to everyone who complained.
* **The Routing Agent's Rigidity:** While fast and reliable at classification, it cannot handle nuance. In Test 3, it correctly classified a `COMPENSATION_REQUEST`, but because it relies on static downstream code, it blindly applied a generic `Standard Protocol` without considering the specifics of the guest's complaint.
* **Rate Limiting (The Infrastructure Bottleneck):** During testing (Tests 4 through 10), all LLM-powered agents hit a `429 RESOURCE_EXHAUSTED` error. This was caused by exceeding the 15 Requests-Per-Minute quota on the Gemini Free Tier.
* *Observation:* The **Constrained ReAct Agent** handled this gracefully. Tenacity intercepted the API failure, attempted its bounded retries, and then cleanly output: `Request escalated due to a processing error.` The unconstrained loop simply crashed and printed a raw stack trace.


* **Unconstrained Hallucination Risks:** While the Unconstrained agent successfully navigated the happy paths, its lack of schemas makes it dangerous for production. It relied on unvalidated string matching (e.g., `Action: dispatch_maintenance(room_number="402", issue="no air conditioning")`), which is highly vulnerable to breaking the execution loop if the model changes its syntax slightly.
