import { create } from 'zustand';
import api from '../api/client';

export const useWidgetStore = create((set) => ({
  widgets: [],
  loading: false,

  fetchWidgets: async (user) => {
    if (!user) {
      set({ widgets: [], loading: false });
      return;
    }
    
    set({ loading: true });
    try {
      const { data } = await api.get('/widgets/my-widgets');
      set({ widgets: data.widgets || [] });
    } catch {
      set({ widgets: [] });
    } finally {
      set({ loading: false });
    }
  },
}));
