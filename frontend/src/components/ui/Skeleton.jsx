/** Loading placeholder block. Parent should provide an aria-live status message. */
export default function Skeleton({ width = '100%', height = 16, className = '', style }) {
  return <div className={`skeleton ${className}`} style={{ width, height, ...style }} aria-hidden="true" />;
}
