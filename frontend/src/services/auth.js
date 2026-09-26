/**
 * Authentication provider abstraction.
 *
 * - Supabase mode (VITE_SUPABASE_URL + anon key): Google OAuth and email magic links via supabase-js.
 * - Development mode: the backend mints a short-lived session token (only when the server allows it).
 *
 * Only the public anon key ever reaches the browser. The backend independently verifies every token.
 */
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;
const DEV_SESSION_KEY = 'lexlens.dev-session';
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export const AUTH_MODE = SUPABASE_URL && SUPABASE_ANON_KEY ? 'supabase' : 'dev';

const supabase = AUTH_MODE === 'supabase' ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY) : null;

function readDevSession() {
  try {
    const raw = window.sessionStorage.getItem(DEV_SESSION_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw);
    if (!session.access_token || !session.expires_at || Date.now() > session.expires_at) return null;
    return session;
  } catch {
    return null;
  }
}

function decodeExpiry(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    return payload.exp ? payload.exp * 1000 : Date.now() + 60 * 60 * 1000;
  } catch {
    return Date.now() + 60 * 60 * 1000;
  }
}

export async function getAccessToken() {
  const local = readDevSession();
  if (local?.access_token) return local.access_token;
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }
  return null;
}

export async function getCurrentSession() {
  const local = readDevSession();
  if (local) return { email: local.email, provider: local.provider || 'demo' };
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    return data.session ? { email: data.session.user.email, provider: 'supabase' } : null;
  }
  return null;
}

export function onAuthChange(callback) {
  if (!supabase) return () => {};
  const { data } = supabase.auth.onAuthStateChange(() => {
    getCurrentSession().then(callback);
  });
  return () => data.subscription.unsubscribe();
}

export async function signInWithGoogle(redirectTo) {
  if (!supabase) throw new Error('Google sign-in requires Supabase configuration.');
  const { error } = await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo } });
  if (error) throw error;
}

function storeLocalSession(session, provider) {
  window.sessionStorage.setItem(
    DEV_SESSION_KEY,
    JSON.stringify({
      access_token: session.access_token,
      email: session.email,
      provider,
      expires_at: decodeExpiry(session.access_token),
    }),
  );
}

export async function fetchAuthConfig() {
  const response = await fetch(`${API_BASE}/api/auth/config`);
  if (!response.ok) return { demo_login: false, dev_login: false };
  return response.json();
}

export async function signInWithDemo() {
  const response = await fetch(`${API_BASE}/api/auth/demo-session`, { method: 'POST' });
  if (!response.ok) {
    throw new Error(response.status === 404 ? 'Demo sign-in is not enabled on the server.' : 'Sign-in failed. Please try again.');
  }
  const session = await response.json();
  storeLocalSession(session, 'demo');
  return { pending: false, email: session.email };
}

export async function signInWithEmail(email, redirectTo) {
  if (supabase) {
    const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: redirectTo } });
    if (error) throw error;
    return { pending: true };
  }
  const response = await fetch(`${API_BASE}/api/auth/dev-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    throw new Error(response.status === 404 ? 'Development sign-in is not enabled on the server.' : 'Sign-in failed. Please try again.');
  }
  const session = await response.json();
  storeLocalSession(session, 'dev');
  return { pending: false, email: session.email };
}

export async function signOut() {
  window.sessionStorage.removeItem(DEV_SESSION_KEY);
  if (supabase) {
    await supabase.auth.signOut();
  }
}
