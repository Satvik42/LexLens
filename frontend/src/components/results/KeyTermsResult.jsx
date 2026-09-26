import StatusBadge from '../evidence/StatusBadge';
import EvidenceChip from '../evidence/EvidenceChip';
import EvidenceCard from '../evidence/EvidenceCard';
import { categoryLabel } from '../../utils/operations';

export default function KeyTermsResult({ documentId, result }) {
  return (
    <div className="term-grid">
      {result.findings.map((finding) => (
        <article key={finding.id} className="card card--padded term-card">
          <p className="text-xs text-muted">{categoryLabel(finding.category)}</p>
          <h3 className="term-card__label">{finding.label}</h3>
          <p className="term-card__value">{finding.value || 'Not stated'}</p>
          <StatusBadge status={finding.status} />
          {finding.evidence[0] ? (
            <div className="stack" style={{ gap: 8, marginTop: 12 }}>
              <EvidenceChip documentId={documentId} evidence={finding.evidence[0]} relatedQuestions={result.related_questions} />
              <EvidenceCard documentId={documentId} evidence={finding.evidence[0]} relatedQuestions={result.related_questions} />
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}
