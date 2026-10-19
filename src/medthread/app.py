import base64
import json
from pathlib import Path

import streamlit as st

from medthread.ehr_reader import encounter_to_record_text, get_encounters
from medthread.pipeline import run_pipeline


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(page_title="MedThread AI", page_icon="🩺", layout="wide")

st.markdown("""
<style>
  .block-container {max-width: 1080px; padding-top: 1.5rem; padding-bottom: 3rem;}
  h1, h2, h3 {letter-spacing: -.025em;}
  h3 {padding-top: .45rem;}
  [data-testid="stExpander"] {border-radius: 12px;}
  [data-testid="stFileUploader"] {border-radius: 12px;}
  [data-testid="stSidebar"] {border-right: 1px solid rgba(110,150,170,.15);}
  .mt-hero-banner {
      width: 100%;
      min-height: 300px;
      border-radius: 18px;
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      overflow: hidden;
      display: flex;
      align-items: stretch;
      margin-bottom: 1.5rem;
      box-shadow: 0 8px 28px rgba(0, 0, 0, .12);
  }
  .mt-hero-overlay {
      width: 100%;
      min-height: 300px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 2.5rem 3rem;
      background: linear-gradient(90deg,
          rgba(8, 31, 56, .96) 0%,
          rgba(8, 45, 72, .83) 42%,
          rgba(8, 45, 72, .12) 100%);
  }
  .mt-hero-title {
      font-size: clamp(2.2rem, 4vw, 3.7rem);
      font-weight: 800;
      color: #fff;
      line-height: 1.1;
      letter-spacing: -.04em;
      margin-bottom: .8rem;
  }
  .mt-hero-description {
      font-size: 1.1rem;
      color: #dbeafe;
      max-width: 480px;
      line-height: 1.6;
  }
  .mt-hero-tag {
      color: #7dd3fc;
      font-size: .8rem;
      font-weight: 700;
      letter-spacing: .14em;
      margin-bottom: 1rem;
  }
  @media (max-width: 650px) {
      .mt-hero-banner, .mt-hero-overlay {min-height: 245px;}
      .mt-hero-overlay {
          padding: 1.5rem;
          background: rgba(8, 31, 56, .82);
      }
      .mt-hero-description {font-size: .9rem;}
  }
</style>
""", unsafe_allow_html=True)


def render_sources(sources, label="View supporting evidence"):
    """Keep evidence available without overpowering the clinical summary."""
    if not sources:
        st.caption("No source reference was provided for this item.")
        return

    source_names = list(dict.fromkeys(
        str(source.get("document_name") or "Unknown document")
        for source in sources
    ))
    st.caption("Sources: " + ", ".join(source_names))

    with st.expander(f"{label} ({len(sources)})", expanded=False):
        for index, source in enumerate(sources, start=1):
            st.caption(
                f"Source {index} · "
                f"{source.get('document_name') or 'Unknown document'} · "
                f"{source.get('section') or 'Unknown section'}"
            )
            st.caption(
                f"Quotation: {source.get('quoted_text') or 'No quotation provided.'}"
            )


def render_fact(fact, *, bullet=False):
    """Display the clinical statement first and its evidence in smaller text."""
    if not isinstance(fact, dict):
        return
    content = fact.get("content") or "Not documented."
    st.markdown(f"- {content}" if bullet else content)
    render_sources(fact.get("sources") or [])


def render_assessment(assessment):
    """Display uncertainty as part of the report, with optional evidence."""
    assessment = assessment or {}
    status = str(assessment.get("status") or "unknown").replace("_", " ")
    st.caption(f"Documentation status: {status.upper()}")
    if assessment.get("explanation"):
        st.write(assessment["explanation"])
    render_sources(assessment.get("sources") or [], label="View assessment evidence") if assessment.get("sources") else None


# ---------------------------------------------------------
# Full-width image banner and sidebar
# ---------------------------------------------------------
illustration_path = Path(__file__).with_name("hospital_illustration.png")

