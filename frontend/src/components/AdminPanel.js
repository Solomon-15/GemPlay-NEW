import React, { useState, useEffect } from 'react';
import axios from 'axios';
import UserManagement from './UserManagement';
import ProfitAdmin from './ProfitAdmin';
import BetsManagement from './BetsManagement';
import RegularBotsManagement from './RegularBotsManagement';
import HumanBotsManagement from './HumanBotsManagement';
import BotSettings from './BotSettings';
import BotAnalytics from './BotAnalytics';
import InterfaceSettings from './InterfaceSettings';
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
  useEffect(() => {
    console.log('🔍 AdminPanel: Checking user access. User:', user);
    console.log('🔍 AdminPanel: Token in localStorage:', localStorage.getItem('token') ? 'EXISTS' : 'MISSING');
    
    if (!user || (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN')) {
      console.log('❌ AdminPanel: Access denied. User role:', user?.role);
    } else {
      console.log('✅ AdminPanel: Access granted. User role:', user.role);
    }
  }, [user]);

  if (!user || (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN')) {
    console.log('❌ AdminPanel: Rendering access denied component');
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="bg-surface-card border border-red-500 rounded-lg p-8 text-center">
          <h2 className="font-russo text-2xl text-red-400 mb-4">Доступ запрещён</h2>
          <p className="font-roboto text-text-secondary">
            У вас нет разрешения для доступа к админ-панели
          </p>
          <p className="font-roboto text-text-secondary mt-2">
            Текущая роль: {user?.role || 'НЕ ОПРЕДЕЛЕНА'}
          </p>
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Закрыть
          </button>
        </div>
      </div>
    );
  }

  useEffect(() => {
    fetchDashboardStats();
    
    // Настраиваем перехватчик axios для обработки ошибок 401
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          console.log('🔒 AdminPanel: Global axios interceptor caught 401 error');
          handleTokenExpired();
        }
        return Promise.reject(error);
      }
    );
    
    // Очищаем перехватчик при размонтировании компонента
    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, []);

  const handleTokenExpired = () => {
    console.log('🔒 AdminPanel: Token expired, cleaning up and closing');
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    showErrorRU('Сессия истекла. Пожалуйста, войдите снова.');
    onClose();
  };

  const fetchDashboardStats = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('🔍 AdminPanel: Fetching dashboard stats. Token exists:', !!token);
      
      if (!token) {
        console.log('❌ AdminPanel: No token found, redirecting to login');
        handleTokenExpired();
        return;
      }
      
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

      console.log('✅ AdminPanel: Dashboard stats responses:', {
        users: usersResponse.status,
        bots: botsResponse.status,
        games: gamesResponse.status
      });

      setStats({
        users: usersResponse.status === 'fulfilled' ? usersResponse.value.data : { total: '—', active: '—', banned: '—' },
        bots: botsResponse.status === 'fulfilled' ? botsResponse.value.data.length : '—',
        games: gamesResponse.status === 'fulfilled' ? gamesResponse.value.data : { total: '—', active: '—', completed: '—' }
      });
      
      setLoading(false);
    } catch (error) {
      console.error('❌ AdminPanel: Error loading statistics:', error);
      
      // Если получили 401 ошибку, токен истек
      if (error.response?.status === 401) {
        console.log('🔒 AdminPanel: Token expired (401), handling logout');
        handleTokenExpired();
        return;
      }
      
      setLoading(false);
    }
  };

  const adminSections = [
    {
      id: 'dashboard',
      title: 'Главная',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
        </svg>
      )
    },
    {
      id: 'users',
      title: 'Пользователи',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
        </svg>
      )
    },
    {
      id: 'bets',
      title: 'Ставки',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12a3 3 0 1 1 6 0 3 3 0 0 1-6 0Z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12h3m-6 0h.01" />
        </svg>
      )
    },
    {
      id: 'regular-bots',
      title: 'Обычные Боты',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3.5a1.5 1.5 0 1 1 3 0M12 3.5v2M7.5 7.5h9a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3h-9a3 3 0 0 1-3-3v-6a3 3 0 0 1 3-3ZM9 12a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm6 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3ZM8.25 18h7.5M12 1.5v2" />
        </svg>
      )
    },
    {
      id: 'human-bots',
      title: 'Human Боты',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    },
    {
      id: 'bot-settings',
      title: 'Настройки ботов',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    },
    {
      id: 'bot-analytics',
      title: 'Аналитика ботов',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      id: 'bots',
      title: 'Боты',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3.5a1.5 1.5 0 1 1 3 0M12 3.5v2M7.5 7.5h9a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3h-9a3 3 0 0 1-3-3v-6a3 3 0 0 1 3-3ZM9 12a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm6 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3ZM8.25 18h7.5M12 1.5v2" />
        </svg>
      )
    },
    {
      id: 'games',
      title: 'Игры',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
      )
    },
    {
      id: 'gems',
      title: 'Гемы',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.091 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
        </svg>
      )
    },
    {
      id: 'settings',
      title: 'Настройки',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    },
    {
      id: 'profit',
      title: 'Прибыль',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      )
    },
    {
      id: 'analytics',
      title: 'Аналитика',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      id: 'logs',
      title: 'Логи',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    }
  ];

  const StatCard = ({ title, value, icon, color = 'text-accent-primary' }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 hover:border-green-500 transition-colors duration-200">
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
        <h2 className="font-russo text-2xl text-white mb-6">Обзор системы</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Всего пользователей"
            value={stats.users?.total || '—'}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            }
          />
          <StatCard
            title="Активных ботов"
            value={stats.bots || '—'}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            }
            color="text-blue-400"
          />
          <StatCard
            title="Всего игр"
            value={stats.games?.total || '—'}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            }
            color="text-purple-400"
          />
          <StatCard
            title="Активных игр"
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
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 hover:border-green-500 transition-colors duration-200">
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

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 hover:border-green-500 transition-colors duration-200">
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

  const resetAllBets = async () => {
    if (!window.confirm('Вы уверены, что хотите сбросить все ставки? Это действие нельзя отменить.')) {
      return;
    }
    
    setResetLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/games/reset-all`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU('Все ставки успешно сброшены');
      await fetchDashboardStats(); // Обновляем статистику
    } catch (error) {
      console.error('Ошибка при сбросе ставок:', error);
      showErrorRU('Ошибка при сбросе ставок: ' + (error.response?.data?.detail || error.message));
    } finally {
      setResetLoading(false);
    }
  };

  const BetsContent = () => (
    <div className="space-y-8">
      <div>
        <h2 className="font-russo text-2xl text-white mb-6">Bet Management</h2>
        
        {/* Bet Settings */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Bet Limits</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-text-secondary text-sm mb-2">Minimum Bet Amount ($)</label>
              <input
                type="number"
                defaultValue="1"
                min="1"
                className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
              />
            </div>
            
            <div>
              <label className="block text-text-secondary text-sm mb-2">Maximum Bet Amount ($)</label>
              <input
                type="number"
                defaultValue="3000"
                min="1"
                className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
              />
            </div>
            
            <div>
              <label className="block text-text-secondary text-sm mb-2">Commission Rate (%)</label>
              <input
                type="number"
                defaultValue="6"
                min="0"
                max="100"
                step="0.1"
                className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
              />
            </div>
            
            <div>
              <label className="block text-text-secondary text-sm mb-2">Auto-Cancel Time (hours)</label>
              <input
                type="number"
                defaultValue="24"
                min="1"
                max="168"
                className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
              />
            </div>
          </div>
          
          <div className="mt-6">
            <button className="px-6 py-3 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300">
              Save Settings
            </button>
          </div>
        </div>

        {/* Current Bets Overview */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Current Bets</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Active Bets</div>
              <div className="text-2xl font-bold text-green-400">{stats.games?.active || '—'}</div>
            </div>
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Total Volume Today</div>
              <div className="text-2xl font-bold text-blue-400">$0</div>
            </div>
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Commission Earned</div>
              <div className="text-2xl font-bold text-yellow-400">$0</div>
            </div>
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Cancelled Bets</div>
              <div className="text-2xl font-bold text-red-400">0</div>
            </div>
          </div>
        </div>

        {/* Bet History Table */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Recent Bets</h3>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-border-primary">
                  <th className="pb-3 text-text-secondary font-rajdhani">Game ID</th>
                  <th className="pb-3 text-text-secondary font-rajdhani">Creator</th>
                  <th className="pb-3 text-text-secondary font-rajdhani">Amount</th>
                  <th className="pb-3 text-text-secondary font-rajdhani">Status</th>
                  <th className="pb-3 text-text-secondary font-rajdhani">Created</th>
                  <th className="pb-3 text-text-secondary font-rajdhani">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border-primary">
                  <td className="py-3 text-white font-rajdhani">#12345</td>
                  <td className="py-3 text-white">admin@gemplay.com</td>
                  <td className="py-3 text-green-400 font-rajdhani font-bold">$100.00</td>
                  <td className="py-3">
                    <span className="bg-orange-600 text-white text-xs font-rajdhani font-bold px-2 py-1 rounded">
                      WAITING
                    </span>
                  </td>
                  <td className="py-3 text-text-secondary text-sm">2 hours ago</td>
                  <td className="py-3">
                    <button className="text-red-400 hover:text-red-300 text-sm">Cancel</button>
                  </td>
                </tr>
                <tr>
                  <td className="py-3 text-text-secondary" colSpan="6">
                    No recent bets to display
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );

  const GamesContent = () => (
    <div className="space-y-8">
      <div>
        <h2 className="font-russo text-2xl text-white mb-6">Game Management</h2>
        
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Опасные действия</h3>
          <div className="bg-red-900 bg-opacity-20 border border-red-500 border-opacity-30 rounded-lg p-4">
            <div className="flex items-center space-x-3 mb-3">
              <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <h4 className="font-rajdhani text-lg font-bold text-red-400">Сбросить все ставки</h4>
            </div>
            <p className="text-text-secondary text-sm mb-4">
              Это действие отменит все активные игры, вернёт замороженные гемы и комиссию всем игрокам и ботам. 
              Это действие нельзя отменить.
            </p>
            <button
              onClick={resetAllBets}
              disabled={resetLoading}
              className={`px-6 py-3 font-rajdhani font-bold rounded-lg transition-all duration-300 ${
                resetLoading 
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                  : 'bg-red-600 hover:bg-red-700 text-white'
              }`}
            >
              {resetLoading ? (
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span>Сброс...</span>
                </div>
              ) : (
                'Сбросить все ставки'
              )}
            </button>
          </div>
        </div>
        
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Статистика игр</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Всего игр</div>
              <div className="text-2xl font-bold text-white">{stats.games?.total || '—'}</div>
            </div>
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Active Games</div>
              <div className="text-2xl font-bold text-orange-400">{stats.games?.active || '—'}</div>
            </div>
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Завершённых игр</div>
              <div className="text-2xl font-bold text-green-400">{stats.games?.completed || '—'}</div>
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
        return <UserManagement user={user} />;
      case 'bets':
        return <BetsManagement />;
      case 'regular-bots':
        return <RegularBotsManagement />;
      case 'human-bots':
        return <HumanBotsManagement />;
      case 'bot-settings':
        return <BotSettings user={user} />;
      case 'bot-analytics':
        return <BotAnalytics />;
      case 'bots':
        return <div className="text-white">Управление ботами (в разработке)</div>;
      case 'games':
        return <GamesContent />;
      case 'gems':
        return <div className="text-white">Управление гемами (в разработке)</div>;
      case 'profit':
        return <ProfitAdmin user={user} />;
      case 'settings':
        return <InterfaceSettings />;
      default:
        return <DashboardContent />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Загружается админ-панель...</div>
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
                  <h1 className="font-russo text-xl text-accent-primary">Админ-панель</h1>
                  <p className="font-roboto text-text-secondary text-sm">GemPlay</p>
                </div>
              </div>
            )}
            
            {/* Collapse/Expand button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="admin-tooltip flex items-center justify-center p-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white hover:border-accent-primary hover:border-opacity-100 transition-all duration-300"
              title={sidebarCollapsed ? "Развернуть меню" : "Свернуть меню"}
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
          {!sidebarCollapsed ? (
            <button
              onClick={onClose}
              className="w-full flex items-center space-x-2 px-4 py-2 mb-6 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white hover:border-accent-primary hover:border-opacity-100 transition-all duration-300"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span className="text-sm font-rajdhani">Назад</span>
            </button>
          ) : (
            <button
              onClick={onClose}
              className="w-full flex items-center justify-center px-2 py-2 mb-6 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white hover:border-accent-primary hover:border-opacity-100 transition-all duration-300"
              title="Назад"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
          )}

          {/* Menu */}
          <nav className="space-y-2">
            {adminSections.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`admin-tooltip w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'space-x-3'} px-4 py-3 rounded-lg transition-all duration-200 ${
                  activeSection === item.id
                    ? 'bg-accent-primary bg-opacity-20 text-accent-primary border-l-4 border-accent-primary'
                    : 'text-text-secondary hover:text-white hover:bg-surface-card'
                }`}
                title={sidebarCollapsed ? item.title : ''}
              >
                <div className="flex-shrink-0">
                  {item.icon}
                </div>
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