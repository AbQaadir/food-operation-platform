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
  createdAt: string;
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('accessToken');
  const correlationId = crypto.randomUUID();

  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
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
