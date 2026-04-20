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

   {
        "name": "generate_soap_note",
        "description": (
            "Generates a structured SOAP note (Subjective, Objective, Assessment, Plan) "
            "from patient information, ready for entry into an EHR system such as Lifecare. "
            "Accepts input in Finnish or English and generates the note in the same language. "
            "SOAP notes follow Finnish healthcare documentation standards."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_age": {
                    "type": "integer",
                    "description": "Patient age in years"
                },
                "patient_gender": {
                    "type": "string",
                    "description": "Patient gender, e.g. 'male', 'female', 'other' or Finnish equivalent"
                },
                "chief_complaint": {
                    "type": "string",
                    "description": "The patient's primary complaint in their own words, in Finnish or English"
                },
                "symptoms": {
                    "type": "string",
                    "description": "Detailed symptom description including onset, duration, severity"
                },
                "vitals": {
                    "type": "string",
                    "description": "Vital signs as a free text string, e.g. 'HR 88, BP 130/85, RR 16, Temp 37.2'"
                },
                "medical_history": {
                    "type": "string",
                    "description": "Relevant past medical history, current medications, allergies"
                },
                "assessment": {
                    "type": "string",
                    "description": "Clinician's working diagnosis or differential diagnoses"
                }
            },
            "required": ["chief_complaint", "symptoms"]
        }
    },

    {
        "name": "check_drug_interactions",
        "description": (
            "Checks a list of medications for known drug-drug interactions, "
            "contraindications, and safety flags relevant to Finnish healthcare practice. "
            "References Fimea (Finnish Medicines Agency) safety principles. "
            "Accepts medication names in Finnish or English (brand or generic names)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "medications": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of medication names, e.g. ['warfarin', 'aspirin', 'ibuprofen']"
                },
                "patient_age": {
                    "type": "integer",
                    "description": "Patient age in years — used to flag age-specific risks e.g. elderly polypharmacy"
                },
                "conditions": {
                    "type": "string",
                    "description": "Known patient conditions relevant to drug safety e.g. 'renal impairment, diabetes'"
                }
            },
            "required": ["medications"]
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

def generate_soap_note(
    chief_complaint: str,
    symptoms: str,
    patient_age: int = None,
    patient_gender: str = None,
    vitals: str = None,
    medical_history: str = None,
    assessment: str = None
) -> str:
    """
    Generate a structured SOAP note from patient information.
    SOAP = Subjective, Objective, Assessment, Plan.
    Output is formatted for direct entry into Finnish EHR systems such as Lifecare.
    """

    # Build patient context from available fields
    patient_info_lines = []
    if patient_age is not None:
        patient_info_lines.append(f"  Age: {patient_age}")
    if patient_gender is not None:
        patient_info_lines.append(f"  Gender: {patient_gender}")
    patient_info = "\n".join(patient_info_lines) if patient_info_lines else "  Not provided"

    result = (
        f"SOAP NOTE GENERATION REQUEST\n"
        f"{'─' * 40}\n"
        f"Patient:\n{patient_info}\n\n"
        f"Chief Complaint: {chief_complaint}\n\n"
        f"Symptoms: {symptoms}\n\n"
        f"Vitals: {vitals or 'Not provided'}\n\n"
        f"Medical History / Medications / Allergies: {medical_history or 'Not provided'}\n\n"
        f"Clinician Assessment: {assessment or 'Not provided'}\n\n"
        f"{'─' * 40}\n"
        f"Please generate a complete SOAP note with the following sections:\n\n"
        f"S – SUBJECTIVE\n"
        f"  Patient's own account of symptoms, onset, duration, severity, context.\n\n"
        f"O – OBJECTIVE\n"
        f"  Measurable findings: vitals, physical observations, test results.\n\n"
        f"A – ASSESSMENT\n"
        f"  Working diagnosis or differential diagnoses with ICD-10 codes where applicable.\n\n"
        f"P – PLAN\n"
        f"  Proposed actions: investigations, treatments, referrals, follow-up, patient instructions.\n\n"
        f"Format the note concisely for direct EHR entry. "
        f"Match the language of the input (Finnish or English). "
        f"Use clinical language appropriate for a professional audience."
    )

    return result

def check_drug_interactions(
    medications: list,
    patient_age: int = None,
    conditions: str = None
) -> str:
    """
    Check a medication list for drug-drug interactions and safety flags.
    References Fimea (Finnish Medicines Agency) safety principles.
    Flags age-specific risks for elderly patients (polypharmacy awareness).
    """

    med_list = "\n".join(f"  - {med}" for med in medications)

    # Flag polypharmacy risk for elderly patients
    polypharmacy_note = ""
    if patient_age is not None and patient_age >= 65 and len(medications) >= 5:
        polypharmacy_note = (
            f"\n⚠️  Polypharmacy alert: Patient is {patient_age} years old and has "
            f"{len(medications)} medications listed. "
            f"Fimea guidelines recommend structured medication review for elderly "
            f"patients on 5 or more medications.\n"
        )

    result = (
        f"DRUG INTERACTION CHECK REQUEST\n"
        f"{'─' * 40}\n"
        f"Medications ({len(medications)} total):\n{med_list}\n"
        f"{polypharmacy_note}\n"
        f"Patient age: {patient_age or 'Not provided'}\n"
        f"Known conditions: {conditions or 'Not provided'}\n\n"
        f"{'─' * 40}\n"
        f"Please check for:\n"
        f"1. Drug-drug interactions (severity: major / moderate / minor)\n"
        f"2. Contraindications given the patient's conditions\n"
        f"3. Age-specific risks if patient age is provided\n"
        f"4. Recommended monitoring or dose adjustments\n\n"
        f"For each interaction found provide:\n"
        f"  - Drugs involved\n"
        f"  - Severity level\n"
        f"  - Clinical consequence\n"
        f"  - Recommended action\n\n"
        f"If no significant interactions are found, confirm the combination appears safe "
        f"and note any routine monitoring still recommended."
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
    elif tool_name == "generate_soap_note":
        return generate_soap_note(**tool_input)
    elif tool_name == "check_drug_interactions":
        return check_drug_interactions(**tool_input)
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
