import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UiState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notificationsDrawerOpen: boolean;
}

const initialState: UiState = {
  sidebarOpen: false,
  theme: 'light',
  notificationsDrawerOpen: false,
};

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    toggleNotificationsDrawer: (state) => {
      state.notificationsDrawerOpen = !state.notificationsDrawerOpen;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
  },
});

export const { toggleSidebar, toggleNotificationsDrawer, setTheme } = uiSlice.actions;
export default uiSlice.reducer;
