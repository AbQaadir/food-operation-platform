import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Utensils, LayoutDashboard, Package, Warehouse, ShoppingCart, Bot, Users as UsersIcon, Bell, LogOut, LogIn } from 'lucide-react';
import { NotificationsPopover } from './NotificationsPopover';
import { useAppSelector, useAppDispatch } from '../store';
import { logout } from '../store/authSlice';

export const Header: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Products', path: '/products', icon: Package },
    { label: 'Inventory', path: '/inventory', icon: Warehouse },
    { label: 'Orders', path: '/orders', icon: ShoppingCart },
    { label: 'Notifications', path: '/notifications', icon: Bell },
    { label: 'AI Assistant', path: '/assistant', icon: Bot },
    { label: 'Users', path: '/users', icon: UsersIcon },
  ];

  return (
    <header className="bg-slate-900 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-3">
            <div className="bg-emerald-500 p-2 rounded-lg text-slate-950 font-bold">
              <Utensils className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white">FoodOps</span>
              <span className="text-xs text-emerald-400 block -mt-1 font-medium">Enterprise Platform</span>
            </div>
          </Link>

          <nav className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-800 text-emerald-400'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center space-x-4">
            <NotificationsPopover />
            {isAuthenticated && user ? (
              <div className="flex items-center space-x-3 pl-2 border-l border-slate-700">
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center font-bold text-xs text-emerald-400">
                  {user.role.substring(0, 3)}
                </div>
                <div className="text-xs">
                  <p className="font-semibold text-slate-200">{user.fullName}</p>
                  <p className="text-slate-400">{user.role}</p>
                </div>
                <button
                  onClick={handleLogout}
                  title="Sign Out"
                  className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="pl-2 border-l border-slate-700">
                <Link
                  to="/login"
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Sign In</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
