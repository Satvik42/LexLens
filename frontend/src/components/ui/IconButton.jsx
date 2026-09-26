import Icon from './Icon';

/** Icon-only button with a mandatory accessible name. */
export default function IconButton({ icon, label, size = 18, className = '', ...rest }) {
  return (
    <button type="button" className={`icon-btn ${className}`} aria-label={label} title={label} {...rest}>
      <Icon name={icon} size={size} />
    </button>
  );
}
