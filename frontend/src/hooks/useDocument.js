import { useCallback, useEffect, useState } from 'react';
import { getDocument, getDocumentPages, getDocumentStatus } from '../services/documents';
import { useDocumentStore } from '../state/documentStore';

const POLL_INTERVAL_MS = 1500;

/**
 * Loads a document (from cache when available) and polls its status while processing.
 */
export function useDocument(documentId) {
  const cached = useDocumentStore((state) => state.documents[documentId]);
  const setDocument = useDocumentStore((state) => state.setDocument);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(!cached);

  const reload = useCallback(async () => {
    try {
      const document = await getDocument(documentId);
      setDocument(document);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [documentId, setDocument]);

  useEffect(() => {
    if (!documentId) return;
    if (!cached) reload();
  }, [documentId, cached, reload]);

  const processing = cached && ['UPLOADED', 'PROCESSING'].includes(cached.processing_status);

  useEffect(() => {
    if (!processing) return undefined;
    const timer = setInterval(async () => {
      try {
        const status = await getDocumentStatus(documentId);
        if (status.processing_status !== cached.processing_status) await reload();
      } catch (err) {
        setError(err);
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [processing, documentId, cached?.processing_status, reload]);

  return { document: cached ?? null, loading, error, reload };
}

export function useDocumentPages(documentId, enabled = true) {
  const cached = useDocumentStore((state) => state.pages[documentId]);
  const setPages = useDocumentStore((state) => state.setPages);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(!cached);

  useEffect(() => {
    if (!documentId || !enabled || cached) return;
    let cancelled = false;
    getDocumentPages(documentId)
      .then((result) => !cancelled && setPages(documentId, result.pages))
      .catch((err) => !cancelled && setError(err))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [documentId, enabled, cached, setPages]);

  return { pages: cached ?? null, loading: enabled && loading && !cached, error };
}
