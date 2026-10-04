import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from '../store';
import { setCredentials } from '../store/authSlice';
import { authApi } from '../api/client';
import { LogIn, ShieldAlert } from 'lucide-react';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('customer@foodplatform.com');
  const [password, setPassword] = useState('Customer123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await authApi.login(email, password);
      dispatch(
        setCredentials({
          user: data.user,
          accessToken: data.accessToken,
          refreshToken: data.refreshToken,
        })
      );
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillQuickRole = (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
  };

  return (
    <div className="max-w-md mx-auto my-12 bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
      <div className="flex items-center space-x-3 mb-6">
        <div className="bg-emerald-600 text-white p-3 rounded-xl shadow-sm">
          <LogIn className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Operator Sign In</h1>
          <p className="text-sm text-slate-500">Access enterprise food operations</p>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-3 text-rose-700 text-sm">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none text-slate-900 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none text-slate-900 text-sm"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 px-4 rounded-xl shadow transition duration-150 flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          {loading ? <span>Signing in...</span> : <span>Sign In</span>}
        </button>
      </form>

      <div className="mt-8 pt-6 border-t border-slate-200">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Quick Demo Accounts
        </p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <button
            type="button"
            onClick={() => fillQuickRole('admin@foodplatform.com', 'Admin123!')}
            className="p-2 border border-slate-200 rounded-lg text-left hover:border-emerald-500 hover:bg-emerald-50 transition"
          >
            <span className="font-semibold text-slate-800 block">ADMIN</span>
            <span className="text-slate-500">Full control</span>
          </button>
          <button
            type="button"
            onClick={() => fillQuickRole('manager@foodplatform.com', 'Manager123!')}
            className="p-2 border border-slate-200 rounded-lg text-left hover:border-emerald-500 hover:bg-emerald-50 transition"
          >
            <span className="font-semibold text-slate-800 block">MANAGER</span>
            <span className="text-slate-500">Orders & stock</span>
          </button>
          <button
            type="button"
            onClick={() => fillQuickRole('operator@foodplatform.com', 'Operator123!')}
            className="p-2 border border-slate-200 rounded-lg text-left hover:border-emerald-500 hover:bg-emerald-50 transition"
          >
            <span className="font-semibold text-slate-800 block">OPERATOR</span>
            <span className="text-slate-500">Warehouse hubs</span>
          </button>
          <button
            type="button"
            onClick={() => fillQuickRole('customer@foodplatform.com', 'Customer123!')}
            className="p-2 border border-slate-200 rounded-lg text-left hover:border-emerald-500 hover:bg-emerald-50 transition"
          >
            <span className="font-semibold text-slate-800 block">CUSTOMER</span>
            <span className="text-slate-500">Self-service orders</span>
          </button>
        </div>
      </div>
    </div>
  );
};
