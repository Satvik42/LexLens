"""Persists verified evidence and assigns stable ids that the frontend can resolve via the evidence endpoint."""

from sqlalchemy.orm import Session

from app.db.models import Evidence
from app.schemas.evidence import EvidenceItem


def persist_evidence(db: Session, document_id: str, items: list[EvidenceItem], analysis_result_id: str | None = None) -> None:
    for item in items:
        row = Evidence(
            analysis_result_id=analysis_result_id,
            document_id=document_id,
            page_number=item.page,
            section=item.section,
            text=item.text,
            start_offset=item.start_offset,
            end_offset=item.end_offset,
            location_data={"block_id": item.block_id, "heading": item.heading},
            verified=item.verified,
        )
        db.add(row)
        db.flush()
        item.id = row.id
