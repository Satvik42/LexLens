import { useState } from 'react';
import EvidenceChip from '../evidence/EvidenceChip';

export default function ObligationsResult({ documentId, result }) {
  const [checked, setChecked] = useState(() => new Set());

  function toggle(id) {
    setChecked((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <ul className="checklist">
      {result.findings.map((finding) => {
        const id = `obligation-${finding.id}`;
        const isChecked = checked.has(finding.id);
        return (
          <li key={finding.id} className="card card--padded checklist__item">
            <input
              id={id}
              type="checkbox"
              checked={isChecked}
              onChange={() => toggle(finding.id)}
            />
            <div>
              <label htmlFor={id} className={isChecked ? 'is-checked' : ''}>
                {finding.value || finding.label}
              </label>
              {finding.explanation ? <p className="text-secondary text-sm">{finding.explanation}</p> : null}
              <div className="row row--wrap" style={{ marginTop: 8 }}>
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
          </li>
        );
      })}
    </ul>
  );
}
