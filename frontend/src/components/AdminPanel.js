import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import UserManagement from './UserManagement';
import ProfitAdmin from './ProfitAdmin';
import BetsManagement from './BetsManagement';
import RegularBotsManagement from './RegularBotsManagement';
import HumanBotsManagement from './HumanBotsManagement';
import BotSettings from './BotSettings';
import NewBotAnalytics from './NewBotAnalytics';
import InterfaceSettings from './InterfaceSettings';
import SoundsAdmin from './SoundsAdmin';
import GemsManagement from './GemsManagement';
import NotificationContainer from './NotificationContainer';
import NotificationDemo from './NotificationDemo';
import NotificationAdmin from './NotificationAdmin';
import SecurityMonitoring from './SecurityMonitoring';
import RoleManagement from './RoleManagement';
import { useNotifications } from './NotificationContext';
import useConfirmation from '../hooks/useConfirmation';
import ConfirmationModal from './ConfirmationModal';
import Loader from './Loader';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Temporary proxy for bot-settings API
const BOT_SETTINGS_API = "http://localhost:8002/api";

const AdminPanel = ({ user, onClose }) => {
  const [activeSection, setActiveSection] = useState('dashboard');
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [dashboardStats, setDashboardStats] = useState({});
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [clearCacheLoading, setClearCacheLoading] = useState(false);
  const [navLoading, setNavLoading] = useState(false);
  const navTimerRef = useRef(null);
  const navShownAtRef = useRef(0);

  const MIN_VISIBLE_MS = 600; // минимальное время видимости спиннера
  const DELAY_MS = 1000; // задержка перед показом

  const clearNavTimer = () => {
    if (navTimerRef.current) {
      clearTimeout(navTimerRef.current);
      navTimerRef.current = null;
    }
  };

  const showNavLoaderDelayed = () => {
    clearNavTimer();
    navTimerRef.current = setTimeout(() => {
      navShownAtRef.current = Date.now();
      setNavLoading(true);
    }, DELAY_MS);
  };

  const hideNavLoaderWithMinimum = () => {
    // если таймер ещё не успел показать — просто отменяем
    if (!navLoading) {
      clearNavTimer();
      return;
    }
    const elapsed = Date.now() - navShownAtRef.current;
    const remain = Math.max(0, MIN_VISIBLE_MS - elapsed);
    clearNavTimer();
    if (remain > 0) {
      navTimerRef.current = setTimeout(() => {
        setNavLoading(false);
        clearNavTimer();
      }, remain);
    } else {
      setNavLoading(false);
    }
  };

  // States for bet volume filters
  const [betVolumeFilters, setBetVolumeFilters] = useState({
    period: 'all_time',
    startDate: '',
    endDate: ''
  });
  const [showBetVolumeFilters, setShowBetVolumeFilters] = useState(false);
  const { showSuccessRU, showErrorRU } = useNotifications();
  const { confirm, confirmationModal } = useConfirmation();


  // Scan Inconsistencies Modal state
  const [scanModalOpen, setScanModalOpen] = useState(false);
  const [scanPreset, setScanPreset] = useState('24h'); // '24h' | '7d' | '30d' | 'custom'
  const [scanStart, setScanStart] = useState(''); // datetime-local string
  const [scanEnd, setScanEnd] = useState('');   // datetime-local string
  const [scanPage, setScanPage] = useState(1);
  const [scanPageSize, setScanPageSize] = useState(50);
  const [scanLoading, setScanLoading] = useState(false);
  const [scanError, setScanError] = useState('');
  const [scanResult, setScanResult] = useState({ items: [], found: 0, checked: 0, page: 1, pages: 0, period: {} });

  const getPresetRange = () => {
    const end = new Date();
    let start = new Date(end);
    if (scanPreset === '24h') start = new Date(end.getTime() - 24 * 3600 * 1000);
    else if (scanPreset === '7d') start = new Date(end.getTime() - 7 * 24 * 3600 * 1000);
    else if (scanPreset === '30d') start = new Date(end.getTime() - 30 * 24 * 3600 * 1000);
    else if (scanPreset === 'custom') {
      if (scanStart && scanEnd) {
        return { start_ts: new Date(scanStart).toISOString(), end_ts: new Date(scanEnd).toISOString() };
      }
    }
    return { start_ts: start.toISOString(), end_ts: end.toISOString() };
  };

  const runScanFetch = async (pageOverride, pageSizeOverride) => {
    setScanLoading(true);
    setScanError('');
    try {
      const token = localStorage.getItem('token');
      const p = pageOverride || scanPage;
      const ps = pageSizeOverride || scanPageSize;
      const range = getPresetRange();
      const res = await axios.get(`${API}/admin/games/scan-inconsistencies`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { start_ts: range.start_ts, end_ts: range.end_ts, page: p, page_size: ps }
      });
      const data = res.data || {};
      setScanResult({
        items: data.items || [],
        found: data.found || 0,
        checked: data.checked || 0,
        page: data.page || p,
        pages: data.pages || 0,
        period: data.period || {}
      });
      setScanPage(data.page || p);
      setScanPageSize(ps);
    } catch (e) {
      console.error('Scan inconsistencies error', e);
      setScanError('Ошибка сканирования. Проверьте параметры и повторите.');
    } finally {
      setScanLoading(false);
    }
  };

  useEffect(() => {
    if (!user || (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN' && user.role !== 'MODERATOR')) {
      return;
    }
  }, [user]);

  if (!user || (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN' && user.role !== 'MODERATOR')) {
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

  const fetchInFlight = useRef(false);

  useEffect(() => {
    fetchDashboardStats();
  }, [betVolumeFilters]); // Re-fetch when bet volume filters change

  // Delayed loader on initial admin load
  useEffect(() => {
    if (loading) {
      showNavLoaderDelayed();
    } else {
      hideNavLoaderWithMinimum();
    }
    return () => clearNavTimer();
  }, [loading]);

  // Helper: switch section with delayed loader
  const switchSection = (sectionId) => {
    if (activeSection === sectionId) return;
    // показываем лоадер с задержкой
    showNavLoaderDelayed();
    setActiveSection(sectionId);
    // на следующем тике пробуем скрыть (если секция уже быстрая)
    setTimeout(() => hideNavLoaderWithMinimum(), 0);
  };

  // Removed handleTokenExpired - now handled by global interceptor

  const fetchDashboardStats = async () => {
    if (fetchInFlight.current) return; // защита от гонок/дубликатов
    fetchInFlight.current = true;
    try {
      const token = localStorage.getItem('token');
      
      // Prepare params for bet volume filtering
      let dashboardParams = {};
      if (betVolumeFilters.period !== 'all_time') {
        dashboardParams.bet_volume_period = betVolumeFilters.period;
      }
      if (betVolumeFilters.startDate && betVolumeFilters.endDate) {
        dashboardParams.bet_volume_start_date = betVolumeFilters.startDate;
        dashboardParams.bet_volume_end_date = betVolumeFilters.endDate;
      }
      
      const [usersResponse, botsResponse, gamesResponse, dashboardResponse] = await Promise.allSettled([
        axios.get(`${API}/admin/users/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/bots`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/games/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` },
          params: dashboardParams
        })
      ]);

      setStats({
        users: usersResponse.status === 'fulfilled' ? usersResponse.value.data : { total: '—', active: '—', banned: '—' },
        bots: botsResponse.status === 'fulfilled' ? (Array.isArray(botsResponse.value.data) ? botsResponse.value.data.length : (botsResponse.value.data?.total ?? '—')) : '—',
        games: gamesResponse.status === 'fulfilled' ? gamesResponse.value.data : { total: '—', active: '—', completed: '—' }
      });
      
      if (dashboardResponse.status === 'fulfilled') {
        setDashboardStats(dashboardResponse.value.data);
      } else {
        setDashboardStats({
          active_human_bots: '—',
          active_regular_bots: '—', 
          online_users: '—',
          active_games: '—',
          total_bet_volume: '—',
          online_bet_volume: '—'
        });
      }
      
      setLoading(false);
    } catch (error) {
      setLoading(false);
    } finally {
      fetchInFlight.current = false;
    }
  };

  const formatNumber = (num) => {
    if (num === '—' || num === undefined || num === null) return '—';
    return Number(num).toLocaleString('en-US');
  };

  const resetBetVolume = async () => {
    const confirmed = await confirm({
      title: 'Сброс объёма ставок',
      message: 'Вы уверены, что хотите сбросить общий объём ставок? Это действие удалит все игры и нельзя отменить.',
      confirmText: 'Сбросить объём ставок',
      cancelText: 'Отмена',
      type: 'danger'
    });

    if (!confirmed) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/dashboard/reset-bet-volume`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU('Объём ставок успешно сброшен');
      await fetchDashboardStats(); // Обновляем статистику
    } catch (error) {
      console.error('Ошибка при сбросе объёма ставок:', error);
      showErrorRU('Ошибка при сбросе объёма ставок: ' + (error.response?.data?.detail || error.message));
    }
  };

  const refreshStats = async () => {
    await fetchDashboardStats();
    showSuccessRU('Статистика обновлена');
  };

  const clearCache = async () => {
    if (clearCacheLoading) return;

    const confirmed = await confirm({
      title: 'Очистка кэша',
      message: 'Вы уверены, что хотите очистить серверный и локальный кэш? Это может временно замедлить работу системы.',
      type: 'warning'
    });

    if (confirmed) {
      try {
        setClearCacheLoading(true);

        // Clear server cache
        const token = localStorage.getItem('token');
        const response = await axios.post(`${API}/admin/cache/clear`, {}, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.data.success) {
          // Clear browser local cache
          // Clear localStorage (except token and essential data)
          const token = localStorage.getItem('token');
          const user = localStorage.getItem('user');
          localStorage.clear();
          if (token) localStorage.setItem('token', token);
          if (user) localStorage.setItem('user', user);

          // Clear sessionStorage
          sessionStorage.clear();

          // Clear cache storage if supported
          if ('caches' in window) {
            const cacheNames = await caches.keys();
            await Promise.all(
              cacheNames.map(cacheName => caches.delete(cacheName))
            );
          }

          // Clear memory caches by reloading page data
          await fetchDashboardStats();

          showSuccessRU(`Кэш успешно очищен! ${response.data.message}`);
        } else {
          throw new Error(response.data.message || 'Неизвестная ошибка');
        }
      } catch (error) {
        console.error('Ошибка очистки кэша:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Произошла ошибка при очистке кэша';
        showErrorRU(`Ошибка очистки кэша: ${errorMessage}`);
      } finally {
        setClearCacheLoading(false);
      }
    }
  };

  useEffect(() => {
    if (autoRefresh && activeSection === 'dashboard') {
      const interval = setInterval(fetchDashboardStats, 5000); // Обновление каждые 5 секунд
      setRefreshInterval(interval);
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh, activeSection]);

  // Permission-based section filtering
  const hasPermission = (permission) => {
    if (!user || !user.role) return false;
    
    const rolePermissions = {
      'MODERATOR': ['VIEW_ADMIN_PANEL', 'MANAGE_USERS', 'MANAGE_GAMES'],
      'ADMIN': ['VIEW_ADMIN_PANEL', 'MANAGE_USERS', 'MANAGE_GAMES', 'MANAGE_BOTS', 'MANAGE_ECONOMY', 'VIEW_ANALYTICS', 'MANAGE_SOUNDS'],
      'SUPER_ADMIN': ['ALL'] // Super admin has all permissions
    };
    
    const userPermissions = rolePermissions[user.role] || [];
    return userPermissions.includes('ALL') || userPermissions.includes(permission);
  };

  const adminSections = [
    {
      id: 'dashboard',
      title: 'Главная',
      permission: 'VIEW_ADMIN_PANEL',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
        </svg>
      )
    },
    {
      id: 'users',
      title: 'Пользователи',
      permission: 'MANAGE_USERS',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
        </svg>
      )
    },
    {
      id: 'bets',
      title: 'Ставки',
      permission: 'MANAGE_GAMES',
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
      permission: 'MANAGE_BOTS',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3.5a1.5 1.5 0 1 1 3 0M12 3.5v2M7.5 7.5h9a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3h-9a3 3 0 0 1-3-3v-6a3 3 0 0 1 3-3ZM9 12a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm6 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3ZM8.25 18h7.5M12 1.5v2" />
        </svg>
      )
    },
    {
      id: 'human-bots',
      title: 'Human Боты',
      permission: 'MANAGE_BOTS',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    },
    {
      id: 'bot-settings',
      title: 'Настройки ботов',
      permission: 'MANAGE_BOTS',
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
      permission: 'VIEW_ANALYTICS',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      id: 'bots',
      title: 'Боты',
      permission: 'MANAGE_BOTS',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3.5a1.5 1.5 0 1 1 3 0M12 3.5v2M7.5 7.5h9a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3h-9a3 3 0 0 1-3-3v-6a3 3 0 0 1 3-3ZM9 12a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm6 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3ZM8.25 18h7.5M12 1.5v2" />
        </svg>
      )
    },
    {
      id: 'games',
      title: 'Игры',
      permission: 'MANAGE_GAMES',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
      )
    },
    {
      id: 'gems',
      title: 'Гемы',
      permission: 'MANAGE_ECONOMY',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.091 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
        </svg>
      )
    },
    {
      id: 'sounds',
      title: 'Звуки',
      permission: 'MANAGE_SOUNDS',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.5c-.69 0-1.25-.56-1.25-1.25v-3.5c0-.69.56-1.25 1.25-1.25h2.25Z" />
        </svg>
      )
    },
    {
      id: 'notifications',
      title: 'Уведомления',
      permission: 'MANAGE_SOUNDS', // Group with sounds/interface management
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      )
    },
    {
      id: 'settings',
      title: 'Настройки',
      permission: 'MANAGE_SOUNDS', // Admin-level settings
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
      permission: 'MANAGE_ECONOMY',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      )
    },
    {
      id: 'analytics',
      title: 'Аналитика',
      permission: 'VIEW_ANALYTICS',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      id: 'logs',
      title: 'Логи',
      permission: 'VIEW_ANALYTICS', // Group with analytics
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    },
    {
      id: 'notification-demo',
      title: 'Notification',
      permission: 'MANAGE_SOUNDS', // Admin testing features
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5-5-5h5V12h-5l5-5 5 5h-5v5zM4 4h16v2H4V4zM4 8h16v2H4V8zM4 12h16v2H4v-2z" />
        </svg>
      )
    },
    {
      id: 'monitoring',
      title: 'Monitoring',
      permission: 'VIEW_ANALYTICS', // Group with analytics and logs
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      )
    }
  ];

  // Filter sections based on user permissions
  const filteredAdminSections = adminSections.filter(section => 
    hasPermission(section.permission)
  );

  // Add Role Management for ADMIN and SUPER_ADMIN
  if (user && (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN')) {
    filteredAdminSections.push({
      id: 'roles',
      title: 'Роли и права',
      permission: 'MANAGE_ROLES', // Special permission for role management
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
        </svg>
      )
    });
  }

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

  const StatCardWithAction = ({ title, value, icon, color = 'text-accent-primary', onAction, actionIcon, actionTitle }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 hover:border-green-500 transition-colors duration-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-roboto text-text-secondary text-sm">{title}</p>
          <p className={`font-rajdhani text-3xl font-bold ${color}`}>{value}</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={onAction}
            className="p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors duration-200"
            title={actionTitle}
          >
            {actionIcon}
          </button>
          <div className={`${color} opacity-60`}>
            {icon}
          </div>
        </div>
      </div>
    </div>
  );

  const StatCardWithFilters = ({ title, value, icon, color = 'text-accent-primary', onAction, actionIcon, actionTitle, filters, onFilterChange, showFilters, setShowFilters }) => {
    const today = new Date().toISOString().split('T')[0];
    
    return (
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden hover:border-green-500 transition-colors duration-200">
        {/* Main card content */}
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <p className="font-roboto text-text-secondary text-sm">{title}</p>
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="p-1 text-text-secondary hover:text-white rounded transition-colors"
                  title="Фильтры периода"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.707A1 1 0 013 7V4z" />
                  </svg>
                </button>
              </div>
              <p className={`font-rajdhani text-3xl font-bold ${color}`}>{value}</p>
              <p className="font-roboto text-xs text-text-secondary mt-1">{getBetVolumePeriodLabel()}</p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={onAction}
                className="p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors duration-200"
                title={actionTitle}
              >
                {actionIcon}
              </button>
              <div className={`${color} opacity-60`}>
                {icon}
              </div>
            </div>
          </div>
        </div>

        {/* Filters panel */}
        {showFilters && (
          <div className="border-t border-border-primary bg-surface-sidebar bg-opacity-30 p-4">
            <div className="space-y-4">
              {/* Period selector */}
              <div>
                <label className="block font-roboto text-text-secondary text-sm mb-2">Период</label>
                <select
                  value={filters.period}
                  onChange={(e) => onFilterChange('period', e.target.value)}
                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                >
                  <option value="all_time">За всё время</option>
                  <option value="day">За день</option>
                  <option value="week">За неделю</option>
                  <option value="month">За месяц</option>
                  <option value="quarter">За квартал</option>
                  <option value="half_year">За полугодие</option>
                  <option value="year_1">За 1 год</option>
                  <option value="year_2">За 2 года</option>
                  <option value="year_3">За 3 года</option>
                  <option value="custom">Выбрать даты</option>
                </select>
              </div>

              {/* Custom date range */}
              {filters.period === 'custom' && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-roboto text-text-secondary text-sm mb-1">С даты</label>
                    <input
                      type="date"
                      value={filters.startDate}
                      max={today}
                      onChange={(e) => onFilterChange('startDate', e.target.value)}
                      className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block font-roboto text-text-secondary text-sm mb-1">До даты</label>
                    <input
                      type="date"
                      value={filters.endDate}
                      max={today}
                      min={filters.startDate}
                      onChange={(e) => onFilterChange('endDate', e.target.value)}
                      className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const DashboardContent = () => (
    <div className="space-y-8">
      <div>
        <div className="flex justify-between items-center mb-6">
          <h2 className="font-russo text-2xl text-white">Обзор системы</h2>
          <div className="flex items-center space-x-4">
            <button
              onClick={refreshStats}
              className="p-2 bg-surface-sidebar border border-border-primary rounded-lg text-accent-primary hover:bg-surface-card transition-colors duration-200"
              title="Обновить статистику"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <button
              onClick={clearCache}
              disabled={clearCacheLoading}
              className={`px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-800 disabled:opacity-50 border border-yellow-500 rounded-lg text-white font-roboto text-sm transition-colors duration-200 flex items-center space-x-2 ${
                clearCacheLoading ? 'cursor-not-allowed' : 'cursor-pointer'
              }`}
              title="Очистить серверный и локальный кэш"
            >
              {clearCacheLoading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Очистка...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  <span>Очистить кэш</span>
                </>
              )}
            </button>
            {/* Кнопка сканирования несоответствий (ADMIN/QA only) */}
            {(user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN' || user?.role === 'MODERATOR') && (
              <button
                onClick={() => setScanModalOpen(true)}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 border border-red-500 rounded-lg text-white font-roboto text-sm transition-colors duration-200 flex items-center space-x-2"
                title="Найти потенциально неконсистентные матчи"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 18a7 7 0 100-14 7 7 0 000 14z" />
                </svg>
                <span>Сканировать несоответствия</span>
              </button>
            )}

            <div className="flex items-center space-x-2">
              <span className="text-text-secondary text-sm">Автообновление:</span>
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`w-12 h-6 rounded-full transition-colors duration-200 flex items-center ${
                  autoRefresh ? 'bg-green-500' : 'bg-gray-600'
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full transition-transform duration-200 ${
                    autoRefresh ? 'translate-x-6' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
        
        {/* Новые плитки статистики */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* 0. Всего пользователей (новая плитка) */}
          <StatCard
            title="Пользователи"
            value={formatNumber(dashboardStats.total_users)}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            }
            color="text-indigo-400"
          />
          
          {/* 6. Активных пользователей */}
          <StatCard
            title="Активных пользователей"
            value={formatNumber(dashboardStats.online_users)}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            }
            color="text-green-400"
          />

          {/* 7. Активных ставок пользователей */}
          <StatCard
            title="Активных ставок пользователей"
            value={formatNumber(dashboardStats.active_user_bets)}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 4v12l-4-2-4 2V4M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            }
            color="text-emerald-400"
          />
              
          {/* 2. Активных Human ботов */}
          <StatCard
            title="Активных Human ботов"
            value={formatNumber(dashboardStats.active_human_bots)}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            }
            color="text-blue-400"
          />
       
          {/* 3. Активных игр Human ботов */}
          <StatCard
            title="Активных игр Human ботов"
            value={formatNumber(dashboardStats.active_human_bots_games)}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            color="text-orange-400"
          />
              
          {/* 4. Активных Обычных ботов */}
          <StatCard
            title="Активных Обычных ботов"
            value={formatNumber(dashboardStats.active_regular_bots)}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            }
            color="text-cyan-400"
          />
       
          {/* 5. Активных игр Обычных ботов */}
          <StatCard
            title="Активных игр Обычных ботов"
            value={formatNumber(dashboardStats.active_regular_bots_games)}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            color="text-orange-400"
          />
              
          {/* 6. Объём ставок */}
          <StatCardWithFilters
            title="Объём ставок"
            value={formatNumber(dashboardStats.total_bet_volume)}
            icon={
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            }
            color="text-yellow-400"
            onAction={resetBetVolume}
            actionIcon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            }
            actionTitle="Сброс"
            filters={betVolumeFilters}
            onFilterChange={handleBetVolumeFilterChange}
            showFilters={showBetVolumeFilters}
            setShowFilters={setShowBetVolumeFilters}
          />
          
          {/* 7. Объём ставок онлайн */}
          <StatCard
            title="Объём ставок онлайн"
            value={formatNumber(dashboardStats.online_bet_volume)}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
            color="text-purple-400"
          />

          {/* 8. Общие активные игры */}
          <StatCard
            title="Общие активные игры"
            value={formatNumber(dashboardStats.total_active_games)}
            icon={
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            }
            color="text-teal-400"
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
            {(user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN') && (
              <button
                onClick={() => setActiveSection('roles')}
                className="w-full px-4 py-3 bg-gradient-to-r from-orange-600 to-orange-700 text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity text-left"
              >
                🛡️ Role Management
              </button>
            )}
            <button
              onClick={() => setActiveSection('human-bots')}
              className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity text-left"
            >
              🤖 Human Bot Management
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
            <div className="flex justify-between">
              <span>Auto-Refresh:</span>
              <span className={autoRefresh ? "text-green-400" : "text-red-400"}>
                {autoRefresh ? "Включено (5с)" : "Отключено"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const resetAllBets = async () => {
    const confirmed = await confirm({
      title: 'Сброс всех ставок',
      message: 'Вы уверены, что хотите сбросить все ставки? Это действие нельзя отменить.',
      confirmText: 'Сбросить все ставки',
      cancelText: 'Отмена',
      type: 'danger'
    });

    if (!confirmed) {
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

  const handleBetVolumeFilterChange = (field, value) => {
    setBetVolumeFilters(prev => ({
      ...prev,
      [field]: value,
      // Reset custom dates when period is selected
      ...(field === 'period' && value !== 'custom' ? { startDate: '', endDate: '' } : {})
    }));
  };

  const getBetVolumePeriodLabel = () => {
    const periodLabels = {
      'all_time': 'за всё время',
      'day': 'за день',
      'week': 'за неделю', 
      'month': 'за месяц',
      'quarter': 'за квартал',
      'half_year': 'за полугодие',
      'year_1': 'за 1 год',
      'year_2': 'за 2 года',
      'year_3': 'за 3 года',
      'custom': 'за выбранный период'
    };
    
    if (betVolumeFilters.period === 'custom' && betVolumeFilters.startDate && betVolumeFilters.endDate) {
      return `${betVolumeFilters.startDate} - ${betVolumeFilters.endDate}`;
    }
    
    return periodLabels[betVolumeFilters.period] || 'за всё время';
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
        return <BetsManagement user={user} />;
      case 'regular-bots':
        return <RegularBotsManagement />;
      case 'human-bots':
        return <HumanBotsManagement user={user} />;
      case 'bot-settings':
        return <BotSettings user={user} />;
      case 'bot-analytics':
        return <NewBotAnalytics />;
      case 'bots':
        return <div className="text-white">Управление ботами (в разработке)</div>;
      case 'games':
        return <GamesContent />;
      case 'gems':
        return <GemsManagement />;
      case 'sounds':
        return <SoundsAdmin user={user} />;
      case 'notifications':
        return <NotificationAdmin user={user} />;
      case 'profit':
        return <ProfitAdmin user={user} />;
      case 'settings':
        return <InterfaceSettings />;
      case 'logs':
        return <div className="text-white">Логи системы (в разработке)</div>;
      case 'notification-demo':
        return <NotificationDemo />;
      case 'monitoring':
        return <SecurityMonitoring />;
      case 'roles':
        return <RoleManagement user={user} />;
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

      {/* Scan Inconsistencies Modal */}
      {scanModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black bg-opacity-60" onClick={() => setScanModalOpen(false)} />
          <div className="relative bg-surface-card border border-border-primary rounded-xl w-full max-w-5xl mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-rajdhani text-xl text-white font-bold">Сканирование несоответствий</h3>
              <button onClick={() => setScanModalOpen(false)} className="text-text-secondary hover:text-white">✕</button>
            </div>

            {/* Controls */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="block text-text-secondary text-sm mb-2">Период</label>
                <select
                  value={scanPreset}
                  onChange={(e) => setScanPreset(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                >
                  <option value="24h">Последние 24 часа</option>
                  <option value="7d">Последние 7 дней</option>
                  <option value="30d">Последние 30 дней</option>
                  <option value="custom">Свой период</option>
                </select>
              </div>

              {scanPreset === 'custom' && (
                <>
                  <div>
                    <label className="block text-text-secondary text-sm mb-2">Начало</label>
                    <input
                      type="datetime-local"
                      value={scanStart}
                      onChange={(e) => setScanStart(e.target.value)}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-2">Конец</label>
                    <input
                      type="datetime-local"
                      value={scanEnd}
                      onChange={(e) => setScanEnd(e.target.value)}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-text-secondary text-sm mb-2">Page size</label>
                <select
                  value={scanPageSize}
                  onChange={(e) => setScanPageSize(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                >
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
            </div>

            <div className="flex items-center space-x-2 mb-4">
              <button
                onClick={() => runScanFetch(1, scanPageSize)}
                disabled={scanLoading || (scanPreset === 'custom' && (!scanStart || !scanEnd))}
                className={`px-4 py-2 rounded-lg font-rajdhani font-bold ${scanLoading ? 'bg-gray-600 text-gray-400' : 'bg-accent-primary text-white hover:opacity-90'}`}
              >
                {scanLoading ? 'Сканирую...' : 'Сканировать'}
              </button>
              {scanError && <span className="text-red-400 text-sm">{scanError}</span>}
              {scanResult?.found > 0 && (
                <span className="text-yellow-400 text-sm">Найдено: {scanResult.found} (просмотрено документов: {scanResult.checked})</span>
              )}
            </div>

            {/* Results Table */}
            <div className="overflow-x-auto border border-border-primary rounded-lg">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-border-primary text-text-secondary">
                    <th className="py-2 px-3">Completed At</th>
                    <th className="py-2 px-3">Game ID</th>
                    <th className="py-2 px-3">Creator</th>
                    <th className="py-2 px-3">Opponent</th>
                    <th className="py-2 px-3">Creator Move</th>
                    <th className="py-2 px-3">Opponent Move</th>
                    <th className="py-2 px-3">Winner</th>
                    <th className="py-2 px-3">Expected</th>
                  </tr>
                </thead>
                <tbody>
                  {(scanResult.items || []).length === 0 ? (
                    <tr>
                      <td className="py-4 px-3 text-text-secondary" colSpan="8">Нет данных</td>
                    </tr>
                  ) : (
                    scanResult.items.map((it) => (
                      <tr key={it.game_id} className="border-t border-border-primary">
                        <td className="py-2 px-3 text-white">{it.completed_at ? new Date(it.completed_at).toLocaleString() : '—'}</td>
                        <td className="py-2 px-3 text-white font-mono text-xs">{it.game_id}</td>
                        <td className="py-2 px-3 text-white font-mono text-xs">{it.creator_id}</td>
                        <td className="py-2 px-3 text-white font-mono text-xs">{it.opponent_id}</td>
                        <td className="py-2 px-3 text-white">{it.creator_move}</td>
                        <td className="py-2 px-3 text-white">{it.opponent_move}</td>
                        <td className="py-2 px-3 text-white font-mono text-xs">{it.winner_id || 'DRAW'}</td>
                        <td className="py-2 px-3 text-white font-mono text-xs">{it.expected_winner_id || 'DRAW'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {scanResult.pages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <div className="text-text-secondary text-sm">
                  Страница {scanResult.page} из {scanResult.pages}
                </div>
                <div className="space-x-2">
                  <button
                    onClick={() => runScanFetch(Math.max(1, scanResult.page - 1))}
                    disabled={scanLoading || scanResult.page <= 1}
                    className={`px-3 py-2 rounded bg-surface-sidebar border border-border-primary text-white ${scanResult.page <= 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-surface-card'}`}
                  >
                    Назад
                  </button>
                  <button
                    onClick={() => runScanFetch(Math.min(scanResult.pages, scanResult.page + 1))}
                    disabled={scanLoading || scanResult.page >= scanResult.pages}
                    className={`px-3 py-2 rounded bg-surface-sidebar border border-border-primary text-white ${scanResult.page >= scanResult.pages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-surface-card'}`}
                  >
                    Вперёд
                  </button>
                </div>
              </div>
            )}

            <div className="mt-4 text-text-secondary text-xs">
              Период: {scanResult?.period?.start ? new Date(scanResult.period.start).toLocaleString() : '—'} — {scanResult?.period?.end ? new Date(scanResult.period.end).toLocaleString() : '—'}
            </div>
          </div>
        </div>
      )}

                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
          )}

          {/* Menu */}
          <nav className="space-y-2">
            {filteredAdminSections.map((item) => (
              <button
                key={item.id}
                onClick={() => switchSection(item.id)}
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
      <div className="flex-1 p-8 overflow-auto relative">
        {renderContent()}
        {navLoading && (
          <div className="absolute inset-0 z-40 flex items-center justify-center bg-black bg-opacity-30">
            <Loader size={48} ariaLabel="Loading section" />
          </div>
        )}
      </div>
      
      {/* Notification Container */}
      <NotificationContainer />
      
      {/* Confirmation Modal */}
      <ConfirmationModal {...confirmationModal} />
    </div>
  );
};

export default AdminPanel;