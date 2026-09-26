import { Link } from 'react-router-dom';
import { Icon } from '../ui';
import { evidenceLabel, normalizeEvidence, viewerPath } from '../../utils/evidence';

export default function EvidenceCard({ documentId, evidence, relatedQuestions }) {
  const item = normalizeEvidence(evidence);
  if (!item) return null;
  const heading = item.heading ? ` ${item.heading}` : '';
  return (
    <article className="card card--evidence evidence-card">
      <p className="eyebrow">Source</p>
      <p className="evidence-card__meta">
        {evidenceLabel(item)}
        {heading}
      </p>
      {item.text ? <blockquote className="evidence-card__quote">“{item.text}”</blockquote> : null}
      <Link className="evidence-card__action" to={viewerPath(documentId, item)} state={{ evidence: item, relatedQuestions }}>
        View in document
        <Icon name="arrowRight" size={14} />
      </Link>
    </article>
  );
}
