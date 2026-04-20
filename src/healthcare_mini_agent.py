# src/healthcare_mini_agent.py
# Healthcare Mini Agent — Documentation & Triage Assistant
# Bilingual Finnish/English support

import json
import anthropic
from utils.helpers import get_api_key, print_tool_result, print_separator

# ── Client setup ───────────────────────────────────────────────────────────────

client = anthropic.Anthropic(api_key=get_api_key())
MODEL = "claude-sonnet-4-5"

# ══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

tools = [
    {
        "name": "assess_triage_urgency",
        "description": (
            "Assesses patient-reported symptoms and vital signs and returns a Finnish "
            "ABCDE triage urgency category with clinical rationale. "
            "A = Immediate (resuscitation), B = Very urgent (10 min), "
            "C = Urgent (30 min), D = Less urgent (60 min), E = Non-urgent (120 min). "
            "Accepts symptom descriptions in Finnish or English."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "string",
                    "description": "Patient-reported symptoms in Finnish or English, e.g. 'chest pain and shortness of breath' or 'rintakipu ja hengenahdistus'"
                },
                "heart_rate": {
                    "type": "integer",
                    "description": "Heart rate in beats per minute"
                },
                "blood_pressure_systolic": {
                    "type": "integer",
                    "description": "Systolic blood pressure in mmHg"
                },
                "respiratory_rate": {
                    "type": "integer",
                    "description": "Respiratory rate in breaths per minute"
                },
                "consciousness": {
                    "type": "string",
                    "description": "Consciousness level: alert, voice, pain, or unresponsive (AVPU scale)"
                }
            },
            "required": ["symptoms"]
        }
    },

    {
        "name": "lookup_icd10_codes",
        "description": (
            "Looks up relevant ICD-10 diagnosis codes for a given symptom or condition description. "
            "Returns the most clinically relevant codes with their official names and usage notes. "
            "Uses ICD-10-FI, the Finnish national edition used in Finnish EHR systems. "
            "Accepts input in Finnish or English."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Symptom or condition description in Finnish or English, e.g. 'chest pain' or 'rintakipu'"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of ICD-10 codes to return (default: 5)"
                }
            },
            "required": ["description"]
        }
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS
# ══════════════════════════════════════════════════════════════════════════════

def assess_triage_urgency(
    symptoms: str,
    heart_rate: int = None,
    blood_pressure_systolic: int = None,
    respiratory_rate: int = None,
    consciousness: str = None
) -> str:
    """
    Assess triage urgency using the Finnish ABCDE scale.
    Returns a structured triage assessment with category and rationale.
    Vitals are optional but improve accuracy when provided.
    """

    # Build a structured summary of available data
    vitals_lines = []
    if heart_rate is not None:
        vitals_lines.append(f"  Heart rate: {heart_rate} bpm")
    if blood_pressure_systolic is not None:
        vitals_lines.append(f"  Systolic BP: {blood_pressure_systolic} mmHg")
    if respiratory_rate is not None:
        vitals_lines.append(f"  Respiratory rate: {respiratory_rate} breaths/min")
    if consciousness is not None:
        vitals_lines.append(f"  Consciousness (AVPU): {consciousness}")

    vitals_summary = "\n".join(vitals_lines) if vitals_lines else "  No vitals provided."

    # Triage category definitions for reference
    scale = (
        "A – Immediate (resuscitation, seen at once)\n"
        "B – Very urgent (seen within 10 minutes)\n"
        "C – Urgent (seen within 30 minutes)\n"
        "D – Less urgent (seen within 60 minutes)\n"
        "E – Non-urgent (seen within 120 minutes)"
    )

    result = (
        f"TRIAGE ASSESSMENT REQUEST\n"
        f"{'─' * 40}\n"
        f"Symptoms: {symptoms}\n\n"
        f"Vitals:\n{vitals_summary}\n\n"
        f"ABCDE Scale Reference:\n{scale}\n"
        f"{'─' * 40}\n"
        f"Please assign a triage category (A–E) with:\n"
        f"1. Category and target time to be seen\n"
        f"2. Clinical rationale for the category\n"
        f"3. Key warning signs to monitor\n"
        f"4. Immediate actions recommended"
    )

    return result

def lookup_icd10_codes(description: str, max_results: int = 5) -> str:
    """
    Look up relevant ICD-10-FI diagnosis codes for a symptom or condition.
    Returns structured code suggestions with names and usage notes.
    ICD-10-FI is the Finnish national edition used in Lifecare and other Finnish EHR systems.
    """

    result = (
        f"ICD-10-FI CODE LOOKUP REQUEST\n"
        f"{'─' * 40}\n"
        f"Query: {description}\n"
        f"Maximum results requested: {max_results}\n\n"
        f"Please return the {max_results} most relevant ICD-10-FI codes for this "
        f"symptom or condition.\n\n"
        f"For each code provide:\n"
        f"1. ICD-10 code (e.g. R07.4)\n"
        f"2. Official English name\n"
        f"3. Finnish name (ICD-10-FI)\n"
        f"4. Brief note on when this code applies vs the others\n\n"
        f"Order results from most to least likely based on the description.\n"
        f"Flag any codes that are commonly confused with each other."
    )

    return result


# ══════════════════════════════════════════════════════════════════════════════
# TOOL ROUTER
# ══════════════════════════════════════════════════════════════════════════════

def run_tool(tool_name: str, tool_input: dict) -> str:
    """Route a tool call from Claude to the correct Python function."""
    if tool_name == "assess_triage_urgency":
        return assess_triage_urgency(**tool_input)
    elif tool_name == "lookup_icd10_codes":
        return lookup_icd10_codes(**tool_input)
    else:
        return f"Unknown tool: {tool_name}"


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a clinical documentation and triage support assistant for Finnish healthcare professionals.
You support nurses and doctors in the Finnish healthcare system by:
- Assessing triage urgency using the Finnish ABCDE scale
- Looking up relevant ICD-10 diagnosis codes
- Generating structured SOAP notes ready for EHR entry
- Checking medication lists for drug interactions
- Summarising Finnish Current Care Guidelines (Käypä hoito) for conditions

You understand both Finnish and English. If a user writes in Finnish, respond in Finnish.
If they write in English, respond in English.

You are a decision-support tool only. Always remind users that clinical decisions
rest with the licensed healthcare professional.

Be concise and structured. Use clinical language appropriate for a professional audience.
"""


# ══════════════════════════════════════════════════════════════════════════════
# AGENT LOOP
# ══════════════════════════════════════════════════════════════════════════════

def run_agent(user_message: str) -> None:
    """Run the agent loop for a single user query."""
    print_separator()
    print(f"👤 User: {user_message}")
    print_separator()

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages
        )

        # Collect all tool calls in this response before replying
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print_tool_result(block.name, str(block.input))
                result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        # If Claude made tool calls, send all results back and continue loop
        if tool_results:
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            continue

        # No tool calls — Claude has a final text response
        for block in response.content:
            if hasattr(block, "text"):
                print(f"\n🤖 Agent:\n{block.text}")
        break


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — Interactive loop
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print_separator("═")
    print("  Healthcare Mini Agent — Triage & Documentation Assistant")
    print("  Bilingual Finnish/English | Powered by Claude")
    print_separator("═")
    print("Type your query in Finnish or English. Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "lopeta"):
                print("Goodbye / Näkemiin 👋")
                break
            run_agent(user_input)
        except KeyboardInterrupt:
            print("\nGoodbye / Näkemiin 👋")
            break
