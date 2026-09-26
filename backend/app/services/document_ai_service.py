"""Google Cloud Document AI integration: layout/OCR extraction into the normalized page structure."""

import logging

from app.config import Settings
from app.schemas.document import BoundingBox, NormalizedBlock, NormalizedPage, ParsedDocument
from app.services.text_utils import make_block_id

logger = logging.getLogger(__name__)


class DocumentAiService:
    def __init__(self, settings: Settings) -> None:
        from google.api_core.client_options import ClientOptions
        from google.cloud import documentai

        self._documentai = documentai
        location = settings.document_ai_location
        self._client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        )
        self._processor_name = self._client.processor_path(
            settings.gcp_project_id, location, settings.document_ai_processor_id
        )

    def parse(self, content: bytes, mime_type: str) -> ParsedDocument:
        request = self._documentai.ProcessRequest(
            name=self._processor_name,
            raw_document=self._documentai.RawDocument(content=content, mime_type=mime_type),
        )
        result = self._client.process_document(request=request)
        return _normalize(result.document)


def _anchor_text(full_text: str, layout) -> tuple[str, int, int]:
    segments = layout.text_anchor.text_segments
    if not segments:
        return "", 0, 0
    start = int(segments[0].start_index)
    end = int(segments[-1].end_index)
    return full_text[start:end], start, end


def _bounding_box(layout) -> BoundingBox | None:
    vertices = layout.bounding_poly.normalized_vertices
    if not vertices:
        return None
    xs = [v.x for v in vertices]
    ys = [v.y for v in vertices]
    return BoundingBox(x=min(xs), y=min(ys), width=max(xs) - min(xs), height=max(ys) - min(ys))


def _normalize(document) -> ParsedDocument:
    full_text = document.text or ""
    pages: list[NormalizedPage] = []

    for index, page in enumerate(document.pages, start=1):
        units = page.paragraphs or page.blocks or page.lines
        page_text_parts: list[str] = []
        blocks: list[NormalizedBlock] = []
        cursor = 0
        for unit_index, unit in enumerate(units):
            text, _, _ = _anchor_text(full_text, unit.layout)
            text = text.strip()
            if not text:
                continue
            start = cursor
            end = start + len(text)
            blocks.append(
                NormalizedBlock(
                    block_id=make_block_id(index, unit_index),
                    text=text,
                    start=start,
                    end=end,
                    bounding_box=_bounding_box(unit.layout),
                )
            )
            page_text_parts.append(text)
            cursor = end + 2  # "\n\n" separator
        pages.append(NormalizedPage(page_number=index, text="\n\n".join(page_text_parts), blocks=blocks))

    return ParsedDocument(pages=pages, parser="document_ai")
