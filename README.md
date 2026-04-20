# Healthcare Mini Agent 🏥

A bilingual (Finnish/English) AI agent for clinical documentation and triage support in the Finnish healthcare sector. Built as a portfolio project inspired by the goal of helping healthcare professionals spend more time caring for patients and less time documenting - it is not a tool to be used in actual healthcare work, but it uses real data to demonstrate what a more comprehensive tool could do. 

Powered by [Claude](https://www.anthropic.com/claude) via the Anthropic SDK. Please note, real patient data should not be provided to AI analysis with identifiable information, even for testing a demonstartion tool like this. 

---

## What it does

The agent assists nurses and doctors by autonomously selecting and chaining the right clinical tools based on a natural language query — in Finnish or English.

| Tool | Description |
|---|---|
| `assess_triage_urgency` | Assigns a Finnish ABCDE triage category with rationale and recommended actions |
| `lookup_icd10_codes` | Returns ranked ICD-10-FI diagnosis codes for a symptom or condition |
| `generate_soap_note` | Drafts a structured SOAP note ready for EHR entry |
| `check_drug_interactions` | Checks a medication list for interactions, contraindications, and polypharmacy risk |
| `get_care_pathway` | Summarises the Finnish Current Care Guideline (Käypä hoito) for a condition |

---
## How it works

1. You type a query in Finnish or English
2. Claude (AI) reads the intent and selects the appropriate tool(s)
3. Each tool builds a structured clinical prompt and returns it to Claude
4. Claude interprets the result and responds in natural language
5. If your query requires multiple tools, Claude chains them automatically in the right order

No commands or flags needed — just describe what you need as you would to a colleague.

---

## Architecture

```
healthcare-mini-agent/
├── .env                           ← API key (gitignored)
├── requirements.txt
├── verify_setup.py                ← confirms environment before first run
├── src/
│   └── healthcare_mini_agent.py  ← all tools, router, agent loop, main
└── utils/
    ├── __init__.py
    └── helpers.py                 ← get_api_key, print_tool_result, print_separator
```

**Agent loop:** Claude autonomously decides which tools to call and in what order. All tool results in a response are collected before being sent back to Claude, enabling multi-tool chaining in a single query.

---

## Setup

**Requirements:** Python 3.10+, an [Anthropic API key](https://console.anthropic.com)

```bash
# Clone and enter the repo
git clone https://github.com/MerjaR/healthcare-mini-agent.git
cd healthcare-mini-agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Verify setup
python verify_setup.py
```

---

## Running the agent

```bash
python -m src.healthcare_mini_agent
```

Type `quit`, `exit`, or `lopeta` to exit. Press Ctrl+C to force quit.

---

## Example queries

### Triage assessment (English)

**Input:**
```
Patient has chest pain and shortness of breath, heart rate 118, BP 88/60, respiratory rate 24
```

**Example Output:**
```
TRIAGE CATEGORY: A – Immediate
Target: Seen at once / resuscitation bay
Rationale: Hypotension (88/60), tachycardia (118 bpm), and tachypnoea (24/min)
alongside chest pain and dyspnoea indicate haemodynamic instability...
```

---

### Triage assessment (Finnish)

**Input:**
```
Potilaalla on rintakipu ja hengenahdistus, syke 118, verenpaine 88/60
```

**Example Output:**
```
TRIAGELUOKKA: A – Välitön
Tavoite: Hoitoon välittömästi / elvytyshuone
Perustelu: Hypotensio (88/60), takykardia (118 bpm) ja takypnea yhdistettynä
rintakipuun ja hengenahdistukseen viittaavat hemodynaamiseen epävakauteen...
```

---

### ICD-10 code lookup

**Input:**
```
What ICD-10 codes apply to chest pain?
```

**Example Output:**
```
R07.4  Chest pain, unspecified (Rintakipu, määrittämätön) — use when cause is unclear
R07.2  Precordial pain (Prekordiaalikipu) — localised to precordial area
I21.9  Acute myocardial infarction, unspecified — if MI confirmed
I20.0  Unstable angina — if ACS suspected without confirmed infarction
R07.3  Other chest pain — atypical presentations not fitting above
```

---

### SOAP note generation

**Input:**
```
Generate a SOAP note for a 45 year old male with chest pain for 2 hours,
HR 110, BP 145/90, no prior cardiac history
```

**Example Output:**
```
S – SUBJECTIVE
45-year-old male presenting with chest pain of 2 hours duration.
Patient reports no prior cardiac history.

O – OBJECTIVE
HR: 110 bpm (tachycardic)
BP: 145/90 mmHg (mildly hypertensive)
Onset: acute, 2 hours prior to presentation

A – ASSESSMENT
Working diagnosis: Chest pain, unspecified (R07.4)
Differential: Acute coronary syndrome (I21.9), unstable angina (I20.0),
musculoskeletal chest pain (M79.3)

P – PLAN
1. 12-lead ECG immediately
2. Troponin, FBC, BMP, coagulation screen
3. Aspirin 300mg if ACS not excluded
4. Continuous cardiac monitoring
5. Cardiology review if troponin elevated or ECG changes
6. Reassess in 30 minutes
```

---

### Drug interaction check

**Input:**
```
78 year old patient on warfarin, aspirin, ibuprofen, metformin, and lisinopril — any interactions?
```

**Example Output:**
```
⚠️  MAJOR: Warfarin + Ibuprofen
Consequence: NSAIDs inhibit platelet function and can displace warfarin from
plasma proteins, significantly increasing bleeding risk.
Action: Avoid combination. Consider paracetamol for analgesia instead.

⚠️  MODERATE: Warfarin + Aspirin
Consequence: Increased bleeding risk, particularly GI bleeding.
Action: Monitor INR closely. Ensure clinical indication justifies dual therapy.

ℹ️  POLYPHARMACY: Patient is 78 years old with 5 medications listed.
Fimea guidelines recommend a structured medication review.
```

---

### Care pathway lookup (Finnish)

**Input:**
```
Käypä hoito -suositus tyypin 2 diabeteksesta perusterveydenhuollossa
```

**Example Output:**
```
KÄYPÄ HOITO — TYYPIN 2 DIABETES

1. DIAGNOSTISET KRITEERIT
   Paastoglukoosi ≥7,0 mmol/l tai HbA1c ≥48 mmol/mol kahdessa mittauksessa...

2. ENSISIJAINEN HOITO
   Elintapamuutokset: liikunta, ruokavalio, painonhallinta.
   Lääkehoito: metformiini ensisijaisena lääkkeenä...

3. LÄHETTÄMISKRITEERIT
   Lähete erikoissairaanhoitoon: huono hoitotasapaino (HbA1c >75),
   munuaiskomplikaatiot, insuliinihoito...
```

---

### Multi-tool chaining

**Input:**
```
65 year old with chest pain, HR 112, BP 90/60 —
give me triage, ICD-10 codes, and the care pathway
```

**Example Output:**
```
Agent calls assess_triage_urgency → lookup_icd10_codes → get_care_pathway automatically
```

---

## Domain context

This project uses some of the key concepts in Finnish healthcare software:

- **ABCDE triage scale** — the Finnish/European emergency triage standard
- **ICD-10-FI** — the Finnish national edition of ICD-10 used in Finnish EHR systems
- **SOAP notes** — the standard clinical documentation format 
- **Käypä hoito** — Finland's national evidence-based clinical guidelines (Finnish Medical Society Duodecim)
- **Fimea** — Finnish Medicines Agency, the authority for drug safety standards in Finland
- **Polypharmacy risk** — a key concern in elderly care

---

## Disclaimer

This agent is a portfolio demonstration project and is **not intended for clinical use**. It should not be used in clinical work and these as well as all similar outputs should be reviewed by a licensed healthcare professional. Clinical decisions remain the responsibility of the treating clinician. No identifiable patient information should be submitted to the AI agent.

---

