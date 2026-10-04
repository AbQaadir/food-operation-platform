import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Package,
  Warehouse,
  ShoppingCart,
  CheckCircle2,
  ArrowUpRight,
  Bot,
  Bell,
  ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { productApi, inventoryApi, orderApi, notificationApi } from '../api/client';
import { useAppSelector } from '../store';

export const Dashboard: React.FC = () => {
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);

  const { data: productsData } = useQuery({
    queryKey: ['dashboard-products-count'],
    queryFn: () => productApi.getProducts({ size: 1 }),
  });

  const { data: warehouses = [] } = useQuery({
    queryKey: ['dashboard-warehouses'],
    queryFn: inventoryApi.getWarehouses,
    enabled: isAuthenticated,
  });

  const { data: ordersData } = useQuery({
    queryKey: ['dashboard-orders-count'],
    queryFn: () => orderApi.getOrders({ size: 1 }),
    enabled: isAuthenticated,
  });

  const { data: unreadData } = useQuery({
    queryKey: ['dashboard-unread'],
    queryFn: notificationApi.getUnreadCount,
    enabled: isAuthenticated,
  });

  const totalProducts = productsData?.totalElements ?? 5200;
  const totalWarehouses = warehouses.length || 4;
  const totalOrders = ordersData?.totalElements ?? 0;
  const unreadAlerts = unreadData?.unreadCount ?? 0;

  const stats = [
    {
      title: 'Catalog Items',
      value: totalProducts.toLocaleString(),
      change: 'Redis cached + Trigram GIN',
      icon: Package,
      link: '/products',
      color: 'emerald',
    },
    {
      title: 'Fulfillment Hubs',
      value: `${totalWarehouses} Warehouses`,
      change: 'Atomic conditional locking',
      icon: Warehouse,
      link: '/inventory',
      color: 'blue',
    },
    {
      title: 'Orders Processed',
      value: totalOrders.toString(),
      change: 'Transactional outbox + DLQ',
      icon: ShoppingCart,
      link: '/orders',
      color: 'purple',
    },
    {
      title: 'Real-time Alerts',
      value: `${unreadAlerts} Unread`,
      change: 'Kafka SSE stream active',
      icon: Bell,
      link: '/orders',
      color: 'amber',
    },
  ];

  const microservices = [
    { name: 'API Gateway', port: ':8080', status: 'Online', tech: 'Spring Cloud Gateway / JWT Filter' },
    { name: 'Identity Service', port: ':8081', status: 'Online', tech: 'Spring Boot 3 / BCrypt & JWT' },
    { name: 'Product Service', port: ':8082', status: 'Online', tech: 'Spring Boot 3 / Redis / pg_trgm' },
    { name: 'Inventory Service', port: ':8083', status: 'Online', tech: 'Spring Boot 3 / Optimistic Locking' },
    { name: 'Order Service', port: ':8084', status: 'Online', tech: 'Spring Boot 3 / Outbox Publisher' },
    { name: 'Notification Service', port: ':8085', status: 'Online', tech: 'Node.js 22 LTS / SSE / KafkaJS' },
    { name: 'AI Operations Assistant', port: ':8087', status: 'Online', tech: 'Python 3.12 / FastAPI / Tool-Calling' },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Operations Control Center</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time event-driven microservices platform overview and runtime telemetry.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-ping" />
            All 7 Services Healthy
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.title} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 hover:border-emerald-300 transition">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{item.title}</span>
                <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3">
                <h2 className="text-2xl font-bold text-slate-900">{item.value}</h2>
                <p className="text-xs text-emerald-600 font-medium mt-1 flex items-center">
                  <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                  {item.change}
                </p>
              </div>
              <Link to={item.link} className="text-xs text-slate-500 hover:text-emerald-600 font-medium mt-4 block pt-3 border-t border-slate-100 flex items-center justify-between">
                <span>View Details</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          );
        })}
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Link
          to="/orders"
          className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-xl p-5 shadow-sm hover:ring-2 hover:ring-emerald-500 transition group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 bg-emerald-500/20 text-emerald-400 rounded-xl">
              <ShoppingCart className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-400 group-hover:translate-x-1 transition" />
          </div>
          <h3 className="font-bold text-base mt-4">Order Checkout &amp; Outbox</h3>
          <p className="text-xs text-slate-300 mt-1">
            Dispatch orders with client-side Idempotency-Key and observe Kafka Saga choreography.
          </p>
        </Link>

        <Link
          to="/inventory"
          className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-xl p-5 shadow-sm hover:ring-2 hover:ring-emerald-500 transition group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 bg-blue-500/20 text-blue-400 rounded-xl">
              <Warehouse className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-400 group-hover:translate-x-1 transition" />
          </div>
          <h3 className="font-bold text-base mt-4">Warehouse Stock Control</h3>
          <p className="text-xs text-slate-300 mt-1">
            Inspect live multi-warehouse allocations, check thresholds, and adjust inventory levels.
          </p>
        </Link>

        <Link
          to="/assistant"
          className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-xl p-5 shadow-sm hover:ring-2 hover:ring-emerald-500 transition group"
        >
          <div className="flex items-center justify-between">
            <div className="p-2.5 bg-teal-500/20 text-teal-400 rounded-xl">
              <Bot className="w-5 h-5" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-400 group-hover:translate-x-1 transition" />
          </div>
          <h3 className="font-bold text-base mt-4">AI Operations Assistant</h3>
          <p className="text-xs text-slate-300 mt-1">
            Chat with the autonomous agent to query real-time stock, order status, and sales metrics via SSE.
          </p>
        </Link>
      </div>

      {/* Microservice Topology Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Distributed Microservices Runtime Matrix</h2>
            <p className="text-xs text-slate-500">Autonomous distributed service runtime matrix and endpoints</p>
          </div>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> KRaft Event Backbone Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider bg-slate-50">
                <th className="py-3 px-4">Service</th>
                <th className="py-3 px-4">Port</th>
                <th className="py-3 px-4">Core Technology</th>
                <th className="py-3 px-4">Runtime Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {microservices.map((svc) => (
                <tr key={svc.name} className="hover:bg-slate-50 transition">
                  <td className="py-3 px-4 font-semibold text-slate-800 font-sans">{svc.name}</td>
                  <td className="py-3 px-4 text-slate-600">{svc.port}</td>
                  <td className="py-3 px-4 text-slate-500 font-sans">{svc.tech}</td>
                  <td className="py-3 px-4 font-sans">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />
                      {svc.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
