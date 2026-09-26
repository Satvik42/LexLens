/** Page-level heading with optional eyebrow, subtitle and right-aligned actions. */
export default function SectionHeader({ eyebrow, title, subtitle, actions, as: Tag = 'h1', className = '' }) {
  return (
    <header className={`row row--between row--wrap ${className}`} style={{ alignItems: 'flex-start', marginBottom: 'var(--space-6)' }}>
      <div>
        {eyebrow ? <div className="eyebrow" style={{ marginBottom: 'var(--space-2)' }}>{eyebrow}</div> : null}
        <Tag className="page-title">{title}</Tag>
        {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
      </div>
      {actions ? <div className="row row--wrap">{actions}</div> : null}
    </header>
  );
}
