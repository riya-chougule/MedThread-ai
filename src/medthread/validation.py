
import re

from medthread.schemas import DischargeHandoff, DocumentedFact


def _parse_document_sections(records: str) -> dict[str, dict[str, str]]:
    """Parse synthetic records into document IDs and named sections."""
    documents: dict[str, dict[str, str]] = {}

    chunks = re.split(
        r"(?m)^## Document \d+:\s*.*$",
        records,
    )

    section_pattern = re.compile(
        r"(?m)^([A-Za-z][A-Za-z -]*):[ \t]*$"
    )

    for chunk in chunks:
        id_match = re.search(
            r"(?m)^Document ID:\s*(\S+)\s*$",
            chunk,
        )
        if not id_match:
            continue

        document_id = id_match.group(1)
        sections: dict[str, str] = {}
        matches = list(section_pattern.finditer(chunk))

        for index, match in enumerate(matches):
            section_name = match.group(1).strip()
            start = match.end()
            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(chunk)
            )
            sections[section_name] = chunk[start:end].strip()

        documents[document_id] = sections

    return documents


def validate_sources(
    handoff: DischargeHandoff,
    records: str,
) -> list[str]:
    """
    Check that citations refer to the specified document and section
    and that quotations occur verbatim within that section.

    Passing these checks does not prove entailment or clinical accuracy.
    """
    errors: list[str] = []
    documents = _parse_document_sections(records)

    facts: list[tuple[str, DocumentedFact]] = []

    if handoff.admission_reason is not None:
        facts.append(("admission_reason", handoff.admission_reason))

    if handoff.hospital_course is not None:
        facts.append(("hospital_course", handoff.hospital_course))

    for field_name in (
        "discharge_diagnoses",
        "medication_changes",
        "pending_tests",
        "follow_up_instructions",
    ):
        for index, fact in enumerate(getattr(handoff, field_name)):
            facts.append((f"{field_name}[{index}]", fact))

    assessments = [
        ("pending_tests_assessment", handoff.pending_tests_assessment),
        (
            "medication_changes_assessment",
            handoff.medication_changes_assessment,
        ),
    ]

    for fact_name, fact in facts:
        if not fact.sources:
            errors.append(f"{fact_name}: no source references provided.")

        for index, source in enumerate(fact.sources):
            prefix = f"{fact_name}.sources[{index}]"
            _validate_one_source(
                source, prefix, documents, errors
            )

    for assessment_name, assessment in assessments:
        for index, source in enumerate(assessment.sources):
            prefix = f"{assessment_name}.sources[{index}]"
            _validate_one_source(
                source, prefix, documents, errors
            )

    return errors


def _validate_one_source(
    source,
    prefix: str,
    documents: dict[str, dict[str, str]],
    errors: list[str],
) -> None:
    """Validate a citation against its specific document and section."""
    if source.document_name not in documents:
        errors.append(
            f"{prefix}: document ID not found: "
            f"{source.document_name!r}"
        )
        return

    sections = documents[source.document_name]

    if source.section not in sections:
        errors.append(
            f"{prefix}: section {source.section!r} not found in "
            f"document {source.document_name!r}."
        )
        return

    section_text = sections[source.section]

    if not source.quoted_text.strip():
        errors.append(f"{prefix}: quoted text is empty.")
    elif source.quoted_text not in section_text:
        errors.append(
            f"{prefix}: quotation does not appear verbatim in "
            f"the cited section."
        )




def validate_section_assessments(
    handoff: DischargeHandoff,
) -> list[str]:
    """
    Flag unsupported conclusions about pending tests.

    This targeted rule is not a complete semantic or clinical validator.
    """
    errors: list[str] = []
    assessment = handoff.pending_tests_assessment

    if assessment.status != "none_documented":
        return errors

    absence_of_mention_phrases = (
        "no pending tests were mentioned",
        "not mentioned",
        "wasn't mentioned",
        "were not mentioned",
        "not documented",
        "was not documented",
        "were not documented",
        "not specified",
        "was not specified",
        "were not specified",
        "not found",
        "was not found",
        "were not found",
    )

    cited_quotes = " ".join(
        source.quoted_text.lower()
        for source in assessment.sources
    )

    explanation = assessment.explanation.lower()

    quote_only_reports_absence = any(
        phrase in cited_quotes
        for phrase in absence_of_mention_phrases
    )

    if (
        quote_only_reports_absence
        or "mentioned in this document" in explanation
    ):
        errors.append(
            "pending_tests_assessment: the cited evidence only "
            "indicates that pending tests were not mentioned, "
            "documented, specified, or found. It does not establish "
            "that no tests are pending. Change the assessment to "
            "'unclear' unless the records explicitly establish "
            "that no tests remain pending."
        )

    return errors



def enforce_pending_tests_uncertainty(
    handoff: DischargeHandoff,
) -> list[str]:
    """
    Correct a known unsafe classification when the cited evidence
    only says pending tests were not mentioned.

    This is a narrow safety rule, not a general clinical validator.
    """
    assessment = handoff.pending_tests_assessment

    if assessment.status != "none_documented":
        return []

    absence_of_mention_phrases = (
        "no pending tests were mentioned",
        "no pending tests were documented",
        "no pending tests were specified",
        "no pending tests were found",
        "not mentioned",
        "not documented",
        "not specified",
    )

    cited_quotes = " ".join(
        source.quoted_text.lower()
        for source in assessment.sources
    )

    if any(
        phrase in cited_quotes
        for phrase in absence_of_mention_phrases
    ):
        assessment.status = "unclear"
        assessment.explanation = (
            "The cited record says pending tests were not mentioned. "
            "It does not establish whether any tests remain pending; "
            "clarification is needed."
        )

        return [
            "Safety override: pending-test status was changed from "
            "'none_documented' to 'unclear' because the cited evidence "
            "does not establish that no tests are pending."
        ]

    return []
