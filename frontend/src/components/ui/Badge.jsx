import Icon from './Icon';

/** Semantic badge: tone drives colour, but meaning is always carried by text (and an optional icon). */
export default function Badge({ tone = 'neutral', icon, children, className = '' }) {
  return (
    <span className={`badge badge--${tone} ${className}`}>
      {icon ? <Icon name={icon} size={13} strokeWidth={2.2} /> : null}
      {children}
    </span>
  );
}
