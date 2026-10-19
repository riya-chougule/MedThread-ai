from medthread.validation import (
    validate_section_assessments,
    validate_sources,enforce_pending_tests_uncertainty
)

from medthread.schemas import (
    DischargeHandoff,
    DocumentedFact,
    MissingInformation,
    SectionAssessment,
    SourceReference,
)


def make_handoff(**kwargs):
    """Create a handoff with default assessments that can be overridden."""
    kwargs.setdefault(
        "pending_tests_assessment",
        SectionAssessment(
            status="unclear",
            explanation="Pending-test status has not been established.",
        ),
    )
    kwargs.setdefault(
        "medication_changes_assessment",
        SectionAssessment(
            status="unclear",
            explanation="Medication-change status has not been established.",
        ),
    )
    return DischargeHandoff(**kwargs)

def test_handoff_requires_clinician_review():
    handoff = make_handoff()

    assert handoff.requires_clinician_review is True
    assert handoff.missing_information == []


def test_documented_fact_preserves_source():
    source = SourceReference(
        document_name="fictional_discharge_note.txt",
        section="Hospital Course",
        quoted_text="Patient improved with treatment.",
    )

    fact = DocumentedFact(
        content="The patient's condition improved.",
        sources=[source],
    )

    assert len(fact.sources) == 1
    assert fact.sources[0].section == "Hospital Course"


def test_missing_information_is_flagged():
    missing = MissingInformation(
        field_name="discharge medication instructions",
        reason="The provided records do not specify whether the medication should continue.",
    )

    assert missing.status == "needs_review"


def test_valid_source_passes_validation():
    records = (
    "## Document 1: Admission Note\n"
    "Document ID: ADMISSION-001\n\n"
    "Reason for Admission:\n"
    "The patient presented with fever and cough.\n"
)


    handoff = make_handoff(
        admission_reason=DocumentedFact(
            content="The patient presented with fever and cough.",
            sources=[
                SourceReference(
                    document_name="ADMISSION-001",
                    section="Reason for Admission",
                    quoted_text=(
                        "The patient presented with fever and cough."
                    ),
                )
            ],
        )
    )

    assert validate_sources(handoff, records) == []


def test_invented_quotation_fails_validation():
    records = (
    "## Document 1: Admission Note\n"
    "Document ID: ADMISSION-001\n\n"
    "Reason for Admission:\n"
    "The patient presented with fever and cough.\n"
)


    handoff = make_handoff(
        admission_reason=DocumentedFact(
            content="The patient was discharged with antibiotics.",
            sources=[
                SourceReference(
                    document_name="ADMISSION-001",
                    section="Reason for Admission",
                    quoted_text=(
                        "The patient was discharged with antibiotics."
                    ),
                )
            ],
        )
    )

    errors = validate_sources(handoff, records)

    assert any("quotation does not appear verbatim" in e for e in errors)


def test_fact_without_sources_fails_validation():
    records = (
    "## Document 1: Admission Note\n"
    "Document ID: ADMISSION-001\n\n"
    "Reason for Admission:\n"
    "The patient presented with fever and cough.\n"
)


    handoff = make_handoff(
        admission_reason=DocumentedFact(
            content="The patient presented with fever and cough.",
            sources=[],
        )
    )

    errors = validate_sources(handoff, records)

    assert any("no source references provided" in e for e in errors)


def test_section_assessment_requires_explicit_status():
    from medthread.schemas import SectionAssessment

    assessment = SectionAssessment(
        status="unclear",
        explanation=(
            "The discharge note does not establish whether "
            "any tests remain pending."
        ),
    )

    assert assessment.status == "unclear"
    assert assessment.sources == []


def test_no_pending_tests_mentioned_is_not_proof_none_exist():
    records = (
    "## Document 1: Discharge Note\n"
    "Document ID: DISCHARGE-003\n\n"
    "Pending Tests:\n"
    "No pending tests were mentioned in this document.\n"
)


    handoff = make_handoff(
        pending_tests_assessment=SectionAssessment(
            status="unclear",
            explanation=(
                "The document does not establish whether "
                "any tests remain pending."
            ),
            sources=[
                SourceReference(
                    document_name="DISCHARGE-003",
                    section="Pending Tests",
                    quoted_text=(
                        "No pending tests were mentioned in this document."
                    ),
                )
            ],
        )
    )

    assert handoff.pending_tests_assessment.status == "unclear"


def test_ambiguous_pending_tests_assessment_fails_validation():
    handoff = make_handoff(
        pending_tests_assessment=SectionAssessment(
            status="none_documented",
            explanation="No pending tests were mentioned in this document.",
        )
    )

    errors = validate_section_assessments(handoff)

    assert any("does not establish" in error for error in errors)


def test_unclear_pending_tests_assessment_passes_validation():
    handoff = make_handoff(
        pending_tests_assessment=SectionAssessment(
            status="unclear",
            explanation=(
                "The records do not establish whether "
                "any tests remain pending."
            ),
        )
    )

    errors = validate_section_assessments(handoff)

    assert errors == []


def test_invented_assessment_quotation_fails_validation():
    records = (
    "## Document 1: Discharge Note\n"
    "Document ID: DISCHARGE-003\n\n"
    "Pending Tests:\n"
    "No pending tests were mentioned in this document.\n"
)


    handoff = make_handoff(
        pending_tests_assessment=SectionAssessment(
            status="unclear",
            explanation="Pending-test status has not been established.",
            sources=[
                SourceReference(
                    document_name="DISCHARGE-003",
                    section="Pending Tests",
                    quoted_text="All laboratory results were normal.",
                )
            ],
        )
    )

    errors = validate_sources(handoff, records)

    assert any(
        "pending_tests_assessment.sources[0]" in error
        and "quotation does not appear verbatim" in error
        for error in errors
    )


def test_quotation_from_wrong_section_fails_validation():
    records = (
        "## Document 1: Discharge Note\n"
        "Document ID: DISCHARGE-003\n\n"
        "Pending Tests:\n"
        "No pending tests were mentioned in this document.\n\n"
        "Follow-Up:\n"
        "Follow up with the primary care provider within seven days.\n"
    )

    handoff = make_handoff(
        pending_tests_assessment=SectionAssessment(
            status="unclear",
            explanation="Pending-test status has not been established.",
            sources=[
                SourceReference(
                    document_name="DISCHARGE-003",
                    section="Pending Tests",
                    quoted_text=(
                        "Follow up with the primary care provider within seven days."
                    ),
                )
            ],
        )
    )

    errors = validate_sources(handoff, records)

    assert any(
        "quotation does not appear verbatim in the cited section"
        in error
        for error in errors
    )


def test_unsafe_pending_tests_status_is_corrected():
    handoff = make_handoff(
        pending_tests_assessment=SectionAssessment(
            status="none_documented",
            explanation=(
                "No tests are pending as explicitly stated "
                "in the discharge note."
            ),
            sources=[
                SourceReference(
                    document_name="DISCHARGE-003",
                    section="Pending Tests",
                    quoted_text=(
                        "No pending tests were mentioned in this document."
                    ),
                )
            ],
        )
    )

    warnings = enforce_pending_tests_uncertainty(handoff)

    assert handoff.pending_tests_assessment.status == "unclear"
    assert "does not establish" in (
        handoff.pending_tests_assessment.explanation
    )
    assert any("Safety override" in warning for warning in warnings)
