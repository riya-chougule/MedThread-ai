# 🩺 MedThread AI
### Evidence-Grounded Clinical Discharge Handoff Assistant

**Transforming fragmented Electronic Health Records (EHRs) into structured, evidence-linked clinical handoff drafts using Generative AI.**

MedThread AI is a healthcare Generative AI prototype that explores how Large Language Models (LLMs) can assist healthcare providers in preparing hospital discharge and transition-of-care documentation.

Rather than simply summarizing medical records, MedThread AI focuses on **clinical information extraction, multi-document synthesis, source traceability, uncertainty handling, and structured output validation**.

> **Project status:** Early-stage prototype under active development. Built using synthetic healthcare data for educational and research demonstration purposes.


<img width="1440" height="772" alt="Screenshot 2026-10-19 at 3 45 00 PM" src="https://github.com/user-attachments/assets/fa329804-7609-4e59-9fb8-c9c84758f3e4" />


<img width="1440" height="776" alt="needed" src="https://github.com/user-attachments/assets/39fc8c25-c09c-462d-aea7-39e80554d951" />


<img width="1440" height="774" alt="Screenshot 2026-10-19 at 3 43 06 PM" src="https://github.com/user-attachments/assets/f0ba9a1f-7ee4-4e34-9515-20d067e4e06d" />

---

## The Problem

A single hospital stay can generate substantial clinical documentation across multiple sources:

- Admission and physician progress notes
- Laboratory results and diagnostic imaging
- Medication orders and administration records
- Specialist consultations
- Discharge notes and follow-up instructions

When a patient transitions from a hospital to another healthcare provider, this information must be consolidated into an accurate and understandable clinical handoff.

However, important details may be distributed across numerous documents.

Healthcare providers must reconstruct the patient's clinical journey, identify treatment decisions, review medication changes, and determine whether important information remains unresolved.

This creates three major challenges:

**1. Fragmented clinical information**

Relevant patient information is scattered across multiple EHR documents and sections, making it difficult to reconstruct the complete hospitalization.

**2. Documentation burden**

Preparing discharge summaries requires clinicians to review extensive records and organize clinically relevant information into a coherent narrative.

**3. Patient-safety risks**

Incomplete medication reconciliation, missing follow-up instructions, and unclear pending-test status can contribute to communication failures during care transitions.

Research from the World Health Organization, Stanford Medicine, and the Agency for Healthcare Research and Quality highlights the importance of safe medication transitions, accurate clinical documentation, and reliable communication between care teams.

## The Solution

**MedThread AI helps organize fragmented hospital documentation into a structured, evidence-linked clinical handoff draft.**

The application processes supplied hospital records and generates a summary covering:

- Reason for admission
- Hospital course
- Documented discharge diagnoses
- Confirmed discharge medication changes
- Pending tests and unresolved results
- Follow-up instructions
- Missing or ambiguous clinical information

Each documented clinical fact is linked to its original source document, section, and supporting quotation.

The goal is to help a clinician review a coherent summary while retaining access to the underlying evidence.

**MedThread AI does not replace clinical judgment. All generated outputs require clinician review.**

---

## Key Features

### 1. Multi-Format EHR Input

Supports two input formats:

- **Text (`.txt`, `.md`):** Hospital documentation containing labeled clinical notes and source identifiers.
- **Excel (`.xlsx`):** Synthetic EHR-style workbooks containing patient encounters and associated clinical records.

For supported Excel workbooks, users can select a patient and hospitalization before generating a handoff.

### 2. AI-Powered Clinical Information Extraction

Uses an OpenAI language model through LangChain to identify relevant clinical facts and generate a structured handoff.

The extraction workflow is designed to distinguish documented findings from missing information and preserve the clinical meaning of source records.

### 3. Multi-Document Clinical Synthesis

Combines relevant information from multiple documents into a coherent clinical narrative.

For example, admission notes, progress notes, and discharge documentation can collectively describe the patient's presentation, treatments, and documented clinical course.

### 4. Evidence-Linked Clinical Statements

Each extracted clinical fact can include:

- Source document ID
- Source section
- Exact supporting quotation

Users can expand source references to inspect the original documentation.

### 5. Automated Source-Reference Validation

The validation pipeline checks whether cited:

- Document identifiers exist in the supplied records
- Section names correspond to source sections
- Quotations match the original section content

**Important:** Source-reference validation does not independently establish clinical accuracy or completeness.

### 6. Clinical Uncertainty Handling

MedThread AI distinguishes between:

- Explicitly documented information
- Explicitly documented absence of information
- Information that remains unclear

For example:

**Source statement:**

"No pending tests were mentioned in this document."

**Appropriate interpretation:**

The available documentation does not identify outstanding tests, but it does not confirm that all ordered investigations have been finalized.

This distinction helps prevent missing documentation from being incorrectly interpreted as a confirmed negative finding.

### 7. Medication Reconciliation Safeguards

The application distinguishes inpatient medication administration from confirmed discharge medication changes.

A medication administered during hospitalization is not automatically treated as a medication prescribed at discharge.

When the final medication plan is unclear, the handoff flags the need for reconciliation instead of inferring instructions.

### 8. Interactive Clinical Review Interface

The Streamlit interface provides:

- Patient and encounter selection
- Source-record preview
- Structured clinical handoff sections
- Expandable supporting evidence
- Validation and safety warnings
- Missing-information flags
- JSON export

---

## System Architecture

