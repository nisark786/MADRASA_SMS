import { create } from 'zustand';
import api from '../api/client';

const getStored = (key, defaultValue) => {
  const stored = localStorage.getItem(key);
  try {
    return stored ? JSON.parse(stored) : defaultValue;
  } catch {
    return defaultValue;
  }
};

export const useAuthStore = create((set, get) => ({
  user: getStored('auth_user', null),
  permissions: getStored('permissions', []),
  
  login: async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('auth_user', JSON.stringify(data.user));
    localStorage.setItem('permissions', JSON.stringify(data.permissions));
    
    set({ user: data.user, permissions: data.permissions });
    return data;
  },
  
  logout: async () => {
    try { await api.post('/auth/logout'); } catch {}
    localStorage.clear();
    set({ user: null, permissions: [] });
  },
  
  hasPermission: (perm) => {
    const { permissions } = get();
    return permissions.includes(perm);
  },
  
  hasAnyPermission: (...perms) => {
    const { permissions } = get();
    return perms.some((p) => permissions.includes(p));
  },
}));
