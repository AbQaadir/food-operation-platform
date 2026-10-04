export interface ProblemDetail {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  instance?: string;
  errors?: Record<string, string>;
  correlationId?: string;
}

export interface PagedResponse<T> {
  content: T[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  last: boolean;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  description: string;
  categoryId: string;
  unit: string;
  price: number;
  currency: string;
  active: boolean;
  createdAt: string;
  updatedAt: string;
  version: number;
}

export interface Category {
  id: string;
  name: string;
  parentId: string | null;
  createdAt?: string;
}

export interface Warehouse {
  id: string;
  code: string;
  name: string;
  location: string;
  createdAt?: string;
}

export interface StockLevel {
  id: string;
  warehouseId: string;
  warehouseCode: string;
  warehouseName: string;
  productId: string;
  onHand: number;
  reserved: number;
  available: number;
  lowStockThreshold: number;
  version: number;
  updatedAt?: string;
}

export interface OrderItem {
  id?: string;
  productId: string;
  sku: string;
  productName: string;
  unitPrice: number;
  qty: number;
}

export interface Order {
  id: string;
  customerId: string;
  status: 'PENDING' | 'CONFIRMED' | 'CANCELLED';
  totalAmount: number;
  currency: string;
  items: OrderItem[];
  createdAt: string;
  updatedAt: string;
  version?: number;
}

export interface NotificationItem {
  id: string;
  userId?: string;
  eventType: string;
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
}

export interface UnreadCountResponse {
  unreadCount: number;
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('accessToken');
  const correlationId = crypto.randomUUID();

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('X-Correlation-Id', correlationId);

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail: ProblemDetail;
    try {
      errorDetail = await response.json();
    } catch {
      errorDetail = {
        title: response.statusText,
        status: response.status,
        detail: 'An unexpected error occurred',
      };
    }
    throw errorDetail;
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const productApi = {
  getProducts: (params?: { category?: string; q?: string; page?: number; size?: number }) => {
    const query = new URLSearchParams();
    if (params?.category) query.append('category', params.category);
    if (params?.q) query.append('q', params.q);
    if (params?.page !== undefined) query.append('page', params.page.toString());
    if (params?.size !== undefined) query.append('size', params.size.toString());

    return apiFetch<PagedResponse<Product>>(`/api/v1/products?${query.toString()}`);
  },
  getProductById: (id: string) => apiFetch<Product>(`/api/v1/products/${id}`),
  getCategories: () => apiFetch<Category[]>('/api/v1/categories'),
  createProduct: (data: Partial<Product>) =>
    apiFetch<Product>('/api/v1/products', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

export const inventoryApi = {
  getWarehouses: () => apiFetch<Warehouse[]>('/api/v1/warehouses'),
  getStockByProduct: (productId: string) => apiFetch<StockLevel[]>(`/api/v1/inventory/${productId}`),
  adjustStock: (payload: { warehouseId: string; productId: string; delta: number; reason: string }) =>
    apiFetch<StockLevel>('/api/v1/inventory/adjust', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

export const orderApi = {
  getOrders: (params?: { page?: number; size?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.page !== undefined) query.append('page', params.page.toString());
    if (params?.size !== undefined) query.append('size', params.size.toString());
    if (params?.status) query.append('status', params.status);

    return apiFetch<PagedResponse<Order>>(`/api/v1/orders?${query.toString()}`);
  },
  getOrderById: (id: string) => apiFetch<Order>(`/api/v1/orders/${id}`),
  createOrder: (
    payload: { customerId: string; items: { productId: string; qty: number }[] },
    idempotencyKey?: string
  ) => {
    const key = idempotencyKey || crypto.randomUUID();
    return apiFetch<Order>('/api/v1/orders', {
      method: 'POST',
      headers: {
        'Idempotency-Key': key,
      },
      body: JSON.stringify(payload),
    });
  },
  cancelOrder: (id: string) =>
    apiFetch<Order>(`/api/v1/orders/${id}/cancel`, {
      method: 'POST',
    }),
};

export const notificationApi = {
  getNotifications: () => apiFetch<NotificationItem[]>('/api/v1/notifications'),
  getUnreadCount: () => apiFetch<UnreadCountResponse>('/api/v1/notifications/unread-count'),
  markAllRead: () =>
    apiFetch<{ message: string }>('/api/v1/notifications/mark-read', {
      method: 'POST',
    }),
};

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ToolCallPayload {
  tool: string;
  args: Record<string, any>;
}

export interface ToolResultPayload {
  tool: string;
  result: any;
}

export const aiApi = {
  async streamChat(
    messages: ChatMessage[],
    callbacks: {
      onToolCall?: (toolCall: ToolCallPayload) => void;
      onToolResult?: (toolResult: ToolResultPayload) => void;
      onToken?: (token: string) => void;
      onDone?: () => void;
      onError?: (err: any) => void;
    }
  ) {
    try {
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-Id': crypto.randomUUID(),
        },
        body: JSON.stringify({ messages }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('No readable response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          if (!block.trim()) continue;
          let eventType = 'message';
          let dataStr = '';

          for (const line of block.split('\n')) {
            if (line.startsWith('event: ')) {
              eventType = line.replace('event: ', '').trim();
            } else if (line.startsWith('data: ')) {
              dataStr = line.replace('data: ', '').trim();
            }
          }

          if (eventType === 'tool_call' && callbacks.onToolCall) {
            try {
              callbacks.onToolCall(JSON.parse(dataStr));
            } catch {
              // ignore parse errors
            }
          } else if (eventType === 'tool_result' && callbacks.onToolResult) {
            try {
              callbacks.onToolResult(JSON.parse(dataStr));
            } catch {
              // ignore parse errors
            }
          } else if (eventType === 'token' && callbacks.onToken) {
            try {
              const parsed = JSON.parse(dataStr);
              callbacks.onToken(parsed.chunk || '');
            } catch {
              callbacks.onToken(dataStr);
            }
          } else if (eventType === 'done' && callbacks.onDone) {
            callbacks.onDone();
          }
        }
      }

      if (callbacks.onDone) {
        callbacks.onDone();
      }
    } catch (err) {
      if (callbacks.onError) {
        callbacks.onError(err);
      } else {
        console.error('SSE Stream error:', err);
      }
    }
  },
};

export const analyticsApi = {
  getDailyKpis: async (limit: number = 30) => {
    return apiFetch<{ content: any[]; totalElements: number; limit: number }>(`/api/v1/analytics/daily-kpis?limit=${limit}`);
  },
  getRealtimeSummary: async () => {
    return apiFetch<any>('/api/v1/analytics/realtime-summary');
  },
};


