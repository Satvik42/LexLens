"""Document processing pipeline: storage → parser → segmentation → persisted pages → type detection."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import Document, DocumentPage
from app.schemas.document import NormalizedPage, ParsedDocument, ProcessingStatus
from app.services.document_type_service import detect_document_type
from app.services.gemini_service import StructuredModel
from app.services.local_parser_service import LocalParserService, UnsupportedDocumentError
from app.services.segmentation_service import annotate_blocks
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class DocumentParser:
    """Chooses Document AI when configured and falls back to the local parser."""

    def __init__(self, settings: Settings) -> None:
        self._local = LocalParserService()
        self._document_ai = None
        if settings.uses_document_ai:
            from app.services.document_ai_service import DocumentAiService

            self._document_ai = DocumentAiService(settings)

    def parse(self, content: bytes, mime_type: str) -> ParsedDocument:
        if self._document_ai is not None:
            try:
                parsed = self._document_ai.parse(content, mime_type)
                if parsed.pages and any(page.text.strip() for page in parsed.pages):
                    return parsed
                logger.warning("Document AI returned no text; using local parser")
            except Exception as exc:  # keep the product usable if the managed service is unavailable
                logger.warning("Document AI failed (%s); using local parser", exc.__class__.__name__)
        return self._local.parse(content, mime_type)


class DocumentProcessingService:
    def __init__(self, settings: Settings, storage: StorageService, parser: DocumentParser, model: StructuredModel | None) -> None:
        self._settings = settings
        self._storage = storage
        self._parser = parser
        self._model = model

    def process(self, db: Session, document_id: str) -> None:
        document = db.get(Document, document_id)
        if document is None:
            return
        document.processing_status = ProcessingStatus.PROCESSING
        document.processing_error = None
        db.commit()

        try:
            content = self._storage.download(document.storage_key)
            parsed = self._parser.parse(content, document.mime_type)
            pages = annotate_blocks(parsed.pages)
            self._replace_pages(db, document, pages)
            document.document_type, document.document_title = detect_document_type(pages, self._model)
            document.page_count = len(pages)
            document.parser = parsed.parser
            document.processing_status = ProcessingStatus.READY
            document.expires_at = datetime.now(timezone.utc) + timedelta(hours=self._settings.document_retention_hours)
            logger.info("Processed document %s: %s pages via %s", document.id, len(pages), parsed.parser)
        except UnsupportedDocumentError:
            document.processing_status = ProcessingStatus.FAILED
            document.processing_error = "UNSUPPORTED_DOCUMENT"
            logger.info("Document %s could not be parsed", document.id)
        except Exception:
            document.processing_status = ProcessingStatus.FAILED
            document.processing_error = "PROCESSING_FAILED"
            logger.exception("Unexpected failure processing document %s", document.id)
        db.commit()

    @staticmethod
    def _replace_pages(db: Session, document: Document, pages: list[NormalizedPage]) -> None:
        for existing in list(document.pages):
            db.delete(existing)
        db.flush()
        for page in pages:
            db.add(
                DocumentPage(
                    document_id=document.id,
                    page_number=page.page_number,
                    text=page.text,
                    layout_data={"blocks": [block.model_dump() for block in page.blocks]},
                )
            )
        db.flush()


def load_pages(document: Document) -> list[NormalizedPage]:
    """Rebuild normalized pages from persisted rows (cached document structure, no re-parsing)."""
    return [
        NormalizedPage(page_number=row.page_number, text=row.text, blocks=row.layout_data.get("blocks", []))
        for row in document.pages
    ]
