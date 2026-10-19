
from medthread.assessment_normalizer import (
    quarantine_order_only_medication_changes,
)
from medthread.schemas import (
    DischargeHandoff,
    DocumentedFact,
    SectionAssessment,
    SourceReference,
)


def test_order_only_medication_change_is_quarantined():
    handoff = DischargeHandoff(
        medication_changes=[
            DocumentedFact(
                content="Aspirin discontinued at discharge",
                sources=[
                    SourceReference(
                        document_name="EHR-MEDICATIONS-ROW-6",
                        section="Medication Name",
                        quoted_text="Aspirin",
                    )
                ],
            )
        ],
        medication_changes_assessment=SectionAssessment(
            status="documented",
            explanation="Aspirin was stopped at discharge.",
        ),
        pending_tests_assessment=SectionAssessment(
            status="unclear",
            explanation="Pending results need verification.",
        ),
    )

    warnings = quarantine_order_only_medication_changes(
        handoff
    )

    assert handoff.medication_changes == []
    assert (
        handoff.medication_changes_assessment.status
        == "unclear"
    )
    assert len(warnings) == 1
