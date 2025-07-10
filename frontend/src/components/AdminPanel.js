import React, { useState, useEffect } from 'react';
import axios from 'axios';
import UserManagement from './UserManagement';
import ProfitAdmin from './ProfitAdmin';
import NotificationContainer from './NotificationContainer';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPanel = ({ user, onClose }) => {
  const [activeSection, setActiveSection] = useState('dashboard');
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const { showSuccessRU, showErrorRU } = useNotifications();

  // Проверка прав доступа
  if (!user || (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN')) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="bg-surface-card border border-red-500 rounded-lg p-8 text-center">
          <h2 className="font-russo text-2xl text-red-400 mb-4">Access Denied</h2>
          <p className="font-roboto text-text-secondary">
            You don't have permission to access the admin panel
          </p>
        </div>
      </div>
    );
  }

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Получаем статистику для дашборда
      const [usersResponse, botsResponse, gamesResponse] = await Promise.allSettled([
        axios.get(`${API}/admin/users/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/bots`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/games/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setStats({
        users: usersResponse.status === 'fulfilled' ? usersResponse.value.data : { total: '—', active: '—', banned: '—' },
        bots: botsResponse.status === 'fulfilled' ? botsResponse.value.data.length : '—',
        games: gamesResponse.status === 'fulfilled' ? gamesResponse.value.data : { total: '—', active: '—', completed: '—' }
      });
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading statistics:', error);
      setLoading(false);
    }
  };

  const adminSections = [
    {
      id: 'dashboard',
      title: 'Dashboard',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v6H8V5z" />
        </svg>
      )
    },
    {
      id: 'users',
      title: 'Users',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
        </svg>
      )
    },
    {
      id: 'bots',
      title: 'Bots',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      )
    },
    {
      id: 'games',
      title: 'Games',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
      )
    },
    {
      id: 'gems',
      title: 'Gems',
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M6,2L2,8L12,22L22,8L18,2H6M6.5,3H17.5L20.5,8L12,19L3.5,8L6.5,3Z" />
        </svg>
      )
    },
    {
      id: 'settings',
      title: 'Settings',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    },
    {
      id: 'profit',
      title: 'Profit',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
        </svg>
      )
    },
    {
      id: 'analytics',
      title: 'Analytics',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      id: 'logs',
      title: 'Logs',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    }
  ];

  const StatCard = ({ title, value, icon, color = 'text-accent-primary' }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-roboto text-text-secondary text-sm">{title}</p>
          <p className={`font-rajdhani text-3xl font-bold ${color}`}>{value}</p>
        </div>
        <div className={`${color} opacity-60`}>
          {icon}
        </div>
      </div>
    </div>
  );

  const DashboardContent = () => (
    <div className="space-y-8">
      <div>
        <h2 className="font-russo text-2xl text-white mb-6">System Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Users"
            value={stats.users?.total || '—'}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            }
          />
          <StatCard
            title="Active Bots"
            value={stats.bots || '—'}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            }
            color="text-blue-400"
          />
          <StatCard
            title="Total Games"
            value={stats.games?.total || '—'}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            }
            color="text-purple-400"
          />
          <StatCard
            title="Active Games"
            value={stats.games?.active || '—'}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            color="text-orange-400"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button
              onClick={() => setActiveSection('users')}
              className="w-full px-4 py-3 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity text-left"
            >
              👥 User Management
            </button>
            <button
              onClick={() => setActiveSection('bots')}
              className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity text-left"
            >
              🤖 Bot Management
            </button>
            <button
              onClick={() => setActiveSection('games')}
              className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity text-left"
            >
              🎮 Game Monitoring
            </button>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">System Information</h3>
          <div className="space-y-3 text-text-secondary">
            <div className="flex justify-between">
              <span>Version:</span>
              <span className="text-white">GemPlay v1.0</span>
            </div>
            <div className="flex justify-between">
              <span>Status:</span>
              <span className="text-green-400">🟢 Online</span>
            </div>
            <div className="flex justify-between">
              <span>Role:</span>
              <span className="text-accent-primary font-bold">{user.role}</span>
            </div>
            <div className="flex justify-between">
              <span>Last Login:</span>
              <span className="text-white">
                {user.last_login ? new Date(user.last_login).toLocaleDateString('en-US') : 'Not specified'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return <DashboardContent />;
      case 'users':
        return <UserManagement />;
      case 'bots':
        return <div className="text-white">Bot management (in development)</div>;
      case 'games':
        return <div className="text-white">Game management (in development)</div>;
      case 'gems':
        return <div className="text-white">Gem management (in development)</div>;
      case 'profit':
        return <ProfitAdmin user={user} />;
      case 'settings':
        return <div className="text-white">System settings (in development)</div>;
      case 'analytics':
        return <div className="text-white">Analytics (in development)</div>;
      case 'logs':
        return <div className="text-white">System logs (in development)</div>;
      default:
        return <DashboardContent />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Loading admin panel...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-primary flex">
      {/* Collapsible Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-surface-sidebar border-r border-border-primary min-h-screen transition-all duration-300 flex-shrink-0`}>
        <div className="p-4">
          <div className="flex items-center justify-between mb-8">
            {!sidebarCollapsed && (
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-accent rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <div>
                  <h1 className="font-russo text-xl text-accent-primary">Admin Panel</h1>
                  <p className="font-roboto text-text-secondary text-sm">GemPlay</p>
                </div>
              </div>
            )}
            
            {/* Collapse/Expand button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="flex items-center justify-center p-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white hover:border-accent-primary hover:border-opacity-100 transition-all duration-300"
            >
              <svg 
                className={`w-4 h-4 transition-transform duration-300 ${sidebarCollapsed ? 'rotate-180' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          </div>

          {/* Back button */}
          {!sidebarCollapsed && (
            <button
              onClick={onClose}
              className="w-full flex items-center space-x-2 px-4 py-2 mb-6 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white hover:border-accent-primary hover:border-opacity-100 transition-all duration-300"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span className="text-sm font-rajdhani">Back</span>
            </button>
          )}

          {/* Menu */}
          <nav className="space-y-2">
            {adminSections.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'space-x-3'} px-4 py-3 rounded-lg transition-all duration-200 ${
                  activeSection === item.id
                    ? 'bg-accent-primary bg-opacity-20 text-accent-primary border-l-4 border-accent-primary'
                    : 'text-text-secondary hover:text-white hover:bg-surface-card'
                }`}
                title={sidebarCollapsed ? item.title : undefined}
              >
                {item.icon}
                {!sidebarCollapsed && (
                  <span className="font-rajdhani font-medium">{item.title}</span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-8 overflow-auto">
        {renderContent()}
      </div>
      
      {/* Notification Container */}
      <NotificationContainer />
    </div>
  );
};

export default AdminPanel;