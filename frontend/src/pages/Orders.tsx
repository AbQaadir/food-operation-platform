import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ShoppingCart,
  Plus,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Ban,
  ShieldCheck,
  Check
} from 'lucide-react';
import { orderApi, productApi, Order, Product } from '../api/client';

export const Orders: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(0);
  const [expandedOrderId, setExpandedOrderId] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [orderQuantity, setOrderQuantity] = useState<number>(1);
  const [customerId, setCustomerId] = useState<string>('c0000000-0000-0000-0000-000000000001');
  const [idempotencyKey, setIdempotencyKey] = useState<string>(() => crypto.randomUUID());
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['orders', page, statusFilter],
    queryFn: () => orderApi.getOrders({ page, size: 10, status: statusFilter || undefined }),
    refetchInterval: 8000,
  });

  const { data: productsData } = useQuery({
    queryKey: ['products-for-orders'],
    queryFn: () => productApi.getProducts({ size: 50 }),
  });

  const createOrderMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        customerId,
        items: [
          {
            productId: selectedProductId,
            qty: orderQuantity,
          },
        ],
      };
      return orderApi.createOrder(payload, idempotencyKey);
    },
    onSuccess: (newOrder) => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
      setIsCreateModalOpen(false);
      setIdempotencyKey(crypto.randomUUID());
      setSuccessMessage(`Order #${newOrder.id.slice(0, 8)} created successfully! Outbox choreography initiated.`);
      setTimeout(() => setSuccessMessage(null), 5000);
    },
  });

  const cancelOrderMutation = useMutation({
    mutationFn: (id: string) => orderApi.cancelOrder(id),
    onSuccess: (cancelled) => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setSuccessMessage(`Order #${cancelled.id.slice(0, 8)} cancelled! Stock reservation released via Saga.`);
      setTimeout(() => setSuccessMessage(null), 5000);
    },
  });

  const getStatusBadge = (status: Order['status']) => {
    switch (status) {
      case 'CONFIRMED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            CONFIRMED
          </span>
        );
      case 'PENDING':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 animate-pulse">
            <Clock className="w-3.5 h-3.5 mr-1" />
            PENDING (SAGA)
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
            <XCircle className="w-3.5 h-3.5 mr-1" />
            CANCELLED
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Order Management</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track order lifecycles, transactional outbox events, and Saga choreography.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-100 disabled:opacity-50 transition"
            title="Refresh orders"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => {
              setIsCreateModalOpen(true);
              if (!selectedProductId && productsData?.content?.length) {
                setSelectedProductId(productsData.content[0].id);
              }
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 shadow-sm transition"
          >
            <Plus className="w-4 h-4" />
            <span>Create Order</span>
          </button>
        </div>
      </div>

      {successMessage && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center space-x-3 text-emerald-800">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <p className="text-sm font-medium">{successMessage}</p>
        </div>
      )}

      {/* Status Filter Tabs */}
      <div className="flex space-x-2 border-b border-slate-200 pb-3">
        {['', 'PENDING', 'CONFIRMED', 'CANCELLED'].map((st) => (
          <button
            key={st}
            onClick={() => {
              setStatusFilter(st);
              setPage(0);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              statusFilter === st
                ? 'bg-slate-900 text-white'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {st ? st : 'ALL ORDERS'}
          </button>
        ))}
      </div>

      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start space-x-3 text-red-700">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold">Failed to fetch orders from Gateway</h3>
            <p className="text-xs mt-1 text-red-600">
              {((error as any)?.detail || (error as any)?.title || 'Check if order-service (:8084) is online.')}
            </p>
          </div>
        </div>
      )}

      {/* Orders Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-500" />
            <p className="text-sm">Querying distributed orders...</p>
          </div>
        ) : !data?.content || data.content.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <ShoppingCart className="w-10 h-10 mx-auto text-slate-300" />
            <p className="text-base font-medium text-slate-700">No orders found</p>
            <p className="text-xs text-slate-400">Click &ldquo;Create Order&rdquo; above to place an order and trigger Kafka choreography.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            <div className="bg-slate-50 grid grid-cols-12 px-6 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wider">
              <span className="col-span-3">Order ID</span>
              <span className="col-span-3">Status</span>
              <span className="col-span-2">Items</span>
              <span className="col-span-2">Total</span>
              <span className="col-span-2 text-right">Actions</span>
            </div>

            {data.content.map((order: Order) => {
              const isExpanded = expandedOrderId === order.id;
              const totalItems = order.items?.reduce((acc, it) => acc + it.qty, 0) || 0;

              return (
                <div key={order.id} className="hover:bg-slate-50/50 transition">
                  <div
                    className="grid grid-cols-12 px-6 py-4 items-center cursor-pointer text-sm"
                    onClick={() => setExpandedOrderId(isExpanded ? null : order.id)}
                  >
                    <div className="col-span-3 font-mono text-xs font-semibold text-slate-800 flex items-center space-x-1.5">
                      <span>{order.id.slice(0, 13)}...</span>
                    </div>

                    <div className="col-span-3">{getStatusBadge(order.status)}</div>

                    <div className="col-span-2 text-xs text-slate-600">
                      {totalItems} item{totalItems !== 1 ? 's' : ''}
                    </div>

                    <div className="col-span-2 font-semibold text-slate-900">
                      ${Number(order.totalAmount).toFixed(2)} {order.currency}
                    </div>

                    <div className="col-span-2 flex items-center justify-end space-x-2" onClick={(e) => e.stopPropagation()}>
                      {order.status !== 'CANCELLED' && (
                        <button
                          onClick={() => cancelOrderMutation.mutate(order.id)}
                          disabled={cancelOrderMutation.isPending}
                          className="px-2.5 py-1 text-xs border border-rose-200 text-rose-600 hover:bg-rose-50 rounded-lg font-medium transition flex items-center space-x-1"
                          title="Trigger Saga compensation to cancel and release reserved stock"
                        >
                          <Ban className="w-3 h-3" />
                          <span>Cancel</span>
                        </button>
                      )}
                      <button
                        onClick={() => setExpandedOrderId(isExpanded ? null : order.id)}
                        className="p-1 text-slate-400 hover:text-slate-600 rounded"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Items Drawer */}
                  {isExpanded && (
                    <div className="px-6 py-3 bg-slate-50/80 border-t border-slate-100 text-xs text-slate-700">
                      <div className="font-semibold text-slate-600 mb-2">Item Breakdown &amp; Stock Reservations:</div>
                      <div className="space-y-1.5">
                        {order.items?.map((item) => (
                          <div key={item.id || item.productId} className="flex items-center justify-between bg-white p-2.5 rounded-lg border border-slate-200">
                            <div>
                              <span className="font-semibold text-slate-900">{item.productName || 'Product'}</span>
                              <span className="font-mono text-[11px] text-slate-400 ml-2">SKU: {item.sku}</span>
                            </div>
                            <div className="flex items-center space-x-4">
                              <span>Qty: <strong className="text-slate-900">{item.qty}</strong></span>
                              <span>Price: <strong className="text-slate-900">${Number(item.unitPrice).toFixed(2)}</strong></span>
                              <span className="font-semibold text-emerald-700">${(item.qty * Number(item.unitPrice)).toFixed(2)}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
                        <span>Created: {new Date(order.createdAt).toLocaleString()}</span>
                        <span>Customer ID: {order.customerId}</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {data && data.totalPages > 1 && (
          <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Page {page + 1} of {data.totalPages} ({data.totalElements} total orders)
            </span>
            <div className="flex space-x-2">
              <button
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                className="px-3 py-1 text-xs border border-slate-300 rounded-md disabled:opacity-40 hover:bg-slate-100"
              >
                Previous
              </button>
              <button
                disabled={data.last}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 text-xs border border-slate-300 rounded-md disabled:opacity-40 hover:bg-slate-100"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Order Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 text-slate-900 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <ShoppingCart className="w-5 h-5 text-emerald-600" />
                <span>Create New Order</span>
              </h2>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Product</label>
                <select
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  {productsData?.content?.map((p: Product) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku}) - ${p.price.toFixed(2)}
                    </option>
                  ))}
                </select>
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

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Customer UUID</label>
                <input
                  type="text"
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm font-mono text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>

              {/* Idempotency Key Banner */}
              <div className="bg-emerald-50 rounded-xl p-3 border border-emerald-200">
                <div className="flex items-center justify-between text-xs text-emerald-800 font-semibold mb-1">
                  <span className="flex items-center space-x-1">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Idempotency-Key Header:</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => setIdempotencyKey(crypto.randomUUID())}
                    className="text-[11px] underline text-emerald-700 hover:text-emerald-900"
                  >
                    Regenerate Key
                  </button>
                </div>
                <div className="font-mono text-[11px] text-emerald-900 break-all select-all bg-white/70 p-1.5 rounded border border-emerald-300">
                  {idempotencyKey}
                </div>
                <p className="text-[10px] text-emerald-700 mt-1">
                  Guarantees exactly-once processing across network retries via Redis 24h cache.
                </p>
              </div>

              {createOrderMutation.isError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
                  {(createOrderMutation.error as any)?.detail || 'Order creation failed.'}
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(false)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => createOrderMutation.mutate()}
                disabled={createOrderMutation.isPending || !selectedProductId}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition flex items-center space-x-2 disabled:opacity-50"
              >
                {createOrderMutation.isPending ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Submitting Outbox...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Place Order</span>
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
