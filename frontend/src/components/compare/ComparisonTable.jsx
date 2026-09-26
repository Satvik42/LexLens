import { Badge } from '../ui';
import EvidenceChip from '../evidence/EvidenceChip';
import { CHANGE_META } from '../../utils/status';

export default function ComparisonTable({ result }) {
  return (
    <div className="table-wrap comparison-table">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Term</th>
            <th scope="col">{result.original_filename}</th>
            <th scope="col">{result.updated_filename}</th>
            <th scope="col">Change</th>
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row) => {
            const meta = CHANGE_META[row.change] ?? CHANGE_META.UNCHANGED;
            return (
              <tr key={row.id}>
                <th scope="row">{row.term}</th>
                <td>
                  <div className="stack" style={{ gap: 8 }}>
                    <span>{row.original_value || 'Not stated'}</span>
                    {row.original_evidence.map((evidence) => (
                      <EvidenceChip key={`o-${row.id}-${evidence.page}`} documentId={result.original_document_id} evidence={evidence} />
                    ))}
                  </div>
                </td>
                <td>
                  <div className="stack" style={{ gap: 8 }}>
                    <span>{row.updated_value || 'Not stated'}</span>
                    {row.updated_evidence.map((evidence) => (
                      <EvidenceChip key={`u-${row.id}-${evidence.page}`} documentId={result.updated_document_id} evidence={evidence} />
                    ))}
                  </div>
                </td>
                <td>
                  <Badge tone={meta.tone}>{meta.label}</Badge>
                  {row.note ? <p className="text-secondary text-sm">{row.note}</p> : null}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
