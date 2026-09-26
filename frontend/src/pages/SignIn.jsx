import { useState } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { AlertCard, Button, Card } from '../components/ui';
import { AUTH_MODE, signInWithEmail, signInWithGoogle } from '../services/auth';
import { useAuthStore } from '../state/authStore';

export default function SignIn() {
  const status = useAuthStore((state) => state.status);
  const refresh = useAuthStore((state) => state.refresh);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const next = params.get('next') || '/upload';
  const [email, setEmail] = useState('');
  const [pending, setPending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState(null);

  if (status === 'signed_in') return <Navigate to={next} replace />;

  async function onEmail(event) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      const result = await signInWithEmail(email, `${window.location.origin}${next}`);
      if (result.pending) {
        setSent(true);
      } else {
        await refresh();
        navigate(next, { replace: true });
      }
    } catch (err) {
      setError(err.message || 'Sign-in failed. Please try again.');
    } finally {
      setPending(false);
    }
  }

  async function onDemo() {
    setEmail('demo@lexlens.app');
    setError(null);
    setPending(true);
    try {
      await signInWithEmail('demo@lexlens.app');
      await refresh();
      navigate(next, { replace: true });
    } catch (err) {
      setError(err.message || 'Development sign-in is not enabled.');
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="page container page--narrow">
      <Card>
        <p className="eyebrow">Sign in</p>
        <h1 className="page-title" style={{ marginTop: 8 }}>
          Continue to LexLens
        </h1>
        <p className="page-subtitle">Your documents stay attached to your account. We never trust a client-supplied user id.</p>
        {error ? (
          <div style={{ marginTop: 16 }}>
            <AlertCard tone="danger">{error}</AlertCard>
          </div>
        ) : null}
        {sent ? (
          <AlertCard tone="success" title="Check your email">
            If an account exists for that address, a sign-in link is on its way.
          </AlertCard>
        ) : (
          <form className="stack" style={{ marginTop: 24 }} onSubmit={onEmail}>
            {AUTH_MODE === 'supabase' ? (
              <Button
                variant="secondary"
                onClick={() => signInWithGoogle(`${window.location.origin}${next}`)}
              >
                Continue with Google
              </Button>
            ) : null}
            <label className="field">
              <span className="field__label">Email</span>
              <input
                className="input"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
              />
            </label>
            <Button type="submit" loading={pending}>
              {AUTH_MODE === 'supabase' ? 'Email me a sign-in link' : 'Continue'}
            </Button>
            {AUTH_MODE === 'dev' ? (
              <Button variant="ghost" onClick={onDemo} disabled={pending}>
                Continue with a development session
              </Button>
            ) : null}
          </form>
        )}
      </Card>
    </div>
  );
}
