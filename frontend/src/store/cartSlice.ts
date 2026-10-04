import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface CartItem {
  productId: string;
  sku: string;
  name: string;
  unitPrice: number;
  qty: number;
}

interface CartState {
  items: CartItem[];
  idempotencyKey: string | null;
}

const initialState: CartState = {
  items: [],
  idempotencyKey: null,
};

export const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    addItem: (state, action: PayloadAction<CartItem>) => {
      const existing = state.items.find((i) => i.productId === action.payload.productId);
      if (existing) {
        existing.qty += action.payload.qty;
      } else {
        state.items.push(action.payload);
      }
    },
    removeItem: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter((i) => i.productId !== action.payload);
    },
    updateQuantity: (state, action: PayloadAction<{ productId: string; qty: number }>) => {
      const item = state.items.find((i) => i.productId === action.payload.productId);
      if (item) {
        item.qty = Math.max(1, action.payload.qty);
      }
    },
    clearCart: (state) => {
      state.items = [];
      state.idempotencyKey = null;
    },
    setIdempotencyKey: (state, action: PayloadAction<string>) => {
      state.idempotencyKey = action.payload;
    },
  },
});

export const { addItem, removeItem, updateQuantity, clearCart, setIdempotencyKey } = cartSlice.actions;
export default cartSlice.reducer;
