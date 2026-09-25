import { apiClient } from './client';
import type { LoginResponse, RegisterResponse, User } from '../types/auth';

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>('/auth/login', { email, password });
    return res.data;
  },

  register: async (email: string, password: string, full_name?: string): Promise<RegisterResponse> => {
    const res = await apiClient.post<RegisterResponse>('/auth/register', { email, password, full_name });
    return res.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const res = await apiClient.get<User>('/users/me');
    return res.data;
  },

  getGoogleLoginUrl: async (): Promise<{ provider: string; url: string }> => {
    const res = await apiClient.get<{ provider: string; url: string }>('/auth/google/login');
    return res.data;
  },

  exchangeGoogleCode: async (code: string): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>('/auth/google/exchange', { code });
    return res.data;
  },
};


