/** Persistent, unobtrusive legal-safety copy (IMPLEMENTATION_PLAN §42). */
export default function Disclaimer({ className = '' }) {
  return (
    <p className={`disclaimer ${className}`}>
      LexLens provides document-grounded information and assistance. It is not a substitute for professional legal advice.
    </p>
  );
}
