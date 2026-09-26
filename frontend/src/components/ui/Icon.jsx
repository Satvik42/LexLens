/**
 * Inline SVG icon set (stroke-based, 24px grid). Icons are decorative by default (aria-hidden);
 * pass a `label` to expose them to assistive technology.
 */
const PATHS = {
  upload: 'M12 16V4m0 0-4 4m4-4 4 4M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3',
  file: 'M14 3H7a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V8l-4-5zm0 0v5h4M9 13h6M9 17h6',
  check: 'M5 12.5l4.5 4.5L19 7.5',
  checkCircle: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zm-3.5-9 2.5 2.5 5-5',
  alert: 'M12 9v4m0 4h.01M10.3 4.2 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0z',
  info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zm0-9v5m0-8h.01',
  circle: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z',
  circleDashed: 'M12 3a9 9 0 0 1 9 9m-9 9a9 9 0 0 1-9-9m9-9a9 9 0 0 0-9 9m9 9a9 9 0 0 0 9-9',
  lock: 'M7 11V8a5 5 0 0 1 10 0v3M6 11h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1z',
  money: 'M3 7h18v10H3zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 10h.01M18 14h.01',
  exit: 'M15 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4M10 17l5-5-5-5m5 5H3',
  eye: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zm10 3a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  listCheck: 'M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2',
  message: 'M21 12a8 8 0 0 1-8 8H6l-3 3V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8z',
  scale: 'M12 3v18M5 21h14M3 8l9-3 9 3M3 8l3 6a3 3 0 0 0 6 0L9 8M15 8l3 6a3 3 0 0 0 6 0l-3-6',
  compare: 'M4 4h6v16H4zM14 4h6v16h-6z',
  plus: 'M12 5v14M5 12h14',
  arrowRight: 'M5 12h14m-6-6 6 6-6 6',
  arrowLeft: 'M19 12H5m6 6-6-6 6-6',
  chevronLeft: 'M15 6l-6 6 6 6',
  chevronRight: 'M9 6l6 6-6 6',
  zoomIn: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zm9 16-4.3-4.3M11 8v6m-3-3h6',
  zoomOut: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zm9 16-4.3-4.3M8 11h6',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zm9 16-4.3-4.3',
  copy: 'M9 9h10v11H9zM5 15V4h10',
  download: 'M12 4v12m0 0-4-4m4 4 4-4M4 20h16',
  close: 'M6 6l12 12M18 6 6 18',
  external: 'M14 4h6v6m0-6-9 9M20 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h5',
  shield: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z',
  key: 'M14 4a6 6 0 1 0 0 12 6 6 0 0 0 0-12zM4 20l4-4m2 2 2-2',
  calendar: 'M4 6h16v14H4zM8 3v4m8-4v4M4 10h16',
  menu: 'M4 7h16M4 12h16M4 17h16',
  send: 'M4 12l16-8-6 16-3-6-7-2z',
  print: 'M7 8V4h10v4M5 8h14a1 1 0 0 1 1 1v7h-4v4H8v-4H4V9a1 1 0 0 1 1-1z',
  document: 'M6 3h9l5 5v13H6zM15 3v5h5M9 12h6M9 16h4',
  quote: 'M7 7h4v4H7zM7 11c0 3 1 4 4 4M13 7h4v4h-4zM13 11c0 3 1 4 4 4',
  logout: 'M9 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h4M15 17l5-5-5-5m5 5H9',
  sparkle: 'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z',
};

export default function Icon({ name, size = 20, label, className = '', strokeWidth = 1.8 }) {
  const path = PATHS[name];
  if (!path) return null;
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={label ? undefined : 'true'}
      role={label ? 'img' : undefined}
      aria-label={label}
      focusable="false"
    >
      <path d={path} />
    </svg>
  );
}

export const ICON_NAMES = Object.keys(PATHS);
