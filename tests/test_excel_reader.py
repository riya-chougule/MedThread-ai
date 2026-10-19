
from io import BytesIO

from openpyxl import Workbook

from medthread.excel_reader import (
    excel_to_record_text,
    get_patient_ids,
)


def create_test_workbook() -> bytes:
    workbook = Workbook()

    patients = workbook.active
    patients.title = "Patients"
    patients.append(["Patient ID", "Admission Reason"])
    patients.append(["SYN-1001", "Fictional pneumonia case"])
    patients.append(["SYN-1002", "Fictional dehydration case"])

    course = workbook.create_sheet("Hospital Course")
    course.append(["Patient ID", "Hospital Course"])
    course.append(["SYN-1001", "Received fictional treatment A"])
    course.append(["SYN-1002", "Received fictional treatment B"])

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()

    return buffer.getvalue()


def test_get_patient_ids_returns_unique_ids():
    workbook_bytes = create_test_workbook()

    patient_ids = get_patient_ids(workbook_bytes)

    assert patient_ids == ["SYN-1001", "SYN-1002"]


def test_excel_reader_includes_only_selected_patient():
    workbook_bytes = create_test_workbook()

    records = excel_to_record_text(
        workbook_bytes,
        "SYN-1001",
    )

    assert "SYN-1001" in records
    assert "Fictional pneumonia case" in records
    assert "Received fictional treatment A" in records

    assert "SYN-1002" not in records
    assert "Fictional dehydration case" not in records
    assert "Received fictional treatment B" not in records


def test_excel_reader_rejects_unknown_patient():
    workbook_bytes = create_test_workbook()

    try:
        excel_to_record_text(workbook_bytes, "SYN-9999")
    except ValueError as exc:
        assert "No records found" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown patient")
