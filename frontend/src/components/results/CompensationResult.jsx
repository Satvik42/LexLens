import StatusBadge from '../evidence/StatusBadge';
import EvidenceChip from '../evidence/EvidenceChip';
import { categoryLabel } from '../../utils/operations';

export default function CompensationResult({ documentId, result }) {
  const groups = groupBy(result.findings, (item) => item.category);
  return (
    <div className="stack" style={{ gap: 24 }}>
      {Object.entries(groups).map(([category, findings]) => (
        <section key={category}>
          <h3 className="section-title" style={{ marginBottom: 12 }}>
            {categoryLabel(category)}
          </h3>
          <div className="term-grid">
            {findings.map((finding) => (
              <article key={finding.id} className="card card--padded compensation-card">
                <h4 className="term-card__label">{finding.label}</h4>
                <p className="term-card__value term-card__value--money">{finding.value || 'Not stated'}</p>
                <p className="text-secondary text-sm">{finding.explanation}</p>
                <div className="row row--wrap" style={{ marginTop: 10 }}>
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
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function groupBy(items, keyFn) {
  return items.reduce((acc, item) => {
    const key = keyFn(item) || 'other';
    (acc[key] ??= []).push(item);
    return acc;
  }, {});
}
