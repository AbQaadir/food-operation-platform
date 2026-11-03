import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface NotificationState {
  unreadCount: number;
  lastUpdated: string | null;
}

const initialState: NotificationState = {
  unreadCount: 0,
  lastUpdated: null,
};

export const notificationSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    setUnreadCount: (state, action: PayloadAction<number>) => {
      state.unreadCount = action.payload;
      state.lastUpdated = new Date().toISOString();
    },
    decrementUnread: (state) => {
      state.unreadCount = Math.max(0, state.unreadCount - 1);
    },
    clearUnread: (state) => {
      state.unreadCount = 0;
    },
  },
});

export const { setUnreadCount, decrementUnread, clearUnread } = notificationSlice.actions;
export default notificationSlice.reducer;
