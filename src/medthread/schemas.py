
from typing import Literal

from pydantic import BaseModel, Field

class SourceReference(BaseModel):
    """Identifies where a statement came from in the hospital record."""

    document_name: str = Field(
        description="Name of the source document."
    )
    section: str = Field(
        description="Section containing the supporting information."
    )
    quoted_text: str = Field(
        description="Short excerpt supporting the statement."
    )


class DocumentedFact(BaseModel):
    """A fact supported by the provided hospital records."""

    content: str = Field(
        description="A concise statement grounded in the records."
    )
    sources: list[SourceReference] = Field(
        description="Source references supporting this fact."
    )


class MissingInformation(BaseModel):
    """Information that is needed but is not documented."""

    field_name: str = Field(
        description="The missing information, such as discharge medication instructions."
    )
    reason: str = Field(
        description="Why this information needs clarification."
    )
    status: Literal["needs_review"] = "needs_review"


class SectionAssessment(BaseModel):
    """Describes what the provided records establish about a section."""

    status: Literal[
        "documented",
        "none_documented",
        "unclear",
    ] = Field(
        description=(
            "documented: relevant items were found; "
            "none_documented: the reviewed records explicitly "
            "state there are none; "
            "unclear: the records do not establish the answer."
        )
    )

    explanation: str = Field(
        description="Explain what the reviewed records establish."
    )

    sources: list[SourceReference] = Field(
        default_factory=list,
        description="Sources supporting this assessment, if available.",
    )



class DischargeHandoff(BaseModel):
    """Structured draft handoff for the next care provider."""

    patient_identifier: str | None = Field(
        default=None,
        description="Fictional or de-identified identifier; never a patient's name."
    )
    admission_reason: DocumentedFact | None = None
    hospital_course: DocumentedFact | None = None

    discharge_diagnoses: list[DocumentedFact] = Field(
        default_factory=list
    )
    medication_changes: list[DocumentedFact] = Field(
        default_factory=list
    )
    pending_tests: list[DocumentedFact] = Field(
        default_factory=list
    )

    # New assessments — separate fields on the handoff
    pending_tests_assessment: SectionAssessment
    medication_changes_assessment: SectionAssessment

    follow_up_instructions: list[DocumentedFact] = Field(
        default_factory=list
    )
    missing_information: list[MissingInformation] = Field(
        default_factory=list
    )
    requires_clinician_review: bool = True

