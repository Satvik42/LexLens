import { Icon } from '../ui';

/**
 * Required absence-of-evidence UI (IMPLEMENTATION_PLAN §13, design_plan §25).
 */
export default function NotDetermined({
  title = 'Cannot be determined from this document',
  explanation,
  whatIFound,
  professionalQuestions = [],
}) {
  return (
    <article className="not-determined">
      <div className="not-determined__hero">
        <span className="icon-box icon-box--info" aria-hidden="true">
          <Icon name="info" size={22} />
        </span>
        <div>
          <h2 className="page-title" style={{ fontSize: 'var(--text-xl)' }}>
            {title}
          </h2>
          {explanation ? <p className="text-secondary" style={{ marginTop: 8 }}>{explanation}</p> : null}
        </div>
      </div>

      <section className="card card--muted card--padded">
        <h3 className="section-title">What I found</h3>
        <p className="text-secondary" style={{ marginTop: 8 }}>
          {whatIFound || 'No supporting clause was identified in this document.'}
        </p>
      </section>

      {professionalQuestions.length ? (
        <section className="pro-callout">
          <h3 className="section-title">You may want to ask a legal professional</h3>
          <ul className="pro-questions">
            {professionalQuestions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </article>
  );
}
