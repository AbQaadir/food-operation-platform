import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { productApi, Product } from '../api/client';
import { Search, Plus, AlertCircle, RefreshCw, Layers } from 'lucide-react';

export const Products: React.FC = () => {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['products', search, page],
    queryFn: () => productApi.getProducts({ q: search || undefined, page, size: 10 }),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Product Catalog</h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse and manage enterprise foodservice products and pricing.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-100 disabled:opacity-50"
            title="Refresh catalog"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 shadow-sm transition">
            <Plus className="w-4 h-4" />
            <span>Add Product</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search products by SKU, name or description..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
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

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-medium">Fetching catalog items through API Gateway...</p>
          </div>
        ) : !data || data.content.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <Layers className="w-12 h-12 text-slate-300 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-700">No products found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              No products matched your search criteria or the database is currently empty.
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
                  <tr key={product.id} className="hover:bg-slate-50">
                    <td className="py-3.5 px-4 font-mono text-xs font-medium text-slate-600">
                      {product.sku}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-900">{product.name}</div>
                      {product.description && (
                        <div className="text-xs text-slate-500 line-clamp-1">{product.description}</div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 capitalize">{product.unit}</td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      ${Number(product.price).toFixed(2)} <span className="text-xs font-normal text-slate-400">{product.currency}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        product.active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {product.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button className="text-xs text-emerald-600 hover:text-emerald-800 font-medium">
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && data.totalPages > 1 && (
          <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <span>
              Showing page <strong className="font-semibold text-slate-700">{data.page + 1}</strong> of{' '}
              <strong className="font-semibold text-slate-700">{data.totalPages}</strong> ({data.totalElements} total)
            </span>
            <div className="flex space-x-2">
              <button
                disabled={data.page === 0}
                onClick={() => setPage((p) => Math.max(p - 1, 0))}
                className="px-3 py-1.5 border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                disabled={data.last}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
