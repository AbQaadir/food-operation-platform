import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productApi, orderApi, Product, Category } from '../api/client';
import {
  Search,
  AlertCircle,
  RefreshCw,
  Layers,
  ShoppingCart,
  CheckCircle2,
  XCircle,
  Tag,
  ShieldCheck,
  Check
} from 'lucide-react';

export const Products: React.FC = () => {
  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [page, setPage] = useState(0);

  // Quick Order State
  const [quickOrderProduct, setQuickOrderProduct] = useState<Product | null>(null);
  const [orderQuantity, setOrderQuantity] = useState(2);
  const [idempotencyKey, setIdempotencyKey] = useState<string>(() => crypto.randomUUID());
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Debounce search input (300ms)
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchInput);
      setPage(0);
    }, 300);
    return () => clearTimeout(handler);
  }, [searchInput]);

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: productApi.getCategories,
  });

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['products', debouncedSearch, selectedCategory, page],
    queryFn: () =>
      productApi.getProducts({
        q: debouncedSearch || undefined,
        category: selectedCategory || undefined,
        page,
        size: 10,
      }),
  });

  const placeOrderMutation = useMutation({
    mutationFn: async () => {
      if (!quickOrderProduct) throw new Error('No product selected');
      return orderApi.createOrder(
        {
          customerId: 'c0000000-0000-0000-0000-000000000001',
          items: [{ productId: quickOrderProduct.id, qty: orderQuantity }],
        },
        idempotencyKey
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
      setQuickOrderProduct(null);
      setIdempotencyKey(crypto.randomUUID());
      setToastMessage(`Order placed successfully for ${quickOrderProduct?.name}! Outbox event published.`);
      setTimeout(() => setToastMessage(null), 5000);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Product Catalog</h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse 5,000+ foodservice products with Redis sub-millisecond caching and Trigram text search.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-100 disabled:opacity-50 transition"
            title="Refresh catalog"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {toastMessage && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center space-x-3 text-emerald-800">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <p className="text-sm font-medium">{toastMessage}</p>
        </div>
      )}

      {/* Search Bar & Category Chips */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-4">
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search products by SKU, name or description (e.g. milk, cheese, bread)..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>

        {categories.length > 0 && (
          <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
            <span className="text-slate-400 flex items-center mr-1">
              <Tag className="w-3.5 h-3.5 mr-1" /> Category:
            </span>
            <button
              onClick={() => {
                setSelectedCategory('');
                setPage(0);
              }}
              className={`px-3 py-1 rounded-full font-medium transition ${
                selectedCategory === ''
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              All Categories
            </button>
            {categories.map((cat: Category) => (
              <button
                key={cat.id}
                onClick={() => {
                  setSelectedCategory(cat.name);
                  setPage(0);
                }}
                className={`px-3 py-1 rounded-full font-medium whitespace-nowrap transition ${
                  selectedCategory === cat.name
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {cat.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start space-x-3 text-red-700">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold">Failed to load products from Gateway</h3>
            <p className="text-xs mt-1 text-red-600">
              {((error as any)?.detail || (error as any)?.title || 'Check if API Gateway (:8080) and Product Service (:8082) are running.')}
            </p>
          </div>
        </div>
      )}

      {/* Products Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-500" />
            <p className="text-sm font-medium">Fetching catalog items through API Gateway...</p>
          </div>
        ) : !data || data.content.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <Layers className="w-12 h-12 text-slate-300 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-700">No products found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              No products matched your search criteria or category filter.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider text-left">
                <tr>
                  <th className="py-3 px-4">SKU</th>
                  <th className="py-3 px-4">Product Name</th>
                  <th className="py-3 px-4">Unit</th>
                  <th className="py-3 px-4">Price</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.content.map((product: Product) => (
                  <tr key={product.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-4 font-mono text-xs font-semibold text-slate-600">
                      {product.sku}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-900">{product.name}</div>
                      {product.description && (
                        <div className="text-xs text-slate-500 line-clamp-1">{product.description}</div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 capitalize">{product.unit}</td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      ${Number(product.price).toFixed(2)}{' '}
                      <span className="text-xs font-normal text-slate-400">{product.currency}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        product.active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {product.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => {
                          setQuickOrderProduct(product);
                          setIdempotencyKey(crypto.randomUUID());
                        }}
                        className="inline-flex items-center space-x-1 px-3 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-xs font-semibold transition"
                      >
                        <ShoppingCart className="w-3.5 h-3.5" />
                        <span>Order Now</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && data.totalPages > 1 && (
          <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 bg-slate-50">
            <span>
              Showing page <strong className="font-semibold text-slate-700">{data.page + 1}</strong> of{' '}
              <strong className="font-semibold text-slate-700">{data.totalPages}</strong> ({data.totalElements} total products)
            </span>
            <div className="flex space-x-2">
              <button
                disabled={data.page === 0}
                onClick={() => setPage((p) => Math.max(p - 1, 0))}
                className="px-3 py-1.5 border border-slate-300 rounded hover:bg-white disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={data.last}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 border border-slate-300 rounded hover:bg-white disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Quick Order Modal */}
      {quickOrderProduct && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 text-slate-900 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <ShoppingCart className="w-5 h-5 text-emerald-600" />
                <span>Quick Order Placement</span>
              </h2>
              <button
                onClick={() => setQuickOrderProduct(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                <span className="font-semibold text-slate-900 block text-sm">{quickOrderProduct.name}</span>
                <span className="text-xs font-mono text-slate-500">SKU: {quickOrderProduct.sku}</span>
                <div className="mt-2 text-sm font-bold text-emerald-700">
                  Unit Price: ${quickOrderProduct.price.toFixed(2)} {quickOrderProduct.currency}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Quantity</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={orderQuantity}
                  onChange={(e) => setOrderQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-slate-100 rounded-xl text-sm font-semibold">
                <span>Total Amount:</span>
                <span className="text-emerald-700 text-base">
                  ${(orderQuantity * quickOrderProduct.price).toFixed(2)}
                </span>
              </div>

              <div className="bg-emerald-50 rounded-xl p-3 border border-emerald-200">
                <div className="flex items-center space-x-1.5 text-xs text-emerald-800 font-semibold mb-1">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Idempotency-Key Header:</span>
                </div>
                <div className="font-mono text-[11px] text-emerald-900 break-all select-all bg-white/70 p-1.5 rounded border border-emerald-300">
                  {idempotencyKey}
                </div>
              </div>

              {placeOrderMutation.isError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
                  {(placeOrderMutation.error as any)?.detail || 'Order placement failed.'}
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setQuickOrderProduct(null)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => placeOrderMutation.mutate()}
                disabled={placeOrderMutation.isPending}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition flex items-center space-x-2 disabled:opacity-50"
              >
                {placeOrderMutation.isPending ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Emitting Outbox...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Confirm Order</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
