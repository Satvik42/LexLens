import { create } from 'zustand';

/**
 * Client cache for documents, pages and analysis results so navigating between screens never re-fetches or
 * re-runs an analysis that is already available.
 */
export const useDocumentStore = create((set, get) => ({
  documents: {},
  pages: {},
  analyses: {},
  lawyerQuestions: {},
  conversations: {},

  setDocument(document) {
    set((state) => ({ documents: { ...state.documents, [document.id]: document } }));
  },

  removeDocument(id) {
    set((state) => {
      const documents = { ...state.documents };
      delete documents[id];
      return { documents };
    });
  },

  setPages(documentId, pages) {
    set((state) => ({ pages: { ...state.pages, [documentId]: pages } }));
  },

  setAnalysis(documentId, operation, result) {
    set((state) => ({
      analyses: { ...state.analyses, [documentId]: { ...(state.analyses[documentId] ?? {}), [operation]: result } },
    }));
  },

  getAnalysis(documentId, operation) {
    return get().analyses[documentId]?.[operation] ?? null;
  },

  setLawyerQuestions(documentId, result) {
    set((state) => ({ lawyerQuestions: { ...state.lawyerQuestions, [documentId]: result } }));
  },

  setConversation(documentId, conversation) {
    set((state) => ({ conversations: { ...state.conversations, [documentId]: conversation } }));
  },
}));
