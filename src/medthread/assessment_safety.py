
import re

from medthread.schemas import DischargeHandoff
from medthread.validation import _parse_document_sections


def check_assessment_safety(
    handoff: DischargeHandoff,
    records: str,
) -> list[str]:
    """
    Detect selected unsafe assessment conclusions.

    This is a conservative rule-based check, not a
    complete clinical or semantic validation system.
    """

    warnings = []
    documents = _parse_document_sections(records)

    all_sections = []

    for sections in documents.values():
        for section_name, content in sections.items():
            all_sections.append(
                (section_name.lower(), content.lower())
            )

    # --------------------------------------------------
    # Medication reconciliation checks
    # --------------------------------------------------

    medication_uncertainty_patterns = [
        r"\breconcile home and inpatient medications\b",
        r"\bdocument final medication list\b",
        r"\bconfirm which chronic medications\b",
        r"\bfinal medication reconciliation\b",
        r"\bmedication reconciliation is required\b",
        r"\bcontinuation orders not available\b",
        r"\bverify medication reconciliation\b",
    ]

    medication_uncertainty = any(
        re.search(pattern, content)
        for _, content in all_sections
        for pattern in medication_uncertainty_patterns
    )

    medication_status = (
        handoff.medication_changes_assessment.status
    )

    if (
        medication_uncertainty
        and medication_status == "none_documented"
    ):
        warnings.append(
            "Medication assessment conflict: the source "
            "records indicate unresolved medication "
            "reconciliation, but the generated assessment "
            "claims no medication changes were documented. "
            "The discharge medication plan needs review."
        )

    # --------------------------------------------------
    # Pending-test uncertainty checks
    # --------------------------------------------------

    pending_uncertainty_patterns = [
        r"\bverify any outstanding test results\b",
        r"\bfinal .* result not documented\b",
        r"\bconfirm .* pending results\b",
        r"\bcheck outstanding results\b",
        r"\bverify .* culture status\b",
    ]

    pending_uncertainty = any(
        re.search(pattern, content)
        for _, content in all_sections
        for pattern in pending_uncertainty_patterns
    )

    pending_status = handoff.pending_tests_assessment.status

    if (
        pending_uncertainty
        and pending_status == "none_documented"
    ):
        warnings.append(
            "Pending-test assessment conflict: the source "
            "records contain instructions to verify results "
            "or indicate unavailable final results, but "
            "the generated assessment claims no tests "
            "are pending. Verification is required."
        )


    # --------------------------------------------------
    # Discharge medication changes must not rely solely
    # on inpatient medication-order status.
    # --------------------------------------------------

    for index, fact in enumerate(handoff.medication_changes):

        sources = fact.sources

        if not sources:
            warnings.append(
                f"medication_changes[{index}]: "
                "No supporting citations were provided."
            )
            continue

        medication_order_sources = [
            source
            for source in sources
            if source.document_name.startswith(
                "EHR-MEDICATIONS-ROW-"
            )
        ]

        discharge_plan_sources = [
            source
            for source in sources
            if source not in medication_order_sources
        ]

        if (
            medication_order_sources
            and not discharge_plan_sources
        ):
            warnings.append(
                f"medication_changes[{index}]: "
                "Medication change is supported only by "
                "medication-order records. An inpatient "
                "order status does not establish a "
                "discharge medication change."
            )

    if (
        medication_uncertainty
        and medication_status == "documented"
        and not handoff.medication_changes
    ):
        warnings.append(
            "Medication assessment conflict: status is "
            "'documented', but no discharge medication "
            "changes were extracted."
        )


    return warnings
