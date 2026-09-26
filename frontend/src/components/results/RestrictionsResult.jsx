import StatusBadge from '../evidence/StatusBadge';
import EvidenceChip from '../evidence/EvidenceChip';
import { Icon } from '../ui';
import { categoryLabel } from '../../utils/operations';

export default function RestrictionsResult({ documentId, result }) {
  return (
    <div className="restriction-list">
      {result.findings.map((finding) => (
        <article key={finding.id} className="card card--padded restriction-card">
          <span className="icon-box icon-box--warning" aria-hidden="true">
            <Icon name="lock" size={18} />
          </span>
          <div className="stack" style={{ gap: 8, flex: 1 }}>
            <p className="text-xs text-muted">{categoryLabel(finding.category)}</p>
            <h3 className="term-card__label">{finding.label}</h3>
            <p className="term-card__value">{finding.value || 'Restriction present'}</p>
            <p className="text-secondary text-sm">{finding.explanation}</p>
            <div className="row row--wrap">
              <StatusBadge status={finding.status} />
              {finding.evidence.map((evidence) => (
                <EvidenceChip
                  key={`${finding.id}-${evidence.page}-${evidence.section}`}
                  documentId={documentId}
                  evidence={evidence}
                  relatedQuestions={result.related_questions}
                />
              ))}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}
