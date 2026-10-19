
from dataclasses import dataclass, field

from medthread.schemas import DischargeHandoff
from medthread.extractor import extract_handoff
from medthread.citation_repair import (
    repair_trivial_citation_formatting,
)
from medthread.assessment_normalizer import (
    normalize_uncertain_assessments,
    quarantine_order_only_medication_changes,
)
from medthread.validation import (
    enforce_pending_tests_uncertainty,
    validate_section_assessments,
    validate_sources,
)
from medthread.assessment_safety import (
    check_assessment_safety,
)


@dataclass
class PipelineResult:
    handoff: DischargeHandoff
    validation_errors: list[str] = field(default_factory=list)
    safety_warnings: list[str] = field(default_factory=list)
    citation_repairs: list[str] = field(default_factory=list)


def run_pipeline(records: str) -> PipelineResult:
    """Generate and check a clinician-review handoff draft."""

    if not records.strip():
        raise ValueError("Source records cannot be empty.")

    handoff = extract_handoff(records)

    citation_repairs = repair_trivial_citation_formatting(
        handoff, records
    )

    quarantine_warnings = (
        quarantine_order_only_medication_changes(handoff)
    )

    safety_warnings = enforce_pending_tests_uncertainty(
        handoff
    )

    normalization_changes = normalize_uncertain_assessments(
        handoff, records
    )

    safety_warnings.extend(quarantine_warnings)
    safety_warnings.extend(normalization_changes)

    validation_errors = validate_sources(handoff, records)
    validation_errors.extend(
        validate_section_assessments(handoff)
    )
    validation_errors.extend(
        check_assessment_safety(handoff, records)
    )

    return PipelineResult(
        handoff=handoff,
        validation_errors=validation_errors,
        safety_warnings=safety_warnings,
        citation_repairs=citation_repairs,
    )
