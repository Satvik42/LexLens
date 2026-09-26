import { Link } from 'react-router-dom';
import { Icon } from '../ui';
import { OPERATIONS } from '../../utils/operations';
import IntentCard from './IntentCard';

export default function IntentGrid({ documentId, documentType }) {
  return (
    <div className="intent-grid-wrap">
      <div className="intent-grid">
        {OPERATIONS.map((operation) => (
          <IntentCard key={operation.key} operation={operation} documentId={documentId} documentType={documentType} />
        ))}
      </div>
      <Link to={`/documents/${documentId}/compare`} className="compare-cta">
        <span className="icon-box" aria-hidden="true">
          <Icon name="plus" size={18} />
        </span>
        <span>
          <strong>Compare another document</strong>
          <span className="text-secondary text-sm">Upload a second version and compare the terms that changed.</span>
        </span>
      </Link>
    </div>
  );
}
