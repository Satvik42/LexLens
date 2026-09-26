import { useEffect, useState } from 'react';

const STEPS = [
  'Reading document',
  'Identifying relevant clauses',
  'Verifying evidence',
  'Preparing your analysis',
];

export default function AnalyzingState({ title = 'Analyzing your document' }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setStep((current) => Math.min(current + 1, STEPS.length - 1)), 900);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="analyzing card card--padded" role="status" aria-live="polite">
      <div className="row">
        <span className="spinner" aria-hidden="true" />
        <div>
          <h2 className="section-title">{title}</h2>
          <p className="text-secondary text-sm">This may take a moment. Your document is being processed securely.</p>
        </div>
      </div>
      <ol className="analyzing__steps">
        {STEPS.map((label, index) => {
          const done = index < step;
          const current = index === step;
          return (
            <li key={label} className={done ? 'is-done' : current ? 'is-current' : ''}>
              <span aria-hidden="true">{done ? '✓' : current ? '●' : '○'}</span>
              {label}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