```text
                  Hospital Documentation
                            |
                +-----------+-----------+
                |                       |
           Text Records             Excel EHR
          (.txt / .md)                (.xlsx)
                |                       |
                +-----------+-----------+
                            |
                            v
                 Input Processing Layer
                            |
                  Patient / Encounter
                       Selection
                            |
                            v
                  LangChain + OpenAI
                            |
                Structured Clinical
                    Information
                     Extraction
                            |
                            v
                   Pydantic Schema
                      Validation
                            |
                            v
                 Post-Processing and
                  Safety Safeguards
                            |
                            v
                Source-Reference Checks
                            |
                            v
                    Streamlit UI
                            |
               +------------+------------+
               |                         |
         Clinical Handoff          JSON Export
         + Source Evidence
```

### Architecture Overview

**Input processing:** Reads text documentation or synthetic Excel-based encounter records.

**LLM extraction:** Uses LangChain and an OpenAI model to extract clinically relevant information.

**Structured output:** Pydantic defines the handoff schema and validates the returned data structure.

**Safety processing:** Applies rules for medication-change interpretation, pending-test uncertainty, and source-reference handling.

**Citation validation:** Checks document identifiers, section names, and supporting quotations against the supplied records.

**Presentation:** Streamlit renders the clinical handoff with expandable evidence and export functionality.

---

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| LLM integration | OpenAI API |
| LLM orchestration | LangChain |
| Structured output | Pydantic |
| Frontend | Streamlit |
| Data processing | Python, Excel processing |
| Environment configuration | python-dotenv |
| Testing | pytest |
| Version control | Git and GitHub |

### Why this stack?

**LangChain** provides a convenient framework for integrating the language model with structured extraction workflows.

**Pydantic** helps enforce a predictable schema rather than relying on unrestricted text generation.

**Streamlit** makes it possible to build an interactive prototype without introducing a complex frontend architecture.

**Python** supports the complete workflow, from document processing and validation to testing and presentation.

---

## Project Structure

```text
MedThread-ai/
│
├── data/
│   └── sample_records/
│       ├── demo_hospital_stay.txt
│       ├── fictional_patients.xlsx
│       └── synthetic_ehr.xlsx
│
├── src/
│   └── medthread/
│       ├── __init__.py
│       ├── app.py
│       ├── extractor.py
│       ├── schemas.py
│       ├── pipeline.py
│       ├── validation.py
│       ├── citation_repair.py
│       ├── assessment_normalizer.py
│       ├── assessment_safety.py
│       ├── ehr_reader.py
│       ├── excel_reader.py
│       ├── main.py
│       └── hospital_illustration.png
│
├── tests/
│   ├── test_assessment_safety.py
│   ├── test_excel_reader.py
│   ├── test_medication_quarantine.py
│   └── test_schemas.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10 or newer, with compatible dependencies
- An OpenAI API key
- Git
- VS Code or another Python development environment

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/MedThread-ai.git
cd MedThread-ai
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

Replace the placeholder with your own OpenAI API key.

Never commit `.env` or real credentials to GitHub.

### 5. Run the application

From the project root:

```bash
PYTHONPATH=src python -m streamlit run src/medthread/app.py
```

Streamlit will display a local application URL in the terminal.

### 6. Try the sample records

Use the synthetic demonstration files under:

```text
data/sample_records/
```

For example, upload:

```text
demo_hospital_stay.txt
```

Then select **Generate discharge handoff**.

The application will process the supplied documentation and display the structured draft with source references.

---

## Running Tests

From the project root:

```bash
PYTHONPATH=src python -m pytest -q
```

The tests cover selected components of the extraction and validation workflow, including schema behavior, Excel processing, medication safeguards, and assessment handling.

Passing these tests does not establish clinical safety or correctness.

---

## Design Principles

### Evidence Before Confidence

Generated clinical statements should remain traceable to supporting documentation.

### Uncertainty Is Important

Missing information should not be interpreted as proof that a clinical event did not occur.

### Structured Outputs Matter

Predictable schemas make downstream validation and review more manageable.

### Human Oversight Is Essential

The system prepares drafts for review rather than making autonomous clinical decisions.

### Transparency Over Black-Box Summaries

Users should be able to inspect the documentation behind generated statements.

---

## Current Limitations

MedThread AI is an early-stage prototype and has several important limitations:

1. **Synthetic data only:** The application is developed for fictional healthcare records and has not been validated on real clinical datasets.

2. **No live EHR integration:** The prototype does not connect directly to hospital EHR systems.

3. **Limited semantic verification:** Existing citation checks validate source matching but do not fully establish that generated clinical statements are supported by their quotations.

4. **Potential LLM errors:** The model may omit information, misinterpret documentation, or generate unsupported statements.

5. **No clinical validation:** The system has not been evaluated in real patient-care workflows.

6. **No established clinical performance:** Accuracy, completeness, safety, and time savings have not yet been demonstrated through formal clinical evaluation.

**The prototype must not be used for real patient care.**

---

## Future Roadmap

MedThread AI is under active development.

Planned improvements include:

- [ ] Evidence-first clinical extraction
- [ ] Independent semantic verification of generated claims
- [ ] Detection of omitted clinically relevant facts
- [ ] Improved reasoning across multiple source documents
- [ ] Better detection and presentation of conflicting records
- [ ] Evaluation against reference discharge summaries
- [ ] Expanded synthetic EHR test datasets
- [ ] Improved clinical review experience
- [ ] Exploration of HL7 FHIR-based data interoperability

The longer-term goal is to explore a more reliable and explainable approach to AI-assisted clinical handoff preparation.

---

## Disclaimer

**MedThread AI is an educational and research demonstration prototype.**

It is not a medical device, has not undergone clinical validation, and is not approved for patient care.

Do not upload protected health information (PHI), identifiable patient records, or confidential clinical data.

All generated outputs require qualified clinician review.

---

## Project Status

**Prototype — Active Development**

This repository documents an evolving exploration of Generative AI, clinical information extraction, evidence traceability, and healthcare data workflows.

Future iterations will focus on improving reliability, evaluation, and clinical-document reasoning.
