import { create } from 'zustand';
import type { User } from '../types/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

const getInitialUser = (): User | null => {
  try {
    const raw = localStorage.getItem('agentflow_user');
    if (!raw || raw === 'undefined' || raw === 'null') return null;
    return JSON.parse(raw);
  } catch (err) {
    console.error('[AUTH] Failed to parse initial user from localStorage:', err);
    return null;
  }
};

const getInitialToken = (): string | null => {
  const token = localStorage.getItem('agentflow_token');
  if (!token || token === 'undefined' || token === 'null') return null;
  return token;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: getInitialUser(),
  token: getInitialToken(),
  isAuthenticated: !!getInitialToken(),
  setAuth: (user, token) => {
    localStorage.setItem('agentflow_token', token);
    localStorage.setItem('agentflow_user', JSON.stringify(user));
    set({ user, token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('agentflow_token');
    localStorage.removeItem('agentflow_user');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
