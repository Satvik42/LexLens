"""Evidence schemas shared by AI output, validation and the API."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceStatus(StrEnum):
    EXPLICITLY_STATED = "EXPLICITLY_STATED"
    PARTIALLY_DETERMINED = "PARTIALLY_DETERMINED"
    NOT_FOUND = "NOT_FOUND"
    POTENTIAL_INCONSISTENCY = "POTENTIAL_INCONSISTENCY"


class EvidenceQuote(BaseModel):
    """What the model returns: a verbatim quote and where it believes the quote is."""

    page: int = Field(description="1-based page number where the quote appears")
    section: str | None = Field(default=None, description="Section number such as '8.2' if the clause has one")
    text: str = Field(description="Verbatim quote copied exactly from the document, 5 to 60 words")


class EvidenceItem(EvidenceQuote):
    """Evidence after server-side validation; only verified items reach the client as verified."""

    id: str | None = None
    heading: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    block_id: str | None = None
    verified: bool = False

    @property
    def label(self) -> str:
        return f"Page {self.page}" + (f" · §{self.section}" if self.section else "")


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    page_number: int
    section: str | None
    text: str
    start_offset: int | None
    end_offset: int | None
    location_data: dict
    verified: bool
