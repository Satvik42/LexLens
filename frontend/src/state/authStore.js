import { create } from 'zustand';
import { AUTH_MODE, getCurrentSession, onAuthChange, signOut as providerSignOut } from '../services/auth';

/**
 * Authentication state: status is 'loading' until the provider has been consulted once.
 */
export const useAuthStore = create((set) => ({
  status: 'loading',
  session: null,
  mode: AUTH_MODE,

  async initialize() {
    const session = await getCurrentSession();
    set({ session, status: session ? 'signed_in' : 'signed_out' });
    return onAuthChange((next) => set({ session: next, status: next ? 'signed_in' : 'signed_out' }));
  },

  async refresh() {
    const session = await getCurrentSession();
    set({ session, status: session ? 'signed_in' : 'signed_out' });
  },

  async signOut() {
    await providerSignOut();
    set({ session: null, status: 'signed_out' });
  },
}));
