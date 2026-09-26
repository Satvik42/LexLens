"""Converts validated model output into API result objects. Shared by analysis, QA, lawyer prep and comparison."""

from collections.abc import Iterable

from app.schemas.analysis import (
    AnalysisResult,
    Concern,
    ConcernKind,
    ConcernOutput,
    ConcernsOutput,
    Finding,
    FindingOutput,
    FindingsOutput,
    Inconsistency,
    InconsistencyOutput,
    InconsistencyValue,
)
from app.schemas.evidence import EvidenceItem, EvidenceStatus
from app.services.evidence_service import EvidenceValidator, downgrade_status


def convert_findings(outputs: list[FindingOutput], validator: EvidenceValidator) -> list[Finding]:
    findings: list[Finding] = []
    for index, output in enumerate(outputs, start=1):
        evidence = validator.validate_all(output.evidence)
        status, note = downgrade_status(output.status, bool(evidence), bool(output.evidence))
        findings.append(
            Finding(
                id=f"f{index}",
                label=output.label.strip(),
                value=output.value.strip() if output.value else None,
                category=output.category,
                status=status,
                explanation=output.explanation.strip(),
                evidence=evidence,
                verification_note=note,
            )
        )
    return findings


def convert_concerns(outputs: list[ConcernOutput], validator: EvidenceValidator) -> list[Concern]:
    concerns: list[Concern] = []
    for index, output in enumerate(outputs, start=1):
        evidence = validator.validate_all(output.evidence)
        if output.kind == ConcernKind.POTENTIAL_INCONSISTENCY and len(evidence) < 2:
            continue  # an inconsistency needs both sides verified
        note = None
        if output.evidence and not evidence:
            note = "We couldn't verify this against the document, so it is not shown as verified."
        concerns.append(
            Concern(
                id=f"c{index}",
                kind=output.kind,
                title=output.title.strip(),
                explanation=output.explanation.strip(),
                evidence=evidence,
                verification_note=note,
            )
        )
    return concerns


def convert_inconsistencies(outputs: list[InconsistencyOutput], validator: EvidenceValidator) -> list[Inconsistency]:
    inconsistencies: list[Inconsistency] = []
    for index, output in enumerate(outputs, start=1):
        values = []
        for value in output.values:
            item = validator.validate(value.evidence)
            if item is not None:
                values.append(InconsistencyValue(value=value.value.strip(), evidence=item))
        if len(values) >= 2:
            inconsistencies.append(
                Inconsistency(id=f"i{index}", topic=output.topic.strip(), description=output.description.strip(), values=values)
            )
    return inconsistencies


def overall_status(findings: list[Finding], concerns: list[Concern], inconsistencies: list[Inconsistency]) -> EvidenceStatus:
    if inconsistencies:
        return EvidenceStatus.POTENTIAL_INCONSISTENCY
    statuses = [f.status for f in findings]
    if concerns and not findings:
        return EvidenceStatus.EXPLICITLY_STATED
    if not statuses or all(s == EvidenceStatus.NOT_FOUND for s in statuses):
        return EvidenceStatus.NOT_FOUND
    if any(s == EvidenceStatus.EXPLICITLY_STATED for s in statuses):
        return EvidenceStatus.EXPLICITLY_STATED
    return EvidenceStatus.PARTIALLY_DETERMINED


def assemble_analysis(
    output: FindingsOutput | ConcernsOutput,
    validator: EvidenceValidator,
    *,
    result_id: str,
    document_id: str,
    operation: str,
    title: str,
) -> AnalysisResult:
    findings = convert_findings(output.findings, validator) if isinstance(output, FindingsOutput) else []
    concerns = convert_concerns(output.concerns, validator) if isinstance(output, ConcernsOutput) else []
    inconsistencies = convert_inconsistencies(output.inconsistencies, validator)
    return AnalysisResult(
        id=result_id,
        document_id=document_id,
        operation=operation,
        status=overall_status(findings, concerns, inconsistencies),
        title=title,
        summary=output.summary.strip(),
        findings=findings,
        concerns=concerns,
        inconsistencies=inconsistencies,
        related_questions=_clean_questions(output.related_questions),
        professional_questions=_clean_questions(output.professional_questions),
        verification_notes=validator.report.notes,
    )


def iter_analysis_evidence(result: AnalysisResult) -> Iterable[EvidenceItem]:
    for finding in result.findings:
        yield from finding.evidence
    for concern in result.concerns:
        yield from concern.evidence
    for inconsistency in result.inconsistencies:
        for value in inconsistency.values:
            yield value.evidence


def _clean_questions(questions: list[str], limit: int = 6) -> list[str]:
    cleaned = []
    for question in questions:
        text = question.strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned[:limit]
