/** Surface primitive with variants: default | interactive | selected | warning | evidence | muted. */
export default function Card({ as: Tag = 'div', variant, padded = true, className = '', children, ...rest }) {
  const classes = ['card', padded ? 'card--padded' : '', variant ? `card--${variant}` : '', className].filter(Boolean).join(' ');
  return (
    <Tag className={classes} {...rest}>
      {children}
    </Tag>
  );
}
