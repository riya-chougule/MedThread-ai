
import re

from medthread.schemas import DischargeHandoff
from medthread.validation import _parse_document_sections


def repair_trivial_citation_formatting(
    handoff: DischargeHandoff,
    records: str,
) -> list[str]:
    """
    Repair only trivial quotation formatting differences.

    Never change document IDs, section names, or the meaning
    of a quotation.

    Return descriptions of repairs made.
    """
    documents = _parse_document_sections(records)
    repairs = []

    facts = []

    for field_name in ("admission_reason", "hospital_course"):
        fact = getattr(handoff, field_name)
        if fact is not None:
            facts.append(fact)

    for field_name in (
        "discharge_diagnoses",
        "medication_changes",
        "pending_tests",
        "follow_up_instructions",
    ):
        facts.extend(getattr(handoff, field_name))

    facts.extend(
        [
            handoff.pending_tests_assessment,
            handoff.medication_changes_assessment,
        ]
    )

    for fact in facts:
        for source in fact.sources:
            sections = documents.get(source.document_name, {})
            section_text = sections.get(source.section)

            if section_text is None:
                continue

            original_quote = source.quoted_text

            if original_quote in section_text:
                continue

            candidate = original_quote.strip()

            if candidate not in section_text:
                candidate = re.sub(
                    r"[.!?]$",
                    "",
                    candidate,
                ).rstrip()

            if candidate and candidate in section_text:
                source.quoted_text = candidate

                repairs.append(
                    "Corrected trivial quotation formatting for "
                    f"{source.document_name} / {source.section}."
                )

    return repairs
