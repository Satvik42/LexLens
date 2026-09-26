import { forwardRef } from 'react';
import { Link } from 'react-router-dom';
import Icon from './Icon';

/**
 * Button primitive. Renders a <button>, or a router <Link> when `to` is provided, so semantics stay correct.
 */
const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', icon, iconRight, loading = false, to, className = '', children, disabled, ...rest },
  ref,
) {
  const classes = ['btn', `btn--${variant}`, size !== 'md' ? `btn--${size}` : '', className].filter(Boolean).join(' ');
  const iconSize = size === 'sm' ? 14 : 16;
  const content = (
    <>
      {loading ? <span className="spinner" aria-hidden="true" /> : icon ? <Icon name={icon} size={iconSize} /> : null}
      <span>{children}</span>
      {iconRight ? <Icon name={iconRight} size={iconSize} /> : null}
    </>
  );

  if (to) {
    return (
      <Link ref={ref} to={to} className={classes} aria-disabled={disabled || undefined} {...rest}>
        {content}
      </Link>
    );
  }
  return (
    <button ref={ref} type="button" className={classes} disabled={disabled || loading} aria-busy={loading || undefined} {...rest}>
      {content}
    </button>
  );
});

export default Button;