if illustration_path.is_file():
    image_base64 = base64.b64encode(illustration_path.read_bytes()).decode("ascii")
    st.markdown(
        f"""
        <div class="mt-hero-banner"
             style="background-image: url('data:image/png;base64,{image_base64}');">
            <div class="mt-hero-overlay">
                <div class="mt-hero-tag">HEALTHCARE · EVIDENCE-LINKED AI</div>
                <div class="mt-hero-title">MedThread AI</div>
                <div class="mt-hero-description">
                    Intelligent discharge handoffs. Clear clinical summaries.
                    Traceable evidence.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.title("🩺 MedThread AI")
    st.subheader("Evidence-Linked Discharge Handoff Assistant")

st.markdown(
    """
    Upload hospital documentation to generate a structured discharge handoff
    draft with traceable evidence, citation checks, and missing-information flags.

    All generated handoffs require clinician review.
    """
)

with st.sidebar:
    st.header("About MedThread AI")
    st.write(
        "MedThread AI extracts documented hospital-stay information, "
        "preserves source references, and highlights uncertain or missing details."
    )
    st.header("Choose input")
    input_mode = st.radio(
        "Record source", ["Upload a text file", "Upload an Excel file"]
    )


# ---------------------------------------------------------
# Input handling
# ---------------------------------------------------------
records = ""
input_label = ""

if input_mode == "Upload a text file":
    st.subheader("Upload hospital documentation")
    uploaded_file = st.file_uploader(
        "Choose a text file (.txt or .md)",
        type=["txt", "md"],
        key="text_upload",
    )
    st.caption(
        "Upload a document containing one hospitalization. For source-reference "
        "validation, use labeled document IDs and section headings."
    )
    if uploaded_file is not None:
        records = uploaded_file.getvalue().decode("utf-8", errors="replace")
        input_label = uploaded_file.name
        if records.strip():
            st.success(f"Loaded text document: {uploaded_file.name}")
        else:
            records = ""
            st.error("The uploaded text file is empty.")

else:
    st.subheader("Upload hospital EHR workbook")
    uploaded_file = st.file_uploader(
        "Choose an Excel workbook (.xlsx)",
        type=["xlsx"],
        key="excel_upload",
    )
    st.caption(
        "Expected format: an Encounters sheet with Patient ID and Encounter ID "
        "columns, plus optional clinical sheets containing the same identifiers."
    )
    if uploaded_file is not None:
        try:
            workbook_bytes = uploaded_file.getvalue()
            encounters = get_encounters(workbook_bytes)
            if not encounters:
                st.error("No patient encounters were found in the uploaded workbook.")
            else:
                patient_ids = sorted({item["patient_id"] for item in encounters})
                patient_id = st.selectbox(
                    "Select patient", patient_ids, key="selected_patient"
                )
                encounter_ids = sorted({
                    item["encounter_id"]
                    for item in encounters
                    if item["patient_id"] == patient_id
                })
                encounter_id = st.selectbox(
                    "Select hospitalization (Encounter ID)",
                    encounter_ids,
                    key="selected_encounter",
                )
                records = encounter_to_record_text(
                    workbook_bytes, patient_id, encounter_id
                )
                input_label = f"{uploaded_file.name} | {patient_id} | {encounter_id}"
                document_count = sum(
                    line.startswith("## Document ") for line in records.splitlines()
                )
                st.success(
                    f"Loaded {document_count} source documents for patient "
                    f"{patient_id}, encounter {encounter_id}."
                )
                if document_count == 1:
                    st.warning(
                        "Only one source document was found. Check whether the "
                        "workbook includes clinical documentation for this encounter."
                    )
        except Exception:
            records = ""
            st.error("Unable to read this workbook as an encounter-based EHR file.")
            st.info(
                "Check that the workbook contains an 'Encounters' sheet and "
                "valid patient and encounter identifiers."
            )
            # Do not expose exception text; it could include uploaded record data.


# ---------------------------------------------------------
# Clear previous results when the input changes
# ---------------------------------------------------------
input_signature = (input_mode, input_label, records)
if input_signature != st.session_state.get("current_input_signature"):
    for key in (
        "handoff_json", "validation_errors", "safety_warnings", "citation_repairs"
    ):
        st.session_state.pop(key, None)
    st.session_state["current_input_signature"] = input_signature


# ---------------------------------------------------------
# Generate handoff
# ---------------------------------------------------------
if records:
    with st.expander("Preview source records", expanded=False):
        st.markdown(records)

    if st.button("Generate discharge handoff", type="primary"):
        try:
            with st.spinner(
                "Extracting clinical information and validating source references..."
            ):
                result = run_pipeline(records)
            st.session_state["handoff_json"] = result.handoff.model_dump()
            st.session_state["validation_errors"] = result.validation_errors
            st.session_state["safety_warnings"] = result.safety_warnings
            st.session_state["citation_repairs"] = result.citation_repairs
        except Exception:
            st.error(
                "The handoff could not be generated. Check the API "
                "configuration and application logs."
            )


# ---------------------------------------------------------
# Display readable clinical report
# ---------------------------------------------------------
if "handoff_json" in st.session_state:
    data = st.session_state["handoff_json"]
    validation_errors = st.session_state.get("validation_errors", [])
    safety_warnings = st.session_state.get("safety_warnings", [])
    citation_repairs = st.session_state.get("citation_repairs", [])

    st.divider()
    st.header("Clinical handoff summary")
    st.caption(f"Patient identifier: {data.get('patient_identifier') or 'Not documented'}")

    if validation_errors:
        st.error(
            "This draft contains unresolved validation issues. "
            "Review the technical details before relying on the references."
        )
    else:
        st.success("Automated source-reference checks passed.")

    with st.expander("Technical validation details", expanded=False):
        if validation_errors:
            st.markdown("**Validation issues**")
            for error in validation_errors:
                st.write(f"- {error}")
        if safety_warnings:
            st.markdown("**Safety adjustments**")
            for warning in safety_warnings:
                st.write(f"- {warning}")
        if citation_repairs:
            st.markdown("**Citation formatting corrections**")
            for repair in citation_repairs:
                st.write(f"- {repair}")
        if not (validation_errors or safety_warnings or citation_repairs):
            st.write("No technical issues reported.")

    st.caption(
        "AI-generated draft · Clinician review required · "
        "Source matching does not establish clinical accuracy or completeness."
    )

    st.markdown("### Reason for admission")
    if data.get("admission_reason"):
        render_fact(data["admission_reason"])
    else:
        st.write("Not documented in the extracted handoff.")

    st.divider()
    st.markdown("### Hospital course")
    if data.get("hospital_course"):
        render_fact(data["hospital_course"])
    else:
        st.write("Not documented in the extracted handoff.")

    st.divider()
    st.markdown("### Discharge diagnoses")
    diagnoses = data.get("discharge_diagnoses") or []
    if diagnoses:
        for fact in diagnoses:
            # Keep the coded diagnosis distinct from clinical context.
            # The context comes from the separately sourced hospital course;
            # it is not a new diagnosis or an inferred diagnosis explanation.
            st.markdown(f"**{fact.get('content') or 'Diagnosis not specified'}**")
            render_sources(fact.get("sources") or [])
            if len(diagnoses) == 1 and data.get("hospital_course"):
                st.markdown("**Documented clinical context**")
                st.write(data["hospital_course"].get("content") or "Not documented.")
                st.caption("Context from the hospital course; not an additional diagnosis.")
                render_sources(data["hospital_course"].get("sources") or [],
                               label="View clinical-context evidence")
    else:
        st.write("No discharge diagnoses extracted.")

    st.divider()
    st.markdown("### Medication changes")
    render_assessment(data.get("medication_changes_assessment"))
    medication_changes = data.get("medication_changes") or []
    if medication_changes:
        for fact in medication_changes:
            render_fact(fact, bullet=True)
    else:
        st.caption("No confirmed discharge medication changes extracted.")

    st.divider()
    st.markdown("### Pending tests")
    render_assessment(data.get("pending_tests_assessment"))
    pending_tests = data.get("pending_tests") or []
    if pending_tests:
        for fact in pending_tests:
            render_fact(fact, bullet=True)
    else:
        st.caption(
            "No specific pending-test items were extracted. "
            "This does not confirm that all results are finalized."
        )

    st.divider()
    st.markdown("### Follow-up instructions")
    follow_ups = data.get("follow_up_instructions") or []
    if follow_ups:
        for fact in follow_ups:
            render_fact(fact, bullet=True)
    else:
        st.write("No follow-up instructions extracted.")

    st.divider()
    st.markdown("### Items requiring review")
    missing_items = data.get("missing_information") or []
    if missing_items:
        for item in missing_items:
            st.markdown(f"**{item.get('field_name') or 'Unspecified item'}**")
            st.write(item.get("reason") or "Review required.")
    else:
        st.caption(
            "No missing-information flags were returned. "
            "This does not establish clinical completeness."
        )

    st.divider()
    st.download_button(
        label="Download structured handoff (JSON)",
        data=json.dumps(data, indent=2, ensure_ascii=False),
        file_name="medthread_discharge_handoff.json",
        mime="application/json",
    )
