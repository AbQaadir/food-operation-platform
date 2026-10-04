import React, { useEffect, useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, Check, Clock, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { notificationApi, NotificationItem } from '../api/client';

export const NotificationsPopover: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: notifications = [] } = useQuery({
    queryKey: ['notifications'],
    queryFn: notificationApi.getNotifications,
    refetchInterval: 30000,
  });

  const { data: unreadData } = useQuery({
    queryKey: ['unread-count'],
    queryFn: notificationApi.getUnreadCount,
    refetchInterval: 15000,
  });

  const unreadCount = unreadData?.unreadCount ?? 0;

  const markAllMutation = useMutation({
    mutationFn: notificationApi.markAllRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
    },
  });

  // Connect to SSE stream for real-time live events
  useEffect(() => {
    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource('/api/v1/notifications/stream');
      
      eventSource.addEventListener('notification', () => {
        queryClient.invalidateQueries({ queryKey: ['notifications'] });
        queryClient.invalidateQueries({ queryKey: ['unread-count'] });
      });

      eventSource.onerror = () => {
        // SSE auto-reconnects by default in browsers
      };
    } catch {
      // fallback to polling
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [queryClient]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getEventBadge = (eventType: string) => {
    switch (eventType) {
      case 'order.confirmed':
        return <span className="inline-flex items-center text-xs font-medium text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full"><CheckCircle className="w-3 h-3 mr-1" /> Confirmed</span>;
      case 'order.cancelled':
        return <span className="inline-flex items-center text-xs font-medium text-rose-700 bg-rose-100 px-2 py-0.5 rounded-full"><XCircle className="w-3 h-3 mr-1" /> Cancelled</span>;
      case 'inventory.low-stock':
        return <span className="inline-flex items-center text-xs font-medium text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full"><AlertTriangle className="w-3 h-3 mr-1" /> Low Stock</span>;
      default:
        return <span className="inline-flex items-center text-xs font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">{eventType}</span>;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        title="Live Notifications"
        className="relative p-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-full transition focus:outline-none"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-sm ring-2 ring-slate-900 animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl bg-white shadow-xl ring-1 ring-slate-900/10 z-50 overflow-hidden text-slate-900 animate-in fade-in zoom-in-95 duration-100">
          <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-sm text-slate-900">Notifications</span>
              {unreadCount > 0 && (
                <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-medium">
                  {unreadCount} unread
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllMutation.mutate()}
                disabled={markAllMutation.isPending}
                className="text-xs text-emerald-600 hover:text-emerald-700 font-medium flex items-center space-x-1"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Mark all read</span>
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
            {notifications.length === 0 ? (
              <div className="py-8 text-center text-slate-400 text-sm">
                <Bell className="w-8 h-8 mx-auto mb-2 opacity-40" />
                No notifications yet
              </div>
            ) : (
              notifications.map((item: NotificationItem) => (
                <div
                  key={item.id}
                  className={`p-4 transition hover:bg-slate-50 ${!item.read ? 'bg-emerald-50/40' : ''}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-xs text-slate-800">{item.title}</span>
                    {getEventBadge(item.eventType || item.type || 'DEFAULT')}
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-2 mt-1">{item.message || item.body}</p>
                  <div className="flex items-center text-[10px] text-slate-400 mt-2">
                    <Clock className="w-3 h-3 mr-1" />
                    <span>{new Date(item.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 text-center text-[11px] text-slate-400 flex items-center justify-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span>Connected to Kafka real-time stream</span>
          </div>
        </div>
      )}
    </div>
  );
};
