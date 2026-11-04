import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch, notificationApi, NotificationItem } from '../api/client';
import { Bell, CheckCheck, Clock, CheckCircle } from 'lucide-react';

export const Notifications: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: notifications, isLoading, error } = useQuery<NotificationItem[]>({
    queryKey: ['all-notifications'],
    queryFn: async () => {
      const res = await apiFetch<any>('/api/v1/notifications?size=50');
      return Array.isArray(res) ? res : res.content || [];
    },
  });

  const markAllMutation = useMutation({
    mutationFn: () => notificationApi.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] });
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Bell className="w-6 h-6 text-emerald-600" />
            Notifications & Event Stream
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time operational alerts from Kafka messaging backbone
          </p>
        </div>
        <button
          onClick={() => markAllMutation.mutate()}
          disabled={markAllMutation.isPending}
          className="inline-flex items-center px-4 py-2 border border-slate-300 rounded-xl text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 transition shadow-sm"
        >
          <CheckCheck className="w-4 h-4 mr-2 text-emerald-600" />
          Mark all as read
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500">Loading notifications...</div>
        ) : error ? (
          <div className="p-12 text-center text-rose-500">Failed to load notifications</div>
        ) : (notifications || []).length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <CheckCircle className="w-10 h-10 mx-auto text-emerald-500 mb-2" />
            <p className="font-medium text-slate-700">All caught up!</p>
            <p className="text-xs text-slate-400 mt-1">No pending notifications at this time.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {(notifications || []).map((item) => (
              <div
                key={item.id}
                className={`p-5 flex items-start gap-4 transition hover:bg-slate-50 ${
                  !item.read ? 'bg-emerald-50/40' : ''
                }`}
              >
                <div
                  className={`p-2 rounded-xl flex-shrink-0 ${
                    !item.read ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  <Bell className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-slate-900 text-sm">{item.title}</h3>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(item.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{item.body || item.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
