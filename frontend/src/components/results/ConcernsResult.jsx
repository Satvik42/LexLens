import { Badge } from '../ui';
import EvidenceChip from '../evidence/EvidenceChip';
import InconsistencyTable from './InconsistencyTable';
import { CONCERN_META } from '../../utils/status';

export default function ConcernsResult({ documentId, result }) {
  if (!result.concerns.length && !result.inconsistencies.length) {
    return (
      <div className="card card--padded card--muted">
        <h2 className="section-title">No potential inconsistencies identified</h2>
        <p className="text-secondary" style={{ marginTop: 8 }}>
          We did not identify conflicting clauses for this analysis. This is not an exhaustive legal review.
        </p>
      </div>
    );
  }

  return (
    <div className="stack" style={{ gap: 20 }}>
      {result.inconsistencies.map((item) => (
        <InconsistencyTable key={item.id} documentId={documentId} inconsistency={item} relatedQuestions={result.related_questions} />
      ))}
      {result.concerns.map((concern) => {
        const meta = CONCERN_META[concern.kind] ?? CONCERN_META.POTENTIAL_CONCERN;
        return (
          <article key={concern.id} className="card card--padded concern-card">
            <Badge tone={meta.tone} icon={meta.icon}>
              {meta.label}
            </Badge>
            <h3 className="section-title" style={{ marginTop: 10 }}>
              {concern.title}
            </h3>
            <p className="text-secondary" style={{ marginTop: 8 }}>
              {concern.explanation}
            </p>
            <div className="row row--wrap" style={{ marginTop: 12 }}>
              {concern.evidence.map((evidence) => (
                <EvidenceChip
                  key={`${concern.id}-${evidence.page}-${evidence.section}`}
                  documentId={documentId}
                  evidence={evidence}
                  relatedQuestions={result.related_questions}
                />
              ))}
            </div>
          </article>
        );
      })}
    </div>
  );
}
