import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface FilterState {
  productSearch: string;
  selectedCategory: string;
  orderStatus: string;
  unreadOnly: boolean;
}

const initialState: FilterState = {
  productSearch: '',
  selectedCategory: '',
  orderStatus: '',
  unreadOnly: false,
};

export const filterSlice = createSlice({
  name: 'filters',
  initialState,
  reducers: {
    setProductSearch: (state, action: PayloadAction<string>) => {
      state.productSearch = action.payload;
    },
    setSelectedCategory: (state, action: PayloadAction<string>) => {
      state.selectedCategory = action.payload;
    },
    setOrderStatus: (state, action: PayloadAction<string>) => {
      state.orderStatus = action.payload;
    },
    setUnreadOnly: (state, action: PayloadAction<boolean>) => {
      state.unreadOnly = action.payload;
    },
    resetFilters: () => initialState,
  },
});

export const { setProductSearch, setSelectedCategory, setOrderStatus, setUnreadOnly, resetFilters } =
  filterSlice.actions;
export default filterSlice.reducer;
