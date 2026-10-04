import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Warehouse as WarehouseIcon,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Package,
  SlidersHorizontal
} from 'lucide-react';
import { inventoryApi, productApi, Warehouse, StockLevel, Product } from '../api/client';

export const Inventory: React.FC = () => {
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false);
  const [adjustWarehouseId, setAdjustWarehouseId] = useState<string>('');
  const [adjustDelta, setAdjustDelta] = useState<number>(50);
  const [adjustReason, setAdjustReason] = useState<string>('INBOUND_SHIPMENT');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const { data: warehouses = [], isLoading: isLoadingWarehouses } = useQuery({
    queryKey: ['warehouses'],
    queryFn: inventoryApi.getWarehouses,
  });

  const { data: productsData } = useQuery({
    queryKey: ['products-for-inventory'],
    queryFn: () => productApi.getProducts({ size: 100 }),
  });

  // Automatically default to the first product once products load
  React.useEffect(() => {
    if (!selectedProductId && productsData?.content && productsData.content.length > 0) {
      setSelectedProductId(productsData.content[0].id);
    }
  }, [productsData, selectedProductId]);

  // Automatically default warehouse when warehouses load
  React.useEffect(() => {
    if (!adjustWarehouseId && warehouses.length > 0) {
      setAdjustWarehouseId(warehouses[0].id);
    }
  }, [warehouses, adjustWarehouseId]);

  const { data: stockLevels = [], isLoading: isLoadingStock, refetch: refetchStock, isFetching: isFetchingStock } = useQuery({
    queryKey: ['inventory', selectedProductId],
    queryFn: () => (selectedProductId ? inventoryApi.getStockByProduct(selectedProductId) : Promise.resolve([])),
    enabled: !!selectedProductId,
  });

  const adjustStockMutation = useMutation({
    mutationFn: async () => {
      return inventoryApi.adjustStock({
        warehouseId: adjustWarehouseId,
        productId: selectedProductId,
        delta: adjustDelta,
        reason: adjustReason,
      });
    },
    onSuccess: (updatedStock) => {
      queryClient.invalidateQueries({ queryKey: ['inventory', selectedProductId] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      setIsAdjustModalOpen(false);
      setToastMessage(`Stock adjusted successfully! New available: ${updatedStock.available} units.`);
      setTimeout(() => setToastMessage(null), 5000);
    },
  });

  const selectedProduct = productsData?.content?.find((p: Product) => p.id === selectedProductId);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Inventory &amp; Stock Levels</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time multi-warehouse inventory tracking with atomic concurrency control.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetchStock()}
            disabled={isFetchingStock}
            className="p-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-100 disabled:opacity-50 transition"
            title="Refresh stock"
          >
            <RefreshCw className={`w-4 h-4 ${isFetchingStock ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => {
              if (warehouses.length > 0 && !adjustWarehouseId) {
                setAdjustWarehouseId(warehouses[0].id);
              }
              setIsAdjustModalOpen(true);
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 shadow-sm transition"
          >
            <SlidersHorizontal className="w-4 h-4" />
            <span>Adjust Stock</span>
          </button>
        </div>
      </div>

      {toastMessage && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center space-x-3 text-emerald-800">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <p className="text-sm font-medium">{toastMessage}</p>
        </div>
      )}

      {/* Warehouse Hubs Grid */}
      <div>
        <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center space-x-2">
          <WarehouseIcon className="w-4 h-4 text-emerald-600" />
          <span>Fulfillment Warehouses ({warehouses.length})</span>
        </h2>
        {isLoadingWarehouses ? (
          <div className="p-6 bg-white rounded-xl border border-slate-200 text-center text-slate-400 text-sm">
            Loading warehouses...
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {warehouses.map((wh: Warehouse) => (
              <div key={wh.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                    {wh.code}
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500" title="Online" />
                </div>
                <h3 className="font-bold text-sm text-slate-900 mt-2">{wh.name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">{wh.location}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Product Stock Inspector */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-5">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-2">
            Select Product to Inspect Real-Time Multi-Warehouse Stock:
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <select
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(e.target.value)}
              className="flex-1 border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              {productsData?.content?.map((p: Product) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>
          {selectedProduct && (
            <div className="mt-2 text-xs text-slate-500 flex items-center space-x-4">
              <span>SKU: <strong className="font-mono text-slate-700">{selectedProduct.sku}</strong></span>
              <span>Unit: <strong className="text-slate-700">{selectedProduct.unit}</strong></span>
              <span>Price: <strong className="text-emerald-700">${selectedProduct.price.toFixed(2)}</strong></span>
            </div>
          )}
        </div>

        {/* Stock Breakdown */}
        {isLoadingStock ? (
          <div className="p-8 text-center text-slate-400 space-y-2">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-500" />
            <p className="text-xs">Fetching distributed stock levels...</p>
          </div>
        ) : stockLevels.length === 0 ? (
          <div className="p-8 text-center text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
            <Package className="w-8 h-8 mx-auto text-slate-300 mb-2" />
            <p className="text-sm font-medium text-slate-600">No stock records found for this product yet.</p>
            <p className="text-xs text-slate-400 mt-1">Use the &ldquo;Adjust Stock&rdquo; button above to allocate initial units.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
            <div className="bg-slate-50 grid grid-cols-12 px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wider">
              <span className="col-span-4">Warehouse</span>
              <span className="col-span-2 text-center">On Hand</span>
              <span className="col-span-2 text-center">Reserved</span>
              <span className="col-span-2 text-center">Available</span>
              <span className="col-span-2 text-center">Status</span>
            </div>

            {stockLevels.map((sl: StockLevel) => {
              const isLowStock = sl.available <= sl.lowStockThreshold;

              return (
                <div key={sl.id} className="grid grid-cols-12 px-5 py-4 items-center text-sm hover:bg-slate-50/50 transition">
                  <div className="col-span-4">
                    <span className="font-semibold text-slate-900 block">{sl.warehouseName || sl.warehouseCode}</span>
                    <span className="text-[11px] font-mono text-slate-400">Ver: {sl.version}</span>
                  </div>

                  <div className="col-span-2 text-center font-semibold text-slate-700">
                    {sl.onHand}
                  </div>

                  <div className="col-span-2 text-center font-medium text-amber-600">
                    {sl.reserved}
                  </div>

                  <div className="col-span-2 text-center font-bold text-emerald-600 text-base">
                    {sl.available}
                  </div>

                  <div className="col-span-2 text-center">
                    {isLowStock ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-100 text-amber-800">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        LOW STOCK
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                        HEALTHY
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Adjust Stock Modal */}
      {isAdjustModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 text-slate-900 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <SlidersHorizontal className="w-5 h-5 text-emerald-600" />
                <span>Adjust Stock Level</span>
              </h2>
              <button
                onClick={() => setIsAdjustModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 text-sm font-bold"
              >
                &times;
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Target Warehouse</label>
                <select
                  value={adjustWarehouseId}
                  onChange={(e) => setAdjustWarehouseId(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  {warehouses.map((wh: Warehouse) => (
                    <option key={wh.id} value={wh.id}>
                      {wh.name} ({wh.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Delta Quantity (+ or -)</label>
                <input
                  type="number"
                  value={adjustDelta}
                  onChange={(e) => setAdjustDelta(parseInt(e.target.value) || 0)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  placeholder="e.g. 50 or -10"
                />
                <p className="text-[10px] text-slate-400 mt-1">
                  Positive delta increases on-hand stock; negative delta decrements for spoilage or returns.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Movement Reason</label>
                <select
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="INBOUND_SHIPMENT">Inbound Supplier Shipment</option>
                  <option value="CYCLE_COUNT">Cycle Count Audit</option>
                  <option value="SPOILAGE">Spoilage / Damaged</option>
                  <option value="CUSTOMER_RETURN">Customer Return</option>
                </select>
              </div>

              {adjustStockMutation.isError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
                  {(adjustStockMutation.error as any)?.detail || 'Adjustment failed.'}
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsAdjustModalOpen(false)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => adjustStockMutation.mutate()}
                disabled={adjustStockMutation.isPending || !adjustWarehouseId}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition flex items-center space-x-2 disabled:opacity-50"
              >
                {adjustStockMutation.isPending ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Applying Lock...</span>
                  </>
                ) : (
                  <span>Submit Adjustment</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
