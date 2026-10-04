import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../api/client';
import { Users as UsersIcon, Shield, CheckCircle } from 'lucide-react';

interface UserItem {
  id: string;
  email: string;
  fullName: string;
  role: string;
  enabled: boolean;
  createdAt: string;
}

export const Users: React.FC = () => {
  const { data: users, isLoading, error } = useQuery<UserItem[]>({
    queryKey: ['admin-users'],
    queryFn: () => apiFetch<UserItem[]>('/api/v1/users'),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <UsersIcon className="w-6 h-6 text-emerald-600" />
            User & Role Administration
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            RBAC governance across platform operators and customer accounts
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <span className="font-semibold text-slate-800 text-sm">System Users</span>
          <span className="text-xs text-slate-500">Requires ADMIN privilege</span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-slate-500">Loading user accounts...</div>
        ) : error ? (
          <div className="p-8 text-center text-rose-500">
            Failed to load users: {(error as any).message || 'Access restricted'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-6 py-3 text-left font-medium">User</th>
                  <th className="px-6 py-3 text-left font-medium">Email</th>
                  <th className="px-6 py-3 text-left font-medium">Role</th>
                  <th className="px-6 py-3 text-left font-medium">Status</th>
                  <th className="px-6 py-3 text-left font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {(users || []).map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium text-slate-900">{u.fullName}</td>
                    <td className="px-6 py-4 text-slate-600 font-mono text-xs">{u.email}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                        <Shield className="w-3 h-3 mr-1" />
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center text-xs text-emerald-700">
                        <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-500" />
                        {u.enabled ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500 text-xs">
                      {new Date(u.createdAt).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
