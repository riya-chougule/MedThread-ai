
from pathlib import Path

from medthread.ehr_reader import (
    get_encounters,
    encounter_to_record_text,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXCEL_PATH = PROJECT_ROOT / "data" / "sample_records" / "synthetic_ehr.xlsx"


def main():
    file_bytes = EXCEL_PATH.read_bytes()

    encounters = get_encounters(file_bytes)
    print(f"\nTotal encounters: {len(encounters)}")

    patient_id = "000006"
    encounter_id = "2025-000006"

    print(f"\nSelected patient: {patient_id}")
    print(f"Selected encounter: {encounter_id}")

    record_text = encounter_to_record_text(
        file_bytes,
        patient_id,
        encounter_id,
    )

    print("\nDOCUMENTS FOUND:")
    print(record_text.count("## Document "))

    print("\nSOURCE DOCUMENT IDS:")
    for line in record_text.splitlines():
        if line.startswith("Document ID:"):
            print(line)

    print("\nFIRST 1500 CHARACTERS:")
    print(record_text[:1500])


if __name__ == "__main__":
    main()
