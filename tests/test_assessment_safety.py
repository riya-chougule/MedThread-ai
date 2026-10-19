
from types import SimpleNamespace

from medthread.assessment_safety import check_assessment_safety



def make_handoff(
    medication_status="unclear",
    pending_status="unclear",
):
    return SimpleNamespace(
        medication_changes_assessment=SimpleNamespace(
            status=medication_status
        ),
        pending_tests_assessment=SimpleNamespace(
            status=pending_status
        ),
        medication_changes=[],
    )

def test_incomplete_medication_reconciliation_is_flagged():
    records = """
## Document 1: Discharge Notes, row 1

Document ID: TEST-DISCHARGE-1

Medication Reconciliation:
Reconcile home and inpatient medications; document final medication list
"""

    handoff = make_handoff(
        medication_status="none_documented"
    )

    warnings = check_assessment_safety(handoff, records)

    assert any(
        "Medication assessment conflict" in warning
        for warning in warnings
    )


def test_uncertain_pending_results_are_flagged():
    records = """
## Document 1: Discharge Notes, row 1

Document ID: TEST-DISCHARGE-1

Pending Results:
Verify any outstanding test results before finalizing discharge
"""

    handoff = make_handoff(
        pending_status="none_documented"
    )

    warnings = check_assessment_safety(handoff, records)

    assert any(
        "Pending-test assessment conflict" in warning
        for warning in warnings
    )


def test_unclear_assessments_do_not_trigger_false_conflict():
    records = """
## Document 1: Discharge Notes, row 1

Document ID: TEST-DISCHARGE-1

Medication Reconciliation:
Reconcile home and inpatient medications; document final medication list

Pending Results:
Verify any outstanding test results before finalizing discharge
"""

    handoff = make_handoff()

    warnings = check_assessment_safety(handoff, records)

    assert warnings == []


def test_inpatient_discontinued_order_is_not_discharge_change():
    records = """
## Document 1: Medications, row 6

Document ID: EHR-MEDICATIONS-ROW-6

Medication Name:
Aspirin

Medication Status:
Discontinued
"""

    handoff = make_handoff(
        medication_status="documented"
    )

    handoff.medication_changes = [
        SimpleNamespace(
            content="Aspirin discontinued at discharge",
            sources=[
                SimpleNamespace(
                    document_name="EHR-MEDICATIONS-ROW-6",
                    section="Medication Status",
                    quoted_text="Discontinued",
                )
            ],
        )
    ]

    warnings = check_assessment_safety(
        handoff,
        records,
    )

    assert any(
        "medication-order records" in warning
        for warning in warnings
    )


def test_documented_status_without_changes_is_flagged():
    records = """
## Document 1: Discharge Notes, row 3

Document ID: EHR-DISCHARGE-NOTES-ROW-3

Medication Reconciliation:
Reconcile home and inpatient medications; document final medication list
"""

    handoff = make_handoff(
        medication_status="documented"
    )

    handoff.medication_changes = []

    warnings = check_assessment_safety(
        handoff,
        records,
    )

    assert any(
        "no discharge medication changes" in warning
        for warning in warnings
    )
