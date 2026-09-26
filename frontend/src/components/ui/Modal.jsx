import { useEffect, useRef } from 'react';
import IconButton from './IconButton';

/**
 * Accessible dialog: focus moves inside on open, Escape closes, focus returns to the opener, background clicks close.
 */
export default function Modal({ open, title, onClose, children }) {
  const dialogRef = useRef(null);
  const openerRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    openerRef.current = document.activeElement;
    const focusable = dialogRef.current?.querySelector('input, button, textarea, [tabindex]:not([tabindex="-1"])');
    (focusable ?? dialogRef.current)?.focus();

    const onKey = (event) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab' && dialogRef.current) trapFocus(event, dialogRef.current);
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      openerRef.current?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" ref={dialogRef} tabIndex={-1}>
        <div className="row row--between" style={{ marginBottom: 'var(--space-4)' }}>
          <h2 id="modal-title" className="section-title">
            {title}
          </h2>
          <IconButton icon="close" label="Close dialog" onClick={onClose} />
        </div>
        {children}
      </div>
    </div>
  );
}

function trapFocus(event, container) {
  const items = container.querySelectorAll('a[href], button:not([disabled]), input, textarea, select, [tabindex]:not([tabindex="-1"])');
  if (!items.length) return;
  const first = items[0];
  const last = items[items.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
