import { apiFetch } from './api';

export function analyzeDocument(documentId, operation, { force = false } = {}) {
  return apiFetch(`/api/documents/${documentId}/analyze`, { method: 'POST', body: { operation, force } });
}

export function listAnalyses(documentId) {
  return apiFetch(`/api/documents/${documentId}/analyses`);
}

export function askQuestion(documentId, question, conversationId) {
  return apiFetch(`/api/documents/${documentId}/questions`, {
    method: 'POST',
    body: { question, conversation_id: conversationId ?? null },
  });
}

export function getConversation(documentId, conversationId) {
  return apiFetch(`/api/documents/${documentId}/conversations/${conversationId}`);
}

export function getLawyerQuestions(documentId, { force = false } = {}) {
  return apiFetch(`/api/documents/${documentId}/lawyer-questions`, { method: 'POST', body: { force } });
}

export function createComparison(originalDocumentId, updatedDocumentId) {
  return apiFetch('/api/comparisons', {
    method: 'POST',
    body: { original_document_id: originalDocumentId, updated_document_id: updatedDocumentId },
  });
}

export function getComparison(comparisonId) {
  return apiFetch(`/api/comparisons/${comparisonId}`);
}
