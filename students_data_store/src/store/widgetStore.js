import { create } from 'zustand';
import api from '../api/client';

export const useWidgetStore = create((set) => ({
  widgets: [],
  loading: false,
  error: null,

  fetchWidgets: async (user) => {
    if (!user) {
      set({ widgets: [], loading: false, error: null });
      return;
    }
    
    set({ loading: true, error: null });
    try {
      const { data } = await api.get('/widgets/my-widgets');
      set({ widgets: data.widgets || [], error: null });
    } catch (err) {
      console.error('Failed to fetch widgets:', err);
      set({ 
        error: err.response?.data?.detail || 'Failed to load widgets',
        widgets: []
      });
    } finally {
      set({ loading: false });
    }
  },
}));

// Selective subscription selectors
export const useWidgets = () => useWidgetStore(state => state.widgets);
export const useWidgetLoading = () => useWidgetStore(state => state.loading);
export const useWidgetError = () => useWidgetStore(state => state.error);
export const useFetchWidgets = () => useWidgetStore(state => state.fetchWidgets);
