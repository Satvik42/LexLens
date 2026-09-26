import { getAccessToken } from './auth';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

const FRIENDLY_MESSAGES = {
  NETWORK: "We couldn't reach LexLens. Check your connection and try again.",
  AUTH: 'Your session has expired. Please sign in again.',
};

async function parseError(response) {
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  const error = payload?.error ?? {};
  const code = error.code ?? (response.status === 401 ? 'UNAUTHORIZED' : 'REQUEST_FAILED');
  const message = response.status === 401 ? FRIENDLY_MESSAGES.AUTH : error.message ?? 'Something went wrong. Please try again.';
  return new ApiError(response.status, code, message, error.details);
}

/**
 * Authenticated fetch wrapper. Adds the bearer token, normalises errors into ApiError and parses JSON.
 */
export async function apiFetch(path, { method = 'GET', body, formData, signal } = {}) {
  const headers = {};
  const token = await getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
      signal,
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError(0, 'NETWORK', FRIENDLY_MESSAGES.NETWORK);
  }

  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return null;
  return response.json();
}
