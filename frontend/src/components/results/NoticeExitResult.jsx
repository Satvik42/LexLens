import { useMemo, useState } from 'react';
import StatusBadge from '../evidence/StatusBadge';
import EvidenceCard from '../evidence/EvidenceCard';
import EvidenceChip from '../evidence/EvidenceChip';
import InconsistencyTable from './InconsistencyTable';
import { categoryLabel } from '../../utils/operations';

export default function NoticeExitResult({ documentId, result }) {
  const topics = useMemo(() => {
    const seen = [];
    for (const finding of result.findings) {
      if (!seen.includes(finding.category)) seen.push(finding.category);
    }
    return seen;
  }, [result.findings]);

  const initial = topics.includes('notice_period') ? 'notice_period' : topics[0];
  const [topic, setTopic] = useState(initial);
  const selected = result.findings.filter((finding) => finding.category === topic);
  const finding = selected[0];

  return (
    <div className="analysis-split">
      <nav className="topic-nav" aria-label="Notice and exit topics">
        <p className="eyebrow" style={{ marginBottom: 12 }}>
          Notice &amp; Exit Terms
        </p>
        <ul>
          {topics.map((key) => (
            <li key={key}>
              <button
                type="button"
                className={`topic-nav__item ${topic === key ? 'is-active' : ''}`}
                onClick={() => setTopic(key)}
                aria-current={topic === key ? 'true' : undefined}
              >
                {categoryLabel(key)}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="stack" style={{ gap: 20 }}>
        {finding ? (
          <article className="card card--padded analysis-result">
            <p className="text-secondary text-sm">{finding.label}</p>
            <p className="analysis-result__value">{finding.value || 'Not stated'}</p>
            <StatusBadge status={finding.status} />
            <p className="analysis-result__body">{finding.explanation}</p>
            {finding.evidence[0] ? (
              <EvidenceCard documentId={documentId} evidence={finding.evidence[0]} relatedQuestions={result.related_questions} />
            ) : null}
            {finding.evidence.length > 1 ? (
              <div className="row row--wrap">
                {finding.evidence.slice(1).map((evidence) => (
                  <EvidenceChip
                    key={`${evidence.page}-${evidence.section}-${evidence.text}`}
                    documentId={documentId}
                    evidence={evidence}
                    relatedQuestions={result.related_questions}
                  />
                ))}
              </div>
            ) : null}
          </article>
        ) : (
          <p className="text-secondary">No findings in this topic.</p>
        )}
        {result.inconsistencies.map((item) => (
          <InconsistencyTable
            key={item.id}
            documentId={documentId}
            inconsistency={item}
            relatedQuestions={result.related_questions}
          />
        ))}
      </div>
    </div>
  );
}
