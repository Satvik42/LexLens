import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../state/authStore';

/** Redirects unsigned-in visitors to sign-in, preserving the destination. */
export default function RequireAuth({ children }) {
  const status = useAuthStore((state) => state.status);
  const location = useLocation();

  if (status === 'loading') {
    return (
      <div className="page-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" />
        Checking your session…
      </div>
    );
  }

  if (status !== 'signed_in') {
    const next = `${location.pathname}${location.search}`;
    return <Navigate to={`/signin?next=${encodeURIComponent(next)}`} replace />;
  }

  return children;
}
