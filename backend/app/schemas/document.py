"""Document schemas: normalized parsed structure and API representations."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ProcessingStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class DocumentType(StrEnum):
    EMPLOYMENT = "EMPLOYMENT"
    RENTAL = "RENTAL"
    NDA = "NDA"
    FREELANCE = "FREELANCE"
    VENDOR = "VENDOR"
    INTERNSHIP = "INTERNSHIP"
    SAAS_TERMS = "SAAS_TERMS"
    FOUNDER = "FOUNDER"
    PARTNERSHIP = "PARTNERSHIP"
    SERVICE = "SERVICE"
    POLICY = "POLICY"
    GENERAL = "GENERAL"


class BoundingBox(BaseModel):
    """Normalized (0-1) bounding box relative to the page."""

    x: float
    y: float
    width: float
    height: float


class NormalizedBlock(BaseModel):
    block_id: str
    text: str
    start: int  # character offset within the page text
    end: int
    section: str | None = None  # e.g. "8.2" once segmentation has run
    is_heading: bool = False
    bounding_box: BoundingBox | None = None


class NormalizedPage(BaseModel):
    page_number: int
    text: str
    blocks: list[NormalizedBlock] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    pages: list[NormalizedPage]
    parser: str  # "document_ai" | "local"

    @property
    def page_count(self) -> int:
        return len(self.pages)


class Clause(BaseModel):
    """A contiguous section of the document identified by segmentation."""

    clause_id: str
    section: str | None
    heading: str | None
    page_number: int
    text: str
    start: int
    end: int


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    mime_type: str
    size_bytes: int
    document_type: DocumentType
    document_title: str | None
    page_count: int | None
    processing_status: ProcessingStatus
    processing_error: str | None
    parser: str | None
    created_at: datetime
    expires_at: datetime | None


class DocumentStatusOut(BaseModel):
    id: str
    processing_status: ProcessingStatus
    processing_error: str | None
    page_count: int | None
    document_type: DocumentType


class DocumentPagesOut(BaseModel):
    document_id: str
    page_count: int
    pages: list[NormalizedPage]
