export default function Logo({ compact = false }) {
  return (
    <span className="logo">
      <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
        <rect width="32" height="32" rx="8" fill="#5547e8" />
        <path d="M10 8h8l5 5v11a1 1 0 0 1-1 1H10a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" fill="#fff" opacity=".95" />
        <rect x="12" y="16" width="9" height="2" rx="1" fill="#fff1a8" />
        <rect x="12" y="20" width="6" height="2" rx="1" fill="#5547e8" opacity=".5" />
      </svg>
      {compact ? null : <span className="logo__text">LexLens</span>}
    </span>
  );
}
