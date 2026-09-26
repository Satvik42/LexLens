import { Link } from 'react-router-dom';
import { Icon } from '../ui';
import { evidenceLabel, normalizeEvidence, viewerPath } from '../../utils/evidence';

/** Keyboard-accessible source chip. Navigates to the viewer at the evidence location. */
export default function EvidenceChip({ documentId, evidence, relatedQuestions }) {
  const item = normalizeEvidence(evidence);
  if (!item) return null;
  return (
    <Link
      className="chip chip--evidence"
      to={viewerPath(documentId, item)}
      state={{ evidence: item, relatedQuestions }}
    >
      <Icon name="document" size={13} />
      {evidenceLabel(item)}
    </Link>
  );
}
