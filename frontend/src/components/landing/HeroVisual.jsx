import { useState } from 'react';

const INSIGHTS = [
  { key: 'notice', label: 'Notice period', value: '60 days', source: 'Page 15', className: 'hero-float--notice' },
  { key: 'bond', label: 'Training bond', value: '₹2,00,000', source: 'Page 14', className: 'hero-float--bond' },
  { key: 'compete', label: 'Non-compete', value: 'Found', source: 'Page 21', className: 'hero-float--compete' },
];

/** Document stack from the landing reference. Selecting an insight moves the yellow mark. */
export default function HeroVisual() {
  const [active, setActive] = useState(0);

  return (
    <div className="hero-visual">
      <div className="hero-visual__stack">
        <span className="hero-visual__sheet hero-visual__sheet--back" />
        <span className="hero-visual__sheet hero-visual__sheet--mid" />
        <div className="hero-visual__page">
          <span className="hero-visual__rule" />
          <span className="hero-visual__rule hero-visual__rule--short" />
          <span className="hero-visual__rule" />
          <span className={`hero-visual__highlight hero-visual__highlight--${INSIGHTS[active].key}`} />
          <span className="hero-visual__rule hero-visual__rule--mid" />
          <span className="hero-visual__rule" />
          <span className="hero-visual__rule hero-visual__rule--short" />
          <span className="hero-visual__rule" />
        </div>
      </div>
      {INSIGHTS.map((insight, index) => (
        <button
          key={insight.key}
          type="button"
          className={`hero-float ${insight.className} ${index === active ? 'is-active' : ''}`}
          aria-pressed={index === active}
          onClick={() => setActive(index)}
        >
          <span>
            <strong>{insight.label}</strong>
            <span>{insight.value}</span>
            <em>{insight.source}</em>
          </span>
        </button>
      ))}
      <p className="hero-visual__caption">Select a finding. The mark shows where it lives in the document.</p>
    </div>
  );
}
