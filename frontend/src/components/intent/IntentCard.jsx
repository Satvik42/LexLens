import { useNavigate } from 'react-router-dom';
import { Icon } from '../ui';
import { operationDescription, operationPath } from '../../utils/operations';

const TONE = {
  COMPENSATION: 'warning',
  NOTICE_EXIT: 'danger',
  RESTRICTIONS: 'info',
  CONCERNS: 'danger',
  OBLIGATIONS: 'info',
  KEY_TERMS: 'success',
  DOCUMENT_QA: 'primary',
  LAWYER_PREP: 'primary',
};

/**
 * Keyboard-operable intent card. Enter and Space activate, matching design_plan §35.
 */
export default function IntentCard({ operation, documentId, documentType, selected = false }) {
  const navigate = useNavigate();
  const path = operationPath(documentId, operation.key);
  const description = operationDescription(operation, documentType);
  const tone = TONE[operation.key] ?? 'primary';

  function activate() {
    navigate(path);
  }

  function onKeyDown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      activate();
    }
  }

  return (
    <div
      role="link"
      tabIndex={0}
      className={`card card--interactive intent-card ${selected ? 'card--selected' : ''}`}
      onClick={activate}
      onKeyDown={onKeyDown}
      aria-label={`${operation.label}. ${description}`}
    >
      <span className={`icon-box icon-box--lg icon-box--${tone}`} aria-hidden="true">
        <Icon name={operation.icon} size={26} />
      </span>
      <h3 className="intent-card__title">{operation.label}</h3>
      <p className="intent-card__body">{description}</p>
    </div>
  );
}
