
import json
from pathlib import Path

from medthread.pipeline import run_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    records_path = (
        PROJECT_ROOT
        / "data"
        / "sample_records"
        / "fictional_hospital_stay.txt"
    )

    records = records_path.read_text(encoding="utf-8")

    result = run_pipeline(records)

    print("\n=== MEDTHREAD AI: DISCHARGE HANDOFF ===\n")
    print(
        json.dumps(
            result.handoff.model_dump(),
            indent=2,
        )
    )

    print("\n=== SOURCE VALIDATION ===")

    if result.validation_errors:
        print("VALIDATION FAILED")
        for error in result.validation_errors:
            print(f"- {error}")
    else:
        print("Automated source-reference checks passed.")

    print("\n=== SAFETY WARNINGS ===")
    for warning in result.safety_warnings:
        print(f"- {warning}")

    print("\n=== CITATION REPAIRS ===")
    for repair in result.citation_repairs:
        print(f"- {repair}")

    print(
        "\nClinician review required:",
        result.handoff.requires_clinician_review,
    )
    print(
        "Automated checks do not establish clinical "
        "correctness or completeness."
    )


if __name__ == "__main__":
    main()
