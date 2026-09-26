"""Document type detection: keyword heuristic always available, refined by Gemini when configured."""

import logging

from app.prompts.document_type import build_document_type_prompt
from app.schemas.analysis import DocumentTypeOutput
from app.schemas.document import DocumentType, NormalizedPage
from app.services.gemini_service import ModelOutputError, ModelUnavailableError, StructuredModel

logger = logging.getLogger(__name__)

_SAMPLE_CHARS = 4_000

_TYPE_KEYWORDS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.EMPLOYMENT: ("employment", "employee", "employer", "salary", "ctc", "probation", "designation"),
    DocumentType.INTERNSHIP: ("intern", "internship", "stipend"),
    DocumentType.RENTAL: ("lease", "tenant", "landlord", "rent", "premises", "lessee", "lessor"),
    DocumentType.NDA: ("non-disclosure", "nondisclosure", "confidential information", "disclosing party", "receiving party"),
    DocumentType.FREELANCE: ("freelance", "contractor", "independent contractor", "deliverables", "statement of work"),
    DocumentType.VENDOR: ("vendor", "supplier", "purchase order", "goods", "supply"),
    DocumentType.SAAS_TERMS: ("subscription", "software", "service levels", "saas", "terms of service", "subscriber"),
    DocumentType.FOUNDER: ("founder", "co-founder", "vesting", "cap table", "equity split"),
    DocumentType.PARTNERSHIP: ("partnership", "partner", "profit sharing", "capital contribution"),
    DocumentType.SERVICE: ("service agreement", "service provider", "services", "scope of services"),
    DocumentType.POLICY: ("policy", "code of conduct", "guidelines", "handbook"),
}

_TITLES: dict[DocumentType, str] = {
    DocumentType.EMPLOYMENT: "Employment Agreement",
    DocumentType.INTERNSHIP: "Internship Agreement",
    DocumentType.RENTAL: "Rental Agreement",
    DocumentType.NDA: "Non-Disclosure Agreement",
    DocumentType.FREELANCE: "Freelance Contract",
    DocumentType.VENDOR: "Vendor Agreement",
    DocumentType.SAAS_TERMS: "SaaS Terms",
    DocumentType.FOUNDER: "Founder Agreement",
    DocumentType.PARTNERSHIP: "Partnership Agreement",
    DocumentType.SERVICE: "Service Agreement",
    DocumentType.POLICY: "Policy Document",
    DocumentType.GENERAL: "Agreement",
}


def _sample(pages: list[NormalizedPage]) -> str:
    text = "\n\n".join(page.text for page in pages[:3])
    return text[:_SAMPLE_CHARS]


def heuristic_type(text: str) -> DocumentType:
    lowered = text.lower()
    scores = {
        doc_type: sum(lowered.count(keyword) for keyword in keywords) for doc_type, keywords in _TYPE_KEYWORDS.items()
    }
    best_type, best_score = max(scores.items(), key=lambda item: item[1])
    # Internship documents also mention employment terms; prefer the more specific type when it appears.
    if scores[DocumentType.INTERNSHIP] > 0 and best_type == DocumentType.EMPLOYMENT:
        return DocumentType.INTERNSHIP
    return best_type if best_score > 0 else DocumentType.GENERAL


def detect_document_type(pages: list[NormalizedPage], model: StructuredModel | None) -> tuple[DocumentType, str]:
    sample = _sample(pages)
    fallback = heuristic_type(sample)
    if model is None:
        return fallback, _TITLES[fallback]
    try:
        output = model.generate(build_document_type_prompt(sample), DocumentTypeOutput)
        return output.document_type, output.title.strip()[:120] or _TITLES[output.document_type]
    except (ModelUnavailableError, ModelOutputError):
        logger.info("Document type classification fell back to heuristics")
        return fallback, _TITLES[fallback]
