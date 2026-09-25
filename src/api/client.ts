import axios from 'axios';
import { useAuthStore } from '../store/useAuthStore';

export const apiClient = axios.create({
  baseURL: (import.meta.env && import.meta.env.VITE_API_URL) || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => {
    // Automatically unwrap backend APIResponse envelope { success: true, message: "...", data: ... }
    if (
      response.data &&
      typeof response.data === 'object' &&
      'success' in response.data &&
      'data' in response.data &&
      response.data.data !== undefined
    ) {
      response.data = response.data.data;
    }
    return response;
  },
  async (error) => {
    // Only logout if 401 is explicitly returned from auth token endpoints
    if (error.response?.status === 401 && error.config?.url?.includes('/auth/me')) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);
