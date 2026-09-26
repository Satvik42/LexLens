import { useCallback, useEffect, useState } from 'react';
import { analyzeDocument } from '../services/analysis';
import { useDocumentStore } from '../state/documentStore';

/**
 * Runs (or retrieves the cached) analysis for an operation. Results are cached client-side and server-side,
 * so re-opening an operation never triggers a second model call.
 */
export function useAnalysis(documentId, operation, { enabled = true } = {}) {
  const result = useDocumentStore((state) => state.analyses[documentId]?.[operation] ?? null);
  const setAnalysis = useDocumentStore((state) => state.setAnalysis);
  const [status, setStatus] = useState(result ? 'ready' : 'idle');
  const [error, setError] = useState(null);

  const run = useCallback(
    async ({ force = false } = {}) => {
      setStatus('loading');
      setError(null);
      try {
        const next = await analyzeDocument(documentId, operation, { force });
        setAnalysis(documentId, operation, next);
        setStatus('ready');
      } catch (err) {
        setError(err);
        setStatus('error');
      }
    },
    [documentId, operation, setAnalysis],
  );

  useEffect(() => {
    if (enabled && !result && status === 'idle') run();
  }, [enabled, result, status, run]);

  return { result, status: result && status !== 'loading' ? 'ready' : status, error, run };
}
