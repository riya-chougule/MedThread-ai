
from medthread.schemas import (
    DischargeHandoff,
    MissingInformation,
)
from medthread.validation import _parse_document_sections



def add_missing_information(
    handoff: DischargeHandoff,
    field_name: str,
    reason: str,
) -> None:
    """Add a review flag without creating duplicates."""

    existing_fields = {
        item.field_name.strip().lower()
        for item in handoff.missing_information
    }

    if field_name.strip().lower() not in existing_fields:
        handoff.missing_information.append(
            MissingInformation(
                field_name=field_name,
                reason=reason,
            )
        )


def normalize_uncertain_assessments(
    handoff: DischargeHandoff,
    records: str,
) -> list[str]:
    """

Conservatively downgrade unsupported certainty.

Adds missing-information review flags and clears citations
when assessment explanations are replaced.

Does not create confirmed clinical facts.
Returns a list of adjustments for audit.

    """

    changes = []
    documents = _parse_document_sections(records)

    sections = [
        (name.lower(), content.lower())
        for doc in documents.values()
        for name, content in doc.items()
    ]

    medication_uncertainty = any(
        phrase in content
        for _, content in sections
        for phrase in (
            "reconcile home and inpatient medications",
            "document final medication list",
            "confirm which chronic medications",
        )
    )

    pending_uncertainty = any(
        phrase in content
        for _, content in sections
        for phrase in (
            "verify any outstanding test results",
            "final result not documented",
            "check outstanding results",
        )
    )

   
    if medication_uncertainty:
        assessment = handoff.medication_changes_assessment

        if assessment.status in (
            "none_documented",
            "documented",
        ):
            previous_status = assessment.status

            assessment.status = "unclear"
            assessment.explanation = (
                "The supplied records indicate that final "
                "medication reconciliation requires review. "
                "Discharge medication changes cannot be "
                "confirmed from these records alone."
            )
            assessment.sources = []

            changes.append(
                "Medication assessment changed from "
                f"'{previous_status}' to 'unclear' because "
                "final reconciliation is unresolved."
            )


    if (
        pending_uncertainty
        and handoff.pending_tests_assessment.status
        == "none_documented"
    ):
        assessment = handoff.pending_tests_assessment
        assessment.status = "unclear"
        assessment.explanation = (
            "The records request verification of outstanding "
            "results; final pending-test status is unclear."
        )
        assessment.sources = []
        changes.append(
            "Pending-test assessment downgraded to unclear "
            "because result verification is requested."
        )


    if medication_uncertainty:
        add_missing_information(
            handoff,
            field_name="Final medication reconciliation",
            reason=(
                "Confirm the final discharge medication list, "
                "including which medications should be "
                "continued, started, changed, or stopped."
            ),
        )

    if pending_uncertainty:
        add_missing_information(
            handoff,
            field_name="Pending-test verification",
            reason=(
                "Verify whether any test results remain "
                "outstanding before finalizing the handoff."
            ),
        )


    return changes


def quarantine_order_only_medication_changes(
    handoff: DischargeHandoff,
) -> list[str]:
    """
    Remove medication-change claims supported exclusively by
    inpatient medication-order records.

    Conservative prototype safeguard; not a full medication
    reconciliation validator.
    """

    retained = []
    quarantined = []

    for fact in handoff.medication_changes:
        if fact.sources and all(
            source.document_name.startswith(
                "EHR-MEDICATIONS-ROW-"
            )
            for source in fact.sources
        ):
            quarantined.append(fact)
        else:
            retained.append(fact)

    if not quarantined:
        return []

    handoff.medication_changes = retained

    assessment = handoff.medication_changes_assessment
    assessment.status = "unclear"
    assessment.explanation = (
        "Medication-order records do not independently "
        "establish the final discharge medication plan. "
        "Medication reconciliation requires review."
    )
    assessment.sources = []

    return [
        f"Safety quarantine: {len(quarantined)} "
        "medication-change claim(s) were excluded from "
        "the handoff because they were supported only "
        "by medication-order records."
    ]
