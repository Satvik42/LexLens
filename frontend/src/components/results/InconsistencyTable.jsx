import { Button } from '../ui';
import EvidenceChip from '../evidence/EvidenceChip';
import { viewerPath, normalizeEvidence } from '../../utils/evidence';
import { useNavigate } from 'react-router-dom';

export default function InconsistencyTable({ documentId, inconsistency, relatedQuestions }) {
  const navigate = useNavigate();
  if (!inconsistency) return null;

  return (
    <article className="card card--warning card--padded inconsistency">
      <header className="stack" style={{ gap: 8, marginBottom: 16 }}>
        <p className="eyebrow">Potential inconsistency</p>
        <h3 className="section-title">{inconsistency.topic}</h3>
        <p className="text-secondary text-sm">
          {inconsistency.description ||
            'These clauses appear to specify different information. Consider clarifying which provision applies.'}
        </p>
      </header>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th scope="col">Location</th>
              <th scope="col">Clause</th>
              <th scope="col">Value</th>
            </tr>
          </thead>
          <tbody>
            {inconsistency.values.map((row, index) => {
              const evidence = normalizeEvidence(row.evidence);
              return (
                <tr key={`${row.value}-${index}`}>
                  <td>
                    <EvidenceChip documentId={documentId} evidence={evidence} relatedQuestions={relatedQuestions} />
                  </td>
                  <td>§{evidence?.section || '—'}</td>
                  <td>
                    <strong>{row.value}</strong>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="row row--wrap" style={{ marginTop: 16 }}>
        {inconsistency.values.map((row, index) => {
          const evidence = normalizeEvidence(row.evidence);
          return (
            <Button
              key={`${row.value}-view-${index}`}
              variant="secondary"
              size="sm"
              icon="eye"
              onClick={() => navigate(viewerPath(documentId, evidence), { state: { evidence, relatedQuestions } })}
            >
              View §{evidence?.section || evidence?.page}
            </Button>
          );
        })}
        <Button variant="ghost" size="sm" icon="scale" to={`/documents/${documentId}/lawyer`}>
          Add to lawyer questions
        </Button>
      </div>
    </article>
  );
}
