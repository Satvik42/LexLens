import Icon from './Icon';

const ICONS = { info: 'info', warning: 'alert', danger: 'alert', success: 'checkCircle', neutral: 'info' };

/** Inline message. Uses role="alert" for errors so screen readers announce them. */
export default function AlertCard({ tone = 'info', title, children, className = '', role }) {
  const resolvedRole = role ?? (tone === 'danger' ? 'alert' : 'status');
  return (
    <div className={`alert alert--${tone} ${className}`} role={resolvedRole}>
      <span className="alert__icon">
        <Icon name={ICONS[tone]} size={18} />
      </span>
      <div>
        {title ? <div className="alert__title">{title}</div> : null}
        {children ? <div>{children}</div> : null}
      </div>
    </div>
  );
}
