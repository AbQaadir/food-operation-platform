import React from 'react';
import { Package, Warehouse, ShoppingCart, Activity, CheckCircle2, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const stats = [
    { title: 'Catalog Items', value: '5,000+', change: '+12% this month', icon: Package, link: '/products' },
    { title: 'Active Warehouses', value: '4 Hubs', change: '99.4% capacity tracked', icon: Warehouse, link: '/inventory' },
    { title: 'Orders Today', value: '1,248', change: '+18% vs yesterday', icon: ShoppingCart, link: '/orders' },
    { title: 'Gateway Uptime', value: '99.98%', change: 'Resilience4j active', icon: Activity, link: '/' },
  ];

  const microservices = [
    { name: 'API Gateway', port: ':8080', status: 'Healthy', tech: 'Spring Cloud Gateway' },
    { name: 'Identity Service', port: ':8081', status: 'Standby / Phase 2', tech: 'Spring Boot 3 / JWT' },
    { name: 'Product Service', port: ':8082', status: 'Online', tech: 'Spring Boot 3 / Redis' },
    { name: 'Inventory Service', port: ':8083', status: 'Scheduled', tech: 'Spring Boot 3 / Optimistic Lock' },
    { name: 'Order Service', port: ':8084', status: 'Scheduled', tech: 'Spring Boot 3 / Outbox' },
    { name: 'Notification Service', port: ':8085', status: 'Scheduled', tech: 'Node.js 22 / Express' },
    { name: 'AI Service', port: ':8087', status: 'Scheduled', tech: 'Python 3.12 / FastAPI' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Operations Control Center</h1>
        <p className="text-sm text-slate-500 mt-1">
          Real-time event-driven microservices platform overview and telemetry.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.title} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
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
              <Link to={item.link} className="text-xs text-slate-500 hover:text-emerald-600 font-medium mt-4 block pt-3 border-t border-slate-100">
                View Details &rarr;
              </Link>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Microservice Topology & Health</h2>
            <p className="text-xs text-slate-500">Autonomous distributed service runtime matrix</p>
          </div>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
            <CheckCircle2 className="w-3 h-3 mr-1" /> Phase 1 Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider bg-slate-50">
                <th className="py-3 px-4">Service</th>
                <th className="py-3 px-4">Endpoint</th>
                <th className="py-3 px-4">Technology</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {microservices.map((svc) => (
                <tr key={svc.name} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-semibold text-slate-800 font-sans">{svc.name}</td>
                  <td className="py-3 px-4 text-slate-600">{svc.port}</td>
                  <td className="py-3 px-4 text-slate-500 font-sans">{svc.tech}</td>
                  <td className="py-3 px-4 font-sans">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      svc.status === 'Healthy' || svc.status === 'Online'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 text-slate-700'
                    }`}>
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
