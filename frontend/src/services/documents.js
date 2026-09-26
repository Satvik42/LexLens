import { apiFetch } from './api';

export function uploadDocument(file, { signal } = {}) {
  const formData = new FormData();
  formData.append('file', file, file.name);
  return apiFetch('/api/documents', { method: 'POST', formData, signal });
}

export function listDocuments() {
  return apiFetch('/api/documents');
}

export function getDocument(id) {
  return apiFetch(`/api/documents/${id}`);
}

export function getDocumentStatus(id) {
  return apiFetch(`/api/documents/${id}/status`);
}

export function getDocumentPages(id) {
  return apiFetch(`/api/documents/${id}/pages`);
}

export function deleteDocument(id) {
  return apiFetch(`/api/documents/${id}`, { method: 'DELETE' });
}

export function reprocessDocument(id) {
  return apiFetch(`/api/documents/${id}/process`, { method: 'POST' });
}

export function getEvidence(documentId, evidenceId) {
  return apiFetch(`/api/documents/${documentId}/evidence/${evidenceId}`);
}
