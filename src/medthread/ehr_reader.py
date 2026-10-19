
from io import BytesIO
from datetime import date, datetime
import re

from openpyxl import load_workbook


def normalize_patient_id(value) -> str:
    """Convert Excel numeric IDs and text IDs to six-digit strings."""
    if value is None or str(value).strip() == "":
        return ""

    text = str(value).strip()

    if re.fullmatch(r"\d+(?:\.0+)?", text):
        return f"{int(text.split('.')[0]):06d}"

    return text


def normalize_encounter_id(value) -> str:
    """Preserve encounter identifiers as strings."""
    if value is None:
        return ""

    return str(value).strip()


def get_encounters(file_bytes: bytes) -> list[dict]:
    """Read patient-encounter pairs from the Encounters sheet."""
    workbook = load_workbook(
        BytesIO(file_bytes),
        read_only=True,
        data_only=True,
    )

    try:
        if "Encounters" not in workbook.sheetnames:
            raise ValueError(
                "Workbook must contain an 'Encounters' sheet."
            )

        worksheet = workbook["Encounters"]
        rows = worksheet.iter_rows(values_only=True)
        headers = next(rows, None)

        if not headers:
            raise ValueError("Encounters sheet is empty.")

        headers = [
            str(header).strip() if header is not None else ""
            for header in headers
        ]

        if "Patient ID" not in headers or "Encounter ID" not in headers:
            raise ValueError(
                "Encounters sheet must contain "
                "Patient ID and Encounter ID."
            )

        patient_index = headers.index("Patient ID")
        encounter_index = headers.index("Encounter ID")

        encounters = []
        seen = set()

        for row in rows:
            patient_id = normalize_patient_id(
                row[patient_index]
            )
            encounter_id = normalize_encounter_id(
                row[encounter_index]
            )

            if not patient_id or not encounter_id:
                continue

            key = (patient_id, encounter_id)

            if key in seen:
                raise ValueError(
                    f"Duplicate encounter found: {key}"
                )

            seen.add(key)

            encounters.append(
                {
                    "patient_id": patient_id,
                    "encounter_id": encounter_id,
                }
            )

        return encounters

    finally:
        workbook.close()


def encounter_to_record_text(
    file_bytes: bytes,
    patient_id: str,
    encounter_id: str,
) -> str:
    """
    Convert records for one selected patient encounter
    into source documents for MedThread AI.
    """
    selected_patient = normalize_patient_id(patient_id)
    selected_encounter = normalize_encounter_id(encounter_id)

    if not selected_patient or not selected_encounter:
        raise ValueError(
            "Patient ID and Encounter ID are required."
        )

    valid_encounters = {
        (item["patient_id"], item["encounter_id"])
        for item in get_encounters(file_bytes)
    }

    if (selected_patient, selected_encounter) not in valid_encounters:
        raise ValueError(
            f"Encounter {selected_encounter} "
            f"not found for patient {selected_patient}."
        )

    workbook = load_workbook(
        BytesIO(file_bytes),
        read_only=True,
        data_only=True,
    )

    documents = []

    try:
        for worksheet in workbook.worksheets:
            rows = worksheet.iter_rows(values_only=True)
            headers = next(rows, None)

            if not headers:
                continue

            headers = [
                str(header).strip() if header is not None else ""
                for header in headers
            ]

            if "Patient ID" not in headers or "Encounter ID" not in headers:
                raise ValueError(
                    f"Sheet '{worksheet.title}' must contain "
                    "Patient ID and Encounter ID."
                )

            patient_index = headers.index("Patient ID")
            encounter_index = headers.index("Encounter ID")

            sheet_slug = re.sub(
                r"[^A-Z0-9]+",
                "-",
                worksheet.title.upper(),
            ).strip("-")

            for row_number, row in enumerate(rows, start=2):
                row_patient = normalize_patient_id(
                    row[patient_index]
                )
                row_encounter = normalize_encounter_id(
                    row[encounter_index]
                )

                # Only retrieve records belonging to
                # the selected patient AND encounter.
                if (
                    row_patient != selected_patient
                    or row_encounter != selected_encounter
                ):
                    continue

                fields = []

                for header, value in zip(headers, row):

                    # Skip empty spreadsheet cells.
                    if value is None or str(value).strip() == "":
                        continue

                    # Avoid duplicate Document ID labels.
                    # The reader generates the authoritative source ID.
                    if header == "Document ID":
                        header = "Original Record ID"

                    # Normalize identifiers consistently.
                    if header == "Patient ID":
                        value = row_patient

                    elif header == "Encounter ID":
                        value = row_encounter

                    # Format Excel dates as readable strings.
                    elif isinstance(value, (date, datetime)):
                        value = value.isoformat()

                    # Put the section heading on its own line.
                    # This matches the format expected by validate_sources().
                    section_name = re.sub(r"[^A-Za-z -]", " ", header)
                    section_name = re.sub(r"\s+", " ", section_name).strip()

                    if not section_name or not section_name[0].isalpha():
                        section_name = "Field"

                    fields.append(f"{section_name}:\n{value}")

                # Create a unique, traceable source identifier.
                document_id = (
                    f"EHR-{sheet_slug}-ROW-{row_number}"
                )

                document = (
                    f"## Document {len(documents) + 1}: "
                    f"{worksheet.title}, row {row_number}\n\n"
                    f"Document ID: {document_id}\n\n"
                    + "\n\n".join(fields)
                )

                documents.append(document)

    finally:
        workbook.close()

    if not documents:
        raise ValueError(
            "No matching encounter records found."
        )

    return "\n\n".join(documents)
