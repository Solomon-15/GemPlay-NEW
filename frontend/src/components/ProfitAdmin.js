import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { formatCurrencyWithSymbol } from '../utils/economy';
import Pagination from './Pagination';
import usePagination from '../hooks/usePagination';
import ProfitChart from './ProfitChart';
import { 
  generateMockChartData, 
  generateRevenueBreakdownData, 
  generateExpensesData, 
  generateNetProfitData 
} from '../utils/chartUtils';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProfitAdmin = ({ user }) => {
  const [stats, setStats] = useState(null);
  const [entries, setEntries] = useState([]);
  const [commissionSettings, setCommissionSettings] = useState(null);
  const [botIntegrationData, setBotIntegrationData] = useState(null);
  const [dateFilter, setDateFilter] = useState({ from: '', to: '' });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Новые состояния для категорий транзакций
  const [activeCategory, setActiveCategory] = useState('BET_COMMISSION');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // Дополнительные состояния
  const [tooltip, setTooltip] = useState({ show: false, text: '', x: 0, y: 0 });
  const [copySuccess, setCopySuccess] = useState(false);
  
  // Дополнительные фильтры
  const [playerFilter, setPlayerFilter] = useState('');
  const [amountFilter, setAmountFilter] = useState({ min: '', max: '' });
  const [transactionIdFilter, setTransactionIdFilter] = useState('');

  // Состояния для модальных окон и интерактивности
  const [activeModal, setActiveModal] = useState(null);
  const [modalData, setModalData] = useState([]);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState(null);
  const [modalPagination, setModalPagination] = useState({ current_page: 1, total_pages: 1 });
  const [periodFilter, setPeriodFilter] = useState('month'); // day, week, month, all
  const [activePeriod, setActivePeriod] = useState('month'); // Отдельное состояние для активного периода в модальных окнах
  const [expensesSettings, setExpensesSettings] = useState({ percentage: 60, manual_amount: 0 });
  const [showExpensesModal, setShowExpensesModal] = useState(false);
  
  // Состояния для настройки комиссий
  const [commissionModalSettings, setCommissionModalSettings] = useState({
    bet_commission_rate: 3,
    gift_commission_rate: 3
  });
  const [savingCommission, setSavingCommission] = useState(false);

  // Пагинация для истории прибыли
  const pagination = usePagination(1, 10);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeTab === 'history') {
      // Сброс на первую страницу при смене категории или фильтров
      if (pagination.currentPage > 1) {
        pagination.handlePageChange(1);
      } else {
        fetchEntries();
      }
    }
  }, [activeTab, activeCategory, sortBy, sortOrder, dateFilter, playerFilter, amountFilter, transactionIdFilter]);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchEntries();
    }
  }, [pagination.currentPage]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const [statsResponse, settingsResponse, botIntegrationResponse] = await Promise.all([
        axios.get(`${API}/admin/profit/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/profit/commission-settings`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/profit/bot-integration`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setStats(statsResponse.data);
      setCommissionSettings(settingsResponse.data);
      setBotIntegrationData(botIntegrationResponse.data);
    } catch (error) {
      console.error('Ошибка загрузки данных о прибыли:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEntries = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page: pagination.currentPage.toString(),
        limit: pagination.itemsPerPage.toString(),
        type: activeCategory, // Используем активную категорию
        sort_by: sortBy,
        sort_order: sortOrder
      });

      if (dateFilter.from) params.append('date_from', dateFilter.from);
      if (dateFilter.to) params.append('date_to', dateFilter.to);
      if (playerFilter) params.append('player_filter', playerFilter);
      if (amountFilter.min) params.append('amount_min', amountFilter.min);
      if (amountFilter.max) params.append('amount_max', amountFilter.max);
      if (transactionIdFilter) params.append('transaction_id', transactionIdFilter);

      const response = await axios.get(`${API}/admin/profit/entries?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setEntries(response.data.entries || []);
      pagination.updatePagination(response.data.total_count || 0);
    } catch (error) {
      console.error('Ошибка загрузки записей прибыли:', error);
    }
  };

  const getEntryTypeName = (type) => {
    const types = {
      'bet_commission': '💰 Комиссия от ставок',
      'gift_commission': '🎁 Комиссия от подарков',
      'bot_profit': '🤖 Доход от ботов',
      'BOT_REVENUE': '🤖 Доход от ботов',
      'human_bot_profit': '🤖 Доход от Human ботов',
      'penalty': '🚨 Штрафы и удержания',
      'refund': '🔄 Возвраты средств',
      'system_credit': '⚙️ Системные начисления',
      'game_commission': '💰 Комиссия с игры',
      'shop_sale': '🛒 Продажа в магазине',
      'other': '📊 Прочее'
    };
    return types[type] || type;
  };

  const getEntryTypeColor = (type) => {
    const colors = {
      'bet_commission': 'text-green-400',
      'gift_commission': 'text-purple-400',
      'bot_profit': 'text-blue-400',
      'BOT_REVENUE': 'text-blue-400',
      'human_bot_profit': 'text-cyan-400',
      'penalty': 'text-red-400',
      'refund': 'text-yellow-400',
      'system_credit': 'text-purple-400',
      'game_commission': 'text-green-400',
      'shop_sale': 'text-blue-400',
      'other': 'text-gray-400'
    };
    return colors[type] || 'text-gray-400';
  };

  // Информация о категориях
  const categories = {
    'BET_COMMISSION': {
      name: 'Комиссия от ставок',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="8" strokeWidth="2"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 9h3m-3 3h3m-3 3h3M9 12l2 2 4-4"/>
          <text x="12" y="16" textAnchor="middle" fontSize="8" fill="currentColor">%</text>
        </svg>
      ),
      color: 'green',
      description: '3% комиссия с PvP-игр'
    },
    'HUMAN_BOT_COMMISSION': {
      name: 'Комиссия от Human-ботов',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <rect x="4" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
          <rect x="14" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
          <rect x="4" y="14" width="16" height="6" strokeWidth="2" rx="1"/>
          <circle cx="17" cy="7" r="1" fill="currentColor"/>
          <circle cx="7" cy="7" r="1" fill="currentColor"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 17h8"/>
          <text x="12" y="16" textAnchor="middle" fontSize="8" fill="currentColor">%</text>
        </svg>
      ),
      color: 'cyan',
      description: '3% комиссия с игр Human-ботов'
    },
    'BOT_REVENUE': {
      name: 'Доход от Обычных ботов',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <rect x="4" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
          <rect x="14" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
          <rect x="4" y="14" width="16" height="6" strokeWidth="2" rx="1"/>
          <circle cx="17" cy="7" r="1" fill="currentColor"/>
          <circle cx="7" cy="7" r="1" fill="currentColor"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 17h8"/>
          <circle cx="18" cy="15" r="3" strokeWidth="1.5"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17 14v2l1 1"/>
        </svg>
      ),
      color: 'blue',
      description: 'Прибыль когда боты выигрывают против игроков'
    },
    'GIFT_COMMISSION': {
      name: 'Комиссия от подарков',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <rect x="3" y="8" width="18" height="12" strokeWidth="2" rx="2"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8V20"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2"/>
          <circle cx="17" cy="13" r="2" strokeWidth="1.5"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M16 12v2l1 1"/>
        </svg>
      ),
      color: 'purple',
      description: '3% за передачу гемов между игроками'
    }
  };

  const getCategoryBadgeColor = (categoryKey) => {
    const colors = {
      'BET_COMMISSION': 'bg-green-600',
      'HUMAN_BOT_COMMISSION': 'bg-cyan-600',
      'BOT_REVENUE': 'bg-blue-600', 
      'GIFT_COMMISSION': 'bg-purple-600'
    };
    return colors[categoryKey] || 'bg-gray-600';
  };

  const getCategoryBadgeOpacity = (categoryKey) => {
    const colors = {
      'BET_COMMISSION': 'bg-green-600/20',
      'HUMAN_BOT_COMMISSION': 'bg-cyan-600/20',
      'BOT_REVENUE': 'bg-blue-600/20',
      'GIFT_COMMISSION': 'bg-purple-600/20'
    };
    return colors[categoryKey] || 'bg-gray-600/20';
  };

  // Функции для копирования в буфер и tooltip
  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  const showTooltip = (e, text) => {
    setTooltip({
      show: true,
      text: text,
      x: e.clientX,
      y: e.clientY
    });
  };

  const hideTooltip = () => {
    setTooltip({ show: false, text: '', x: 0, y: 0 });
  };

  // Функции для определения типа действия и игрока
  const getActionType = (entry, category) => {
    if (category === 'BET_COMMISSION') {
      return 'Комиссия с выигрыша';
    } else if (category === 'BOT_REVENUE') {
      return 'Выигрыш бота против игрока';
    } else if (category === 'GIFT_COMMISSION') {
      return 'Комиссия с подарка';
    }
    return 'Неизвестно';
  };

  const getPlayerInfo = (entry) => {
    // Для ботов
    if (entry.bot_id) {
      return `Bot_${entry.bot_id.substring(0, 8)}`;
    }
    
    // Для пользователей - показываем имя и почту если есть
    if (entry.source_user_id) {
      // Если есть дополнительная информация о пользователе
      if (entry.user_name && entry.user_email) {
        return (
          <div>
            <div className="font-medium">{entry.user_name}</div>
            <div className="text-xs text-text-secondary">{entry.user_email}</div>
          </div>
        );
      }
      // Если нет дополнительной информации, показываем ID
      return `Игрок ${entry.source_user_id.substring(0, 8)}...`;
    }
    
    return '—';
  };

  // Функции расчёта для блоков
  const calculateTotalRevenue = (stats) => {
    return (stats.bet_commission || 0) + 
           (stats.human_bot_commission || 0) + 
           (stats.gift_commission || 0) + 
           (stats.bot_revenue || 0);
  };

  const calculateExpenses = (stats) => {
    const totalRevenue = calculateTotalRevenue(stats);
    const percentageExpenses = (totalRevenue * expensesSettings.percentage) / 100;
    return percentageExpenses + (expensesSettings.manual_amount || 0);
  };

  const calculateNetProfit = (stats) => {
    return calculateTotalRevenue(stats) - calculateExpenses(stats);
  };

  // Функции для модальных окон
  const openModal = async (type) => {
    try {
      setActiveModal(type);
      setModalError(null);
      setActivePeriod('month'); // Сброс периода при открытии модального окна
      
      // Для модальных окон с настройками комиссий загружаем текущие настройки
      if (type === 'bet_commission' || type === 'gift_commission') {
        // Инициализируем текущими значениями из commissionSettings
        setCommissionModalSettings({
          bet_commission_rate: commissionSettings?.bet_commission_rate || 3,
          gift_commission_rate: commissionSettings?.gift_commission_rate || 3
        });
        setModalData([]);
      } else {
        // Для других типов загружаем соответствующие данные
        await loadModalData(type, 'month');
      }
    } catch (error) {
      console.error('Error opening modal:', error);
      setModalError('Ошибка при открытии модального окна');
    }
  };

  // Функция для загрузки данных для модальных окон
  const loadModalData = async (type, period = activePeriod) => {
    setModalLoading(true);
    setModalError(null);
    
    try {
      const token = localStorage.getItem('token');
      
      switch (type) {
        case 'bot_revenue':
          // Загружаем данные о доходах от ботов
          const botRevenueResponse = await axios.get(`${API}/admin/profit/bot-revenue-details?period=${period}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setModalData(botRevenueResponse.data);
          break;
          
        case 'frozen_funds':
          // Загружаем данные о замороженных средствах
          const frozenFundsResponse = await axios.get(`${API}/admin/profit/frozen-funds-details?period=${period}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setModalData(frozenFundsResponse.data);
          break;
          
        case 'total_revenue':
          // Загружаем сводку по всем источникам дохода
          const totalRevenueResponse = await axios.get(`${API}/admin/profit/total-revenue-breakdown?period=${period}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setModalData(totalRevenueResponse.data);
          break;
          
        case 'expenses':
          // Загружаем данные о расходах
          const expensesResponse = await axios.get(`${API}/admin/profit/expenses-details?period=${period}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setModalData(expensesResponse.data);
          break;
          
        case 'human_bot_commission':
          // Загружаем данные о комиссиях от Human-ботов
          const humanBotCommissionResponse = await axios.get(`${API}/admin/profit/human-bot-commission-breakdown?period=${period}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setModalData(humanBotCommissionResponse.data);
          break;
          
        case 'net_profit':
          // Загружаем данные о чистой прибыли
          const netProfitResponse = await axios.get(`${API}/admin/profit/net-profit-analysis?period=${period}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setModalData(netProfitResponse.data);
          break;
          
        default:
          setModalData([]);
      }
    } catch (error) {
      console.error(`Error loading modal data for ${type}:`, error);
      setModalError('Ошибка при загрузке данных');
      setModalData([]);
    } finally {
      setModalLoading(false);
    }
  };

  // Функция для смены периода
  const handlePeriodChange = (period) => {
    setActivePeriod(period);
    if (activeModal) {
      loadModalData(activeModal, period);
    }
  };

  // Функция для сохранения настроек комиссий
  const saveCommissionSettings = async () => {
    setSavingCommission(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(`${API}/admin/profit/commission-settings`, {
        bet_commission_rate: commissionModalSettings.bet_commission_rate,
        gift_commission_rate: commissionModalSettings.gift_commission_rate
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Обновляем состояние с новыми настройками
      setCommissionSettings(response.data);
      
      // Обновляем статистику, чтобы отразить изменения
      await fetchData();
      
      // Показываем уведомление об успехе (можно добавить toast)
      console.log('Настройки комиссий успешно сохранены');
      
    } catch (error) {
      console.error('Ошибка сохранения настроек комиссий:', error);
      // Показываем уведомление об ошибке
      alert('Ошибка при сохранении настроек комиссий');
    } finally {
      setSavingCommission(false);
    }
  };

  const getModalTitle = (modalType) => {
    const titles = {
      'bet_commission': 'Комиссия от ставок',
      'human_bot_commission': 'Комиссия от Human-ботов',
      'gift_commission': 'Комиссия от подарков',
      'bot_revenue': 'Доход от ботов',
      'frozen_funds': 'Замороженные средства',
      'total_revenue': 'Общая прибыль',
      'net_profit': 'Чистая прибыль'
    };
    return titles[modalType] || 'Неизвестно';
  };

  const exportToCSV = () => {
    const headers = ['Дата', 'Время', 'Тип операции', 'Сумма', 'Источник', 'ID игрока/бота', 'Описание'];
    const csvContent = [
      headers.join(','),
      ...entries.map(entry => [
        new Date(entry.created_at).toLocaleDateString('ru-RU'),
        new Date(entry.created_at).toLocaleTimeString('ru-RU'),
        `"${getEntryTypeName(entry.type)}"`,
        entry.amount.toFixed(2),
        `"${entry.source || '—'}"`,
        entry.source_user_id || entry.bot_id || '—',
        `"${entry.description || '—'}"`
      ].join(','))
    ].join('\n');

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `profit_history_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('ru-RU'),
      time: date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-white text-xl font-roboto">Загружается...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="font-russo text-2xl text-white">Управление прибылью</h2>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 border-b border-border-primary">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 font-rajdhani font-medium transition-colors ${
            activeTab === 'overview'
              ? 'text-accent-primary border-b-2 border-accent-primary'
              : 'text-text-secondary hover:text-white'
          }`}
        >
          Обзор
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 font-rajdhani font-medium transition-colors ${
            activeTab === 'history'
              ? 'text-accent-primary border-b-2 border-accent-primary'
              : 'text-text-secondary hover:text-white'
          }`}
        >
          История прибыли
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 font-rajdhani font-medium transition-colors ${
            activeTab === 'settings'
              ? 'text-accent-primary border-b-2 border-accent-primary'
              : 'text-text-secondary hover:text-white'
          }`}
        >
          Настройки
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && stats && (
        <div className="space-y-8">
          {/* Main Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            
            {/* Комиссия от ставок */}
            <div className="bg-surface-card border border-green-500/30 rounded-lg p-6 hover:border-green-500/60 transition-colors duration-200 shadow-lg cursor-pointer" onClick={() => openModal('bet_commission')}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="8" strokeWidth="2"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 9h3m-3 3h3m-3 3h3M9 12l2 2 4-4"/>
                        <text x="12" y="16" textAnchor="middle" fontSize="8" fill="currentColor">%</text>
                      </svg>
                    </div>
                    <div className="bg-green-500/20 text-green-400 text-xs font-bold px-2 py-1 rounded-full">
                      LIVE
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Комиссия от ставок</h3>
                  <p className="font-russo text-2xl font-bold text-green-400">{formatCurrencyWithSymbol(stats.bet_commission || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">3% от выигрыша в PvP-играх</p>
                  <p className="text-xs text-green-300 mt-1">Клик для детализации</p>
                </div>
              </div>
            </div>

            {/* Комиссия от Human-ботов */}
            <div className="bg-surface-card border border-cyan-500/30 rounded-lg p-6 hover:border-cyan-500/60 transition-colors duration-200 shadow-lg cursor-pointer" onClick={() => openModal('human_bot_commission')}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <rect x="4" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
                        <rect x="14" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
                        <rect x="4" y="14" width="16" height="6" strokeWidth="2" rx="1"/>
                        <circle cx="17" cy="7" r="1" fill="currentColor"/>
                        <circle cx="7" cy="7" r="1" fill="currentColor"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 17h8"/>
                        <circle cx="18" cy="15" r="2" strokeWidth="1.5"/>
                        <text x="18" y="16" textAnchor="middle" fontSize="6" fill="currentColor">%</text>
                      </svg>
                    </div>
                    <div className="bg-cyan-500/20 text-cyan-400 text-xs font-bold px-2 py-1 rounded-full">
                      LIVE
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Комиссия от Human-ботов</h3>
                  <p className="font-russo text-2xl font-bold text-cyan-400">{formatCurrencyWithSymbol(stats.human_bot_commission || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">3% от выигрыша Human-ботов</p>
                  <p className="text-xs text-cyan-300 mt-1">Клик для детализации</p>
                </div>
              </div>
            </div>

            {/* Комиссия от подарков */}
            <div className="bg-surface-card border border-purple-500/30 rounded-lg p-6 hover:border-purple-500/60 transition-colors duration-200 shadow-lg cursor-pointer" onClick={() => openModal('gift_commission')}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <rect x="3" y="8" width="18" height="12" strokeWidth="2" rx="2"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8V20"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2"/>
                        <circle cx="17" cy="13" r="2" strokeWidth="1.5"/>
                        <text x="17" y="14" textAnchor="middle" fontSize="6" fill="currentColor">%</text>
                      </svg>
                    </div>
                    <div className="bg-purple-500/20 text-purple-400 text-xs font-bold px-2 py-1 rounded-full">
                      LIVE
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Комиссия от подарков</h3>
                  <p className="font-russo text-2xl font-bold text-purple-400">{formatCurrencyWithSymbol(stats.gift_commission || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">3% от стоимости переданных гемов</p>
                  <p className="text-xs text-purple-300 mt-1">Клик для детализации</p>
                </div>
              </div>
            </div>

            {/* Доход от ботов */}
            <div className="bg-surface-card border border-blue-500/30 rounded-lg p-6 hover:border-blue-500/60 transition-colors duration-200 shadow-lg cursor-pointer" onClick={() => openModal('bot_revenue')}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <rect x="4" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
                        <rect x="14" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
                        <rect x="4" y="14" width="16" height="6" strokeWidth="2" rx="1"/>
                        <circle cx="17" cy="7" r="1" fill="currentColor"/>
                        <circle cx="7" cy="7" r="1" fill="currentColor"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 17h8"/>
                      </svg>
                    </div>
                    <div className="bg-blue-500/20 text-blue-400 text-xs font-bold px-2 py-1 rounded-full">
                      AI
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Доход от ботов</h3>
                  <p className="font-russo text-2xl font-bold text-blue-400">{formatCurrencyWithSymbol(stats.bot_revenue || 0, true)}</p>
                  <div className="text-xs text-text-secondary mt-1">
                    {botIntegrationData && (
                      <div className="space-y-1">
                        <p>Активных ботов: {botIntegrationData.bot_stats.active_bots}</p>
                        <p>Avg Win Rate: {botIntegrationData.bot_stats.avg_win_rate?.toFixed(1) || 0}%</p>
                        <p>Сегодня: {formatCurrencyWithSymbol(botIntegrationData.bot_revenue.today || 0, true)}</p>
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-blue-300 mt-1">Клик для детализации</p>
                </div>
              </div>
            </div>

            {/* Общая прибыль */}
            <div className="bg-surface-card border border-yellow-500/30 rounded-lg p-6 hover:border-yellow-500/60 transition-colors duration-200 shadow-lg cursor-pointer" onClick={() => openModal('total_revenue')}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                      </svg>
                    </div>
                    <div className="bg-yellow-500/20 text-yellow-400 text-xs font-bold px-2 py-1 rounded-full">
                      TOTAL
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Общая прибыль</h3>
                  <p className="font-russo text-2xl font-bold text-yellow-400">{formatCurrencyWithSymbol(calculateTotalRevenue(stats), true)}</p>
                  <p className="text-xs text-text-secondary mt-1">Сумма всех источников дохода</p>
                  <p className="text-xs text-yellow-300 mt-1">Клик для детализации</p>
                </div>
              </div>
            </div>

            {/* Замороженные средства */}
            <div className="bg-surface-card border border-orange-500/30 rounded-lg p-6 hover:border-orange-500/60 transition-colors duration-200 shadow-lg cursor-pointer" onClick={() => openModal('frozen_funds')}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-orange-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    </div>
                    <div className="bg-orange-500/20 text-orange-400 text-xs font-bold px-2 py-1 rounded-full">
                      FROZEN
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Замороженные средства</h3>
                  <p className="font-russo text-2xl font-bold text-orange-400">{formatCurrencyWithSymbol(stats.frozen_funds || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">Комиссия в активных играх</p>
                  <p className="text-xs text-orange-300 mt-1">Обновляется при создании ставок</p>
                </div>
              </div>
            </div>

            {/* Расходы */}
            <div className="bg-surface-card border border-red-500/30 rounded-lg p-6 hover:border-red-500/60 transition-colors duration-200 shadow-lg cursor-pointer" onClick={() => setShowExpensesModal(true)}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-red-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="bg-red-500/20 text-red-400 text-xs font-bold px-2 py-1 rounded-full">
                      CALC
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Расходы</h3>
                  <p className="font-russo text-2xl font-bold text-red-400">{formatCurrencyWithSymbol(calculateExpenses(stats), true)}</p>
                  <p className="text-xs text-text-secondary mt-1">{expensesSettings.percentage}% от общей прибыли + дополнительные</p>
                  <p className="text-xs text-red-300 mt-1">Клик для настройки</p>
                </div>
              </div>
            </div>

            {/* Чистая прибыль */}
            <div className="bg-surface-card border border-emerald-500/30 rounded-lg p-6 hover:border-emerald-500/60 transition-colors duration-200 shadow-lg cursor-pointer" onClick={() => openModal('net_profit')}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="bg-emerald-500/20 text-emerald-400 text-xs font-bold px-2 py-1 rounded-full">
                      NET
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Чистая прибыль</h3>
                  <p className="font-russo text-2xl font-bold text-emerald-400">{formatCurrencyWithSymbol(calculateNetProfit(stats), true)}</p>
                  <p className="text-xs text-text-secondary mt-1">Общая прибыль минус расходы</p>
                  <p className="text-xs text-emerald-300 mt-1">Клик для детализации</p>
                </div>
              </div>
            </div>
            
          </div>
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          {/* Tabbed Interface для категорий */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
            {/* Табы */}
            <div className="border-b border-border-primary bg-surface-sidebar">
              <div className="flex">
                {Object.entries(categories).map(([key, category]) => (
                  <button
                    key={key}
                    onClick={() => {
                      setActiveCategory(key);
                      if (pagination.handlePageChange) {
                        pagination.handlePageChange(1);
                      }
                    }}
                    className={`px-6 py-4 font-roboto font-bold text-sm transition-all duration-200 border-b-2 flex items-center space-x-2 ${
                      activeCategory === key
                        ? (category.color === 'green' ? 'border-green-500 bg-green-500/10 text-green-400' :
                           category.color === 'cyan' ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400' :
                           category.color === 'blue' ? 'border-blue-500 bg-blue-500/10 text-blue-400' :
                           'border-purple-500 bg-purple-500/10 text-purple-400')
                        : 'border-transparent text-text-secondary hover:text-white hover:bg-surface-card'
                    }`}
                  >
                    <div className={`${
                      activeCategory === key
                        ? (category.color === 'green' ? 'text-green-400' :
                           category.color === 'cyan' ? 'text-cyan-400' :
                           category.color === 'blue' ? 'text-blue-400' :
                           'text-purple-400')
                        : 'text-text-secondary'
                    }`}>
                      {category.icon}
                    </div>
                    <span>{category.name}</span>
                    <span className={`px-2 py-1 text-xs rounded-full font-bold ${
                      activeCategory === key 
                        ? 'bg-white/20 text-white' 
                        : 'bg-surface-card text-text-secondary'
                    }`}>
                      {activeCategory === key ? entries.length : '•'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Фильтры и управление */}
            <div className="p-4 bg-surface-sidebar border-b border-border-primary">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-3 lg:space-y-0">
                <div className="flex items-center space-x-3">
                  <h3 className="font-rajdhani text-lg font-bold text-white flex items-center space-x-2">
                    <div className={`${
                      categories[activeCategory]?.color === 'green' ? 'text-green-400' :
                      categories[activeCategory]?.color === 'cyan' ? 'text-cyan-400' :
                      categories[activeCategory]?.color === 'blue' ? 'text-blue-400' :
                      categories[activeCategory]?.color === 'purple' ? 'text-purple-400' : 'text-gray-400'
                    }`}>
                      {categories[activeCategory]?.icon}
                    </div>
                    <span>{categories[activeCategory]?.name || 'Неизвестная категория'}</span>
                  </h3>
                  <span className="text-text-secondary text-sm">
                    ({entries.length} записей)
                  </span>
                </div>
                
                <div className="flex flex-wrap items-center gap-3">
                  {/* Сортировка */}
                  <div className="flex items-center space-x-2">
                    <span className="text-text-secondary text-sm">Сортировка:</span>
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="bg-surface-card border border-border-primary rounded-lg px-3 py-1 text-white text-sm focus:outline-none focus:border-accent-primary"
                    >
                      <option value="date">По дате</option>
                      <option value="amount">По сумме</option>
                      <option value="source">По источнику</option>
                    </select>
                    
                    <button
                      onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                      className="px-2 py-1 bg-surface-card border border-border-primary rounded text-white hover:bg-surface-sidebar transition-colors text-sm"
                      title={sortOrder === 'asc' ? 'По возрастанию' : 'По убыванию'}
                    >
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </button>
                  </div>
                  
                  {/* Экспорт */}
                  <button
                    onClick={exportToCSV}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white font-rajdhani font-bold rounded text-sm transition-colors"
                  >
                    📥 CSV
                  </button>
                </div>
              </div>
              
              {/* Расширенные фильтры */}
              <div className="p-4 bg-surface-card border-b border-border-primary">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Фильтр по периоду */}
                  <div>
                    <label className="block text-text-secondary text-sm mb-2">Период</label>
                    <div className="flex space-x-2">
                      <input
                        type="date"
                        value={dateFilter.from}
                        onChange={(e) => setDateFilter(prev => ({ ...prev, from: e.target.value }))}
                        className="flex-1 bg-surface-sidebar border border-border-primary rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-accent-primary"
                        placeholder="От"
                      />
                      <input
                        type="date"
                        value={dateFilter.to}
                        onChange={(e) => setDateFilter(prev => ({ ...prev, to: e.target.value }))}
                        className="flex-1 bg-surface-sidebar border border-border-primary rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-accent-primary"
                        placeholder="До"
                      />
                    </div>
                  </div>
                  
                  {/* Фильтр по игроку/боту */}
                  <div>
                    <label className="block text-text-secondary text-sm mb-2">Игрок/Бот</label>
                    <input
                      type="text"
                      value={playerFilter}
                      onChange={(e) => setPlayerFilter(e.target.value)}
                      className="w-full bg-surface-sidebar border border-border-primary rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-accent-primary"
                      placeholder="Имя, почта или ID"
                    />
                  </div>
                  
                  {/* Фильтр по сумме */}
                  <div>
                    <label className="block text-text-secondary text-sm mb-2">Сумма ($)</label>
                    <div className="flex space-x-2">
                      <input
                        type="number"
                        value={amountFilter.min}
                        onChange={(e) => setAmountFilter(prev => ({ ...prev, min: e.target.value }))}
                        className="flex-1 bg-surface-sidebar border border-border-primary rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-accent-primary"
                        placeholder="Мин"
                        step="0.01"
                      />
                      <input
                        type="number"
                        value={amountFilter.max}
                        onChange={(e) => setAmountFilter(prev => ({ ...prev, max: e.target.value }))}
                        className="flex-1 bg-surface-sidebar border border-border-primary rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-accent-primary"
                        placeholder="Макс"
                        step="0.01"
                      />
                    </div>
                  </div>
                  
                  {/* Фильтр по ID транзакции */}
                  <div>
                    <label className="block text-text-secondary text-sm mb-2">ID транзакции</label>
                    <input
                      type="text"
                      value={transactionIdFilter}
                      onChange={(e) => setTransactionIdFilter(e.target.value)}
                      className="w-full bg-surface-sidebar border border-border-primary rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-accent-primary"
                      placeholder="Полный или частичный ID"
                    />
                  </div>
                </div>
                
                {/* Кнопка сброса фильтров */}
                <div className="mt-4 flex justify-end">
                  <button
                    onClick={() => {
                      setDateFilter({ from: '', to: '' });
                      setPlayerFilter('');
                      setAmountFilter({ min: '', max: '' });
                      setTransactionIdFilter('');
                    }}
                    className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white font-rajdhani rounded text-sm transition-colors"
                  >
                    Сбросить фильтры
                  </button>
                </div>
              </div>
            </div>

            {/* Таблица транзакций */}
            <div className="overflow-hidden">
              {entries.length === 0 ? (
                <div className="text-center py-16">
                  <div className={`mb-4 flex justify-center ${
                    categories[activeCategory]?.color === 'green' ? 'text-green-400' :
                    categories[activeCategory]?.color === 'blue' ? 'text-blue-400' :
                    categories[activeCategory]?.color === 'purple' ? 'text-purple-400' : 'text-gray-400'
                  }`}>
                    <div style={{ transform: 'scale(3)' }}>
                      {categories[activeCategory]?.icon}
                    </div>
                  </div>
                  <h4 className="font-rajdhani text-xl font-bold text-white mb-2">Нет транзакций</h4>
                  <p className="text-text-secondary">В категории "{categories[activeCategory]?.name || 'Неизвестная категория'}" пока нет данных</p>
                  <p className="text-text-secondary text-sm mt-2">Попробуйте изменить фильтры или период</p>
                </div>
              ) : (
                <>
                  {/* Desktop Table */}
                  <div className="hidden lg:block overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-surface-sidebar">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">ID</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Дата и время</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Сумма</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Тип действия</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Игрок</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Описание</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-primary">
                        {entries.map((entry, index) => {
                          const { date, time } = formatDateTime(entry.created_at);
                          const currentCategory = categories[activeCategory] || { color: 'gray' };
                          return (
                            <tr key={index} className="hover:bg-surface-sidebar transition-colors">
                              <td className="px-4 py-3">
                                <button
                                  onClick={() => copyToClipboard(entry.id)}
                                  onMouseEnter={(e) => showTooltip(e, entry.id)}
                                  onMouseLeave={hideTooltip}
                                  className="p-2 bg-surface-card border border-border-primary rounded hover:border-accent-primary transition-colors group"
                                  title="Нажмите чтобы скопировать ID"
                                >
                                  <svg className="w-4 h-4 text-accent-primary group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                  </svg>
                                </button>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto font-bold text-white">{date}</div>
                                <div className="text-xs text-text-secondary">{time}</div>
                              </td>
                              <td className="px-4 py-3">
                                <span className={`text-lg font-bold font-russo ${
                                  currentCategory.color === 'green' ? 'text-green-400' : 
                                  currentCategory.color === 'blue' ? 'text-blue-400' : 
                                  currentCategory.color === 'purple' ? 'text-purple-400' : 'text-gray-400'
                                }`}>
                                  {formatCurrencyWithSymbol(entry.amount, true)}
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  currentCategory.color === 'green' ? 'bg-green-100 text-green-800' :
                                  currentCategory.color === 'blue' ? 'bg-blue-100 text-blue-800' :
                                  'bg-purple-100 text-purple-800'
                                }`}>
                                  {getActionType(entry, activeCategory)}
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto text-white">
                                  {getPlayerInfo(entry)}
                                </div>
                                {entry.source_user_id && (
                                  <div className="text-xs text-accent-primary font-mono">
                                    ID: {entry.source_user_id.substring(0, 8)}...
                                  </div>
                                )}
                              </td>
                              <td className="px-4 py-3 text-sm font-roboto text-text-secondary max-w-xs">
                                <div className="truncate" title={entry.description}>
                                  {entry.description || '—'}
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Mobile Cards */}
                  <div className="lg:hidden space-y-3 p-4">
                    {entries.map((entry, index) => {
                      const { date, time } = formatDateTime(entry.created_at);
                      const currentCategory = categories[activeCategory] || { color: 'gray' };
                      return (
                        <div key={index} className="bg-surface-sidebar rounded-lg p-4 border border-border-primary">
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center space-x-3">
                              <button
                                onClick={() => copyToClipboard(entry.id)}
                                className="p-2 bg-surface-card border border-border-primary rounded hover:border-accent-primary transition-colors"
                                title="Скопировать ID"
                              >
                                <svg className="w-4 h-4 text-accent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                              </button>
                              <div>
                                <div className="text-sm font-roboto font-bold text-white">{date}</div>
                                <div className="text-xs text-text-secondary">{time}</div>
                              </div>
                            </div>
                            <div className={`text-lg font-bold font-russo ${
                              currentCategory.color === 'green' ? 'text-green-400' : 
                              currentCategory.color === 'blue' ? 'text-blue-400' : 
                              currentCategory.color === 'purple' ? 'text-purple-400' : 'text-gray-400'
                            }`}>
                              {formatCurrencyWithSymbol(entry.amount, true)}
                            </div>
                          </div>
                          
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-text-secondary">Тип действия:</span>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                currentCategory.color === 'green' ? 'bg-green-100 text-green-800' :
                                currentCategory.color === 'blue' ? 'bg-blue-100 text-blue-800' :
                                'bg-purple-100 text-purple-800'
                              }`}>
                                {getActionType(entry, activeCategory)}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-text-secondary">Игрок:</span>
                              <span className="text-white">{getPlayerInfo(entry)}</span>
                            </div>
                            {entry.description && (
                              <div>
                                <span className="text-text-secondary">Описание:</span>
                                <div className="text-white text-xs mt-1">{entry.description}</div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
            </div>
            
            {/* Пагинация */}
            {pagination.totalPages > 1 && pagination.handlePageChange && (
              <div className="border-t border-border-primary p-4 bg-surface-sidebar">
                <Pagination
                  currentPage={pagination.currentPage}
                  totalPages={pagination.totalPages}
                  onPageChange={pagination.handlePageChange}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && commissionSettings && (
        <div className="space-y-6">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Настройки комиссий</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Комиссия за ставки (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  defaultValue={commissionSettings.bet_commission_rate || 3}
                  className="w-full bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Комиссия за подарки (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  defaultValue={commissionSettings.gift_commission_rate || 3}
                  className="w-full bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                />
              </div>
              <button className="bg-accent-primary hover:bg-accent-primary/80 text-white font-rajdhani font-bold py-2 px-4 rounded-lg transition-colors">
                Сохранить настройки
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Tooltip */}
      {tooltip.show && (
        <div 
          className="fixed z-50 bg-black text-white text-xs rounded px-2 py-1 pointer-events-none"
          style={{ left: tooltip.x + 10, top: tooltip.y - 30 }}
        >
          {tooltip.text}
        </div>
      )}

      {/* Copy Success Notification */}
      {copySuccess && (
        <div className="fixed top-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg z-50 transition-all">
          ✓ ID скопирован в буфер обмена
        </div>
      )}

      {/* Модальное окно для настройки расходов */}
      {showExpensesModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-red-500 border-opacity-50 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-red-400">Настройка расходов</h3>
              <button
                onClick={() => setShowExpensesModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-white font-bold mb-2">Процент от общей прибыли (%)</label>
                <input
                  type="number"
                  value={expensesSettings.percentage}
                  onChange={(e) => setExpensesSettings(prev => ({ ...prev, percentage: parseInt(e.target.value) || 0 }))}
                  className="w-full bg-surface-sidebar border border-border-primary rounded px-3 py-2 text-white"
                  min="0"
                  max="100"
                />
              </div>
              
              <div>
                <label className="block text-white font-bold mb-2">Дополнительные расходы ($)</label>
                <input
                  type="number"
                  value={expensesSettings.manual_amount}
                  onChange={(e) => setExpensesSettings(prev => ({ ...prev, manual_amount: parseFloat(e.target.value) || 0 }))}
                  className="w-full bg-surface-sidebar border border-border-primary rounded px-3 py-2 text-white"
                  step="0.01"
                />
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowExpensesModal(false)}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-bold"
                >
                  Сохранить
                </button>
                <button
                  onClick={() => {
                    setExpensesSettings({ percentage: 60, manual_amount: 0 });
                    setShowExpensesModal(false);
                  }}
                  className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded"
                >
                  Сбросить
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Специализированные модальные окна */}
      {activeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-50 rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-border-primary">
              <h3 className="font-rajdhani text-xl font-bold text-white">
                {getModalTitle(activeModal)}
              </h3>
              <button
                onClick={() => setActiveModal(null)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {/* Модальное окно для комиссии от ставок */}
              {activeModal === 'bet_commission' && (
                <div className="space-y-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="8" strokeWidth="2"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 9h3m-3 3h3m-3 3h3M9 12l2 2 4-4"/>
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-rajdhani text-lg font-bold text-white">Настройка комиссии от ставок</h4>
                      <p className="text-sm text-text-secondary">Процент комиссии, взимаемый с выигрыша в PvP-играх</p>
                    </div>
                  </div>

                  <div className="bg-surface-sidebar rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <span className="text-sm text-text-secondary">Текущая комиссия:</span>
                        <div className="text-2xl font-bold text-green-400">{commissionSettings?.bet_commission_rate || 3}%</div>
                      </div>
                      <div>
                        <span className="text-sm text-text-secondary">Общая сумма:</span>
                        <div className="text-2xl font-bold text-green-400">{formatCurrencyWithSymbol(stats.bet_commission || 0, true)}</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Процент комиссии (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={commissionModalSettings.bet_commission_rate}
                        onChange={(e) => setCommissionModalSettings(prev => ({
                          ...prev,
                          bet_commission_rate: parseFloat(e.target.value) || 0
                        }))}
                        className="w-full bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                      />
                      <p className="text-xs text-text-secondary mt-1">
                        Рекомендуемый диапазон: 1-10%. Текущий: {commissionSettings?.bet_commission_rate || 3}%
                      </p>
                    </div>

                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                      <div className="flex items-center space-x-2">
                        <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                        <span className="text-sm font-medium text-yellow-400">Внимание</span>
                      </div>
                      <p className="text-sm text-yellow-300 mt-1">
                        Изменение комиссии повлияет на все новые ставки. Существующие игры останутся с прежним процентом.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Модальное окно для комиссии от Human-ботов */}
              {activeModal === 'human_bot_commission' && (
                <div className="space-y-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-12 h-12 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <rect x="4" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
                        <rect x="14" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
                        <rect x="4" y="14" width="16" height="6" strokeWidth="2" rx="1"/>
                        <circle cx="17" cy="7" r="1" fill="currentColor"/>
                        <circle cx="7" cy="7" r="1" fill="currentColor"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 17h8"/>
                        <text x="12" y="16" textAnchor="middle" fontSize="8" fill="currentColor">%</text>
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-rajdhani text-lg font-bold text-white">Комиссия от Human-ботов</h4>
                      <p className="text-sm text-text-secondary">Детализация комиссий, взимаемых с Human-ботов в играх</p>
                    </div>
                  </div>

                  {modalLoading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400 mx-auto mb-4"></div>
                      <p className="text-cyan-400">Загрузка данных...</p>
                    </div>
                  ) : modalError ? (
                    <div className="text-center py-8">
                      <div className="text-red-400 mb-2">⚠️</div>
                      <p className="text-sm text-red-400">{modalError}</p>
                      <button 
                        onClick={() => loadModalData('human_bot_commission')}
                        className="mt-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                      >
                        Повторить попытку
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="bg-surface-sidebar rounded-lg p-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                          <div>
                            <span className="text-sm text-text-secondary">Общая сумма:</span>
                            <div className="text-2xl font-bold text-cyan-400">
                              {formatCurrencyWithSymbol(modalData.total_amount || 0, true)}
                            </div>
                            <div className="text-xs text-cyan-300 mt-1">
                              {modalData.period === 'day' && 'за день'}
                              {modalData.period === 'week' && 'за неделю'}
                              {modalData.period === 'month' && 'за месяц'}
                              {modalData.period === 'all' && 'за все время'}
                            </div>
                          </div>
                          <div>
                            <span className="text-sm text-text-secondary">Всего транзакций:</span>
                            <div className="text-2xl font-bold text-cyan-400">{modalData.total_transactions || 0}</div>
                            <div className="text-xs text-cyan-300 mt-1">комиссионных операций</div>
                          </div>
                          <div>
                            <span className="text-sm text-text-secondary">Средняя комиссия:</span>
                            <div className="text-2xl font-bold text-cyan-400">
                              {formatCurrencyWithSymbol(modalData.avg_per_transaction || 0, true)}
                            </div>
                            <div className="text-xs text-cyan-300 mt-1">за транзакцию</div>
                          </div>
                        </div>
                        <div className="text-xs text-cyan-300">
                          Активных Human-ботов: {modalData.unique_bots || 0} • Ставка комиссии: {modalData.summary?.commission_rate || '3%'}
                        </div>
                      </div>

                      {modalData.breakdown && modalData.breakdown.length > 0 ? (
                        <div className="space-y-3">
                          <h5 className="font-rajdhani text-sm font-bold text-cyan-400 mb-2">Комиссии по Human-ботам:</h5>
                          {modalData.breakdown.map((bot, index) => (
                            <div key={index} className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
                              <div className="flex justify-between items-center mb-2">
                                <div>
                                  <span className="text-sm font-medium text-cyan-400">{bot.bot_name}</span>
                                  <div className="text-xs text-text-secondary">ID: {bot.bot_id}</div>
                                </div>
                                <div className="text-right">
                                  <div className="text-lg font-bold text-cyan-400">
                                    {formatCurrencyWithSymbol(bot.amount || 0, true)}
                                  </div>
                                  <div className="text-xs text-cyan-300">{bot.transactions} игр</div>
                                </div>
                              </div>
                              <div className="text-xs text-text-secondary">
                                Средняя комиссия: {formatCurrencyWithSymbol(bot.avg_per_transaction || 0, true)} за игру
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8">
                          <div className="text-4xl mb-4">🤖</div>
                          <h4 className="font-rajdhani text-lg font-bold mb-2 text-cyan-400">Нет данных</h4>
                          <p className="text-sm text-text-secondary">За выбранный период Human-боты не генерировали комиссий</p>
                        </div>
                      )}

                      {modalData.summary && modalData.summary.top_earning_bot && (
                        <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
                          <h5 className="font-rajdhani text-sm font-bold text-cyan-400 mb-2">Статистика:</h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="flex justify-between">
                              <span className="text-cyan-300">Топ-бот по доходу:</span>
                              <span className="text-cyan-400">{modalData.summary.top_earning_bot}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-cyan-300">Лучший результат:</span>
                              <span className="text-cyan-400">{formatCurrencyWithSymbol(modalData.summary.top_earning_amount || 0, true)}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Модальное окно для комиссии от подарков */}
              {activeModal === 'gift_commission' && (
                <div className="space-y-6">
                  <div className="flex items-center space-x-3 mb-4">
                    <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <rect x="3" y="8" width="18" height="12" strokeWidth="2" rx="2"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8V20"/>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2"/>
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-rajdhani text-lg font-bold text-white">Настройка комиссии от подарков</h4>
                      <p className="text-sm text-text-secondary">Процент комиссии, взимаемый при передаче гемов между игроками</p>
                    </div>
                  </div>

                  <div className="bg-surface-sidebar rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <span className="text-sm text-text-secondary">Текущая комиссия:</span>
                        <div className="text-2xl font-bold text-purple-400">{commissionSettings?.gift_commission_rate || 3}%</div>
                      </div>
                      <div>
                        <span className="text-sm text-text-secondary">Общая сумма:</span>
                        <div className="text-2xl font-bold text-purple-400">{formatCurrencyWithSymbol(stats.gift_commission || 0, true)}</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Процент комиссии (%)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={commissionModalSettings.gift_commission_rate}
                        onChange={(e) => setCommissionModalSettings(prev => ({
                          ...prev,
                          gift_commission_rate: parseFloat(e.target.value) || 0
                        }))}
                        className="w-full bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                      />
                      <p className="text-xs text-text-secondary mt-1">
                        Рекомендуемый диапазон: 1-10%. Текущий: {commissionSettings?.gift_commission_rate || 3}%
                      </p>
                    </div>

                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                      <div className="flex items-center space-x-2">
                        <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-sm font-medium text-blue-400">Информация</span>
                      </div>
                      <p className="text-sm text-blue-300 mt-1">
                        Комиссия за подарки взимается с отправителя при каждой передаче гемов другому игроку.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Модальное окно для дохода от ботов */}
              {activeModal === 'bot_revenue' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
                        <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <rect x="4" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
                          <rect x="14" y="4" width="6" height="6" strokeWidth="2" rx="1"/>
                          <rect x="4" y="14" width="16" height="6" strokeWidth="2" rx="1"/>
                          <circle cx="17" cy="7" r="1" fill="currentColor"/>
                          <circle cx="7" cy="7" r="1" fill="currentColor"/>
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 17h8"/>
                        </svg>
                      </div>
                      <div>
                        <h4 className="font-rajdhani text-lg font-bold text-white">Доход от ботов</h4>
                        <p className="text-sm text-text-secondary">Интегрированная аналитика прибыли от AI-ботов</p>
                      </div>
                    </div>
                    
                    {/* Переключатель периодов */}
                    <div className="flex bg-surface-sidebar rounded-lg p-1">
                      {[
                        { key: 'day', label: 'День' },
                        { key: 'week', label: 'Неделя' },
                        { key: 'month', label: 'Месяц' },
                        { key: 'all', label: 'Все' }
                      ].map((period) => (
                        <button
                          key={period.key}
                          onClick={() => handlePeriodChange(period.key)}
                          className={`px-3 py-1 text-xs rounded-md transition-colors ${
                            activePeriod === period.key
                              ? 'bg-blue-500 text-white'
                              : 'text-text-secondary hover:text-white'
                          }`}
                        >
                          {period.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Интегрированная статистика ботов */}
                  {botIntegrationData && (
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-6">
                      <h5 className="font-rajdhani text-lg font-bold text-blue-400 mb-4">
                        🤖 Статистика ботов
                      </h5>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <div className="bg-surface-sidebar rounded-lg p-3">
                          <div className="text-xs text-text-secondary mb-1">Активных ботов</div>
                          <div className="text-lg font-bold text-blue-400">{botIntegrationData.bot_stats.active_bots}</div>
                        </div>
                        <div className="bg-surface-sidebar rounded-lg p-3">
                          <div className="text-xs text-text-secondary mb-1">Всего ботов</div>
                          <div className="text-lg font-bold text-blue-400">{botIntegrationData.bot_stats.total_bots}</div>
                        </div>
                        <div className="bg-surface-sidebar rounded-lg p-3">
                          <div className="text-xs text-text-secondary mb-1">Avg Win Rate</div>
                          <div className="text-lg font-bold text-blue-400">{botIntegrationData.bot_stats.avg_win_rate?.toFixed(1) || 0}%</div>
                        </div>
                        <div className="bg-surface-sidebar rounded-lg p-3">
                          <div className="text-xs text-text-secondary mb-1">Всего игр</div>
                          <div className="text-lg font-bold text-blue-400">{botIntegrationData.bot_stats.total_games}</div>
                        </div>
                      </div>
                      
                      {/* Режимы создания ставок */}
                      <div className="mb-4">
                        <h6 className="font-rajdhani text-sm font-bold text-blue-400 mb-2">Доход по режимам создания ставок:</h6>
                        <div className="space-y-2">
                          {Object.entries(botIntegrationData.creation_modes).map(([mode, data]) => (
                            <div key={mode} className="flex justify-between items-center bg-surface-card rounded-lg p-2">
                              <span className="text-sm text-text-secondary">
                                {mode === 'always-first' ? 'Always First' : 
                                 mode === 'queue-based' ? 'Queue-Based' : 
                                 mode === 'after-all' ? 'After All' : mode}
                              </span>
                              <span className="text-blue-400 font-bold">{formatCurrencyWithSymbol(data.revenue || 0, true)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Поведение ботов */}
                      <div className="mb-4">
                        <h6 className="font-rajdhani text-sm font-bold text-blue-400 mb-2">Доход по поведению ботов:</h6>
                        <div className="space-y-2">
                          {Object.entries(botIntegrationData.behaviors).map(([behavior, data]) => (
                            <div key={behavior} className="flex justify-between items-center bg-surface-card rounded-lg p-2">
                              <span className="text-sm text-text-secondary">
                                {behavior === 'aggressive' ? 'Агрессивный' : 
                                 behavior === 'balanced' ? 'Сбалансированный' : 
                                 behavior === 'cautious' ? 'Осторожный' : behavior}
                              </span>
                              <span className="text-blue-400 font-bold">{formatCurrencyWithSymbol(data.revenue || 0, true)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Эффективность */}
                      <div>
                        <h6 className="font-rajdhani text-sm font-bold text-blue-400 mb-2">Эффективность:</h6>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div className="bg-surface-card rounded-lg p-3">
                            <div className="text-xs text-text-secondary mb-1">Доход за игру</div>
                            <div className="text-lg font-bold text-blue-400">{formatCurrencyWithSymbol(botIntegrationData.efficiency.revenue_per_game || 0, true)}</div>
                          </div>
                          <div className="bg-surface-card rounded-lg p-3">
                            <div className="text-xs text-text-secondary mb-1">Доход за бота</div>
                            <div className="text-lg font-bold text-blue-400">{formatCurrencyWithSymbol(botIntegrationData.efficiency.revenue_per_bot || 0, true)}</div>
                          </div>
                          <div className="bg-surface-card rounded-lg p-3">
                            <div className="text-xs text-text-secondary mb-1">Игр на бота</div>
                            <div className="text-lg font-bold text-blue-400">{botIntegrationData.efficiency.games_per_bot?.toFixed(1) || 0}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {modalLoading ? (
                    <div className="text-center py-8">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                      <p className="text-sm text-text-secondary mt-2">Загрузка данных...</p>
                    </div>
                  ) : modalError ? (
                    <div className="text-center py-8">
                      <div className="text-red-400 mb-2">⚠️</div>
                      <p className="text-sm text-red-400">{modalError}</p>
                      <button 
                        onClick={() => loadModalData('bot_revenue')}
                        className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                      >
                        Повторить попытку
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Общий доход:</span>
                          <div className="text-2xl font-bold text-blue-400">
                            {formatCurrencyWithSymbol(modalData.total_revenue || 0, true)}
                          </div>
                          <div className="text-xs text-blue-300 mt-1">
                            {modalData.period === 'day' && 'за день'}
                            {modalData.period === 'week' && 'за неделю'}
                            {modalData.period === 'month' && 'за месяц'}
                            {modalData.period === 'all' && 'за все время'}
                          </div>
                        </div>
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Активных ботов:</span>
                          <div className="text-2xl font-bold text-blue-400">{modalData.active_bots || 0}</div>
                        </div>
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Средний доход:</span>
                          <div className="text-2xl font-bold text-blue-400">
                            {formatCurrencyWithSymbol(modalData.avg_revenue_per_bot || 0, true)}
                          </div>
                        </div>
                      </div>

                      {/* График доходов от ботов */}
                      <div className="bg-surface-sidebar rounded-lg p-4 mb-6">
                        <h5 className="font-rajdhani text-lg font-bold text-blue-400 mb-4">
                          📈 Динамика доходов от ботов
                        </h5>
                        <ProfitChart
                          type="line"
                          data={generateMockChartData(activePeriod, 'blue', modalData.chart_data)}
                          title={`Доходы от ботов ${
                            modalData.period === 'day' ? 'за день' :
                            modalData.period === 'week' ? 'за неделю' :
                            modalData.period === 'month' ? 'за месяц' :
                            'за все время'
                          }`}
                        />
                      </div>

                      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                        <h5 className="font-rajdhani text-sm font-bold text-blue-400 mb-2">Как работает доход от ботов:</h5>
                        <p className="text-sm text-blue-300">
                          Обычные боты накапливают выигрыши в защищенном контейнере. После завершения полного цикла (обычно 12 игр) 
                          прибыль переводится в общий фонд платформы.
                        </p>
                      </div>

                      {modalData.entries && modalData.entries.length > 0 ? (
                        <div className="space-y-3">
                          <h5 className="font-rajdhani text-sm font-bold text-blue-400">Детализация по ботам:</h5>
                          <div className="max-h-64 overflow-y-auto space-y-2">
                            {modalData.entries.map((bot, index) => (
                              <div key={index} className="bg-surface-sidebar rounded-lg p-3">
                                <div className="flex justify-between items-center">
                                  <div>
                                    <div className="font-medium text-white">{bot.bot_name}</div>
                                    <div className="text-xs text-text-secondary">
                                      {bot.games_played} игр • {bot.win_rate?.toFixed(1)}% побед
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-lg font-bold text-blue-400">
                                      {formatCurrencyWithSymbol(bot.total_revenue || 0, true)}
                                    </div>
                                    <div className="text-xs text-text-secondary">
                                      {bot.cycles_completed} циклов
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center text-text-secondary py-8">
                          <div className="text-lg mb-2">📊</div>
                          <p className="text-sm">Нет данных о доходах от ботов</p>
                          <p className="text-xs mt-1">
                            {modalData.period === 'day' && 'за выбранный день'}
                            {modalData.period === 'week' && 'за выбранную неделю'}
                            {modalData.period === 'month' && 'за выбранный месяц'}
                            {modalData.period === 'all' && 'за все время'}
                          </p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Модальное окно для замороженных средств */}
              {activeModal === 'frozen_funds' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center">
                        <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                        </svg>
                      </div>
                      <div>
                        <h4 className="font-rajdhani text-lg font-bold text-white">Замороженные средства</h4>
                        <p className="text-sm text-text-secondary">Комиссия в активных играх и незавершенных транзакциях</p>
                      </div>
                    </div>
                    
                    {/* Переключатель периодов */}
                    <div className="flex bg-surface-sidebar rounded-lg p-1">
                      {[
                        { key: 'day', label: 'День' },
                        { key: 'week', label: 'Неделя' },
                        { key: 'month', label: 'Месяц' },
                        { key: 'all', label: 'Все' }
                      ].map((period) => (
                        <button
                          key={period.key}
                          onClick={() => handlePeriodChange(period.key)}
                          className={`px-3 py-1 text-xs rounded-md transition-colors ${
                            activePeriod === period.key
                              ? 'bg-orange-500 text-white'
                              : 'text-text-secondary hover:text-white'
                          }`}
                        >
                          {period.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {modalLoading ? (
                    <div className="text-center py-8">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-400"></div>
                      <p className="text-sm text-text-secondary mt-2">Загрузка данных...</p>
                    </div>
                  ) : modalError ? (
                    <div className="text-center py-8">
                      <div className="text-red-400 mb-2">⚠️</div>
                      <p className="text-sm text-red-400">{modalError}</p>
                      <button 
                        onClick={() => loadModalData('frozen_funds')}
                        className="mt-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 text-sm"
                      >
                        Повторить попытку
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Замороженная комиссия:</span>
                          <div className="text-2xl font-bold text-orange-400">
                            {formatCurrencyWithSymbol(modalData.total_frozen || 0, true)}
                          </div>
                          <div className="text-xs text-orange-300 mt-1">
                            {modalData.period === 'day' && 'за день'}
                            {modalData.period === 'week' && 'за неделю'}
                            {modalData.period === 'month' && 'за месяц'}
                            {modalData.period === 'all' && 'за все время'}
                          </div>
                        </div>
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Активных игр:</span>
                          <div className="text-2xl font-bold text-orange-400">{modalData.active_games || 0}</div>
                          <div className="text-xs text-orange-300 mt-1">
                            {modalData.period === 'day' && 'за день'}
                            {modalData.period === 'week' && 'за неделю'}
                            {modalData.period === 'month' && 'за месяц'}
                            {modalData.period === 'all' && 'за все время'}
                          </div>
                        </div>
                      </div>

                      <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                        <h5 className="font-rajdhani text-sm font-bold text-orange-400 mb-2">Что такое замороженные средства:</h5>
                        <p className="text-sm text-orange-300">
                          Когда игрок создает ставку, комиссия (6%) замораживается и будет разморожена только после завершения игры. 
                          Это обеспечивает справедливость и предотвращает злоупотребления.
                        </p>
                      </div>

                      {modalData.entries && modalData.entries.length > 0 ? (
                        <div className="space-y-3">
                          <h5 className="font-rajdhani text-sm font-bold text-orange-400">Активные игры:</h5>
                          <div className="max-h-64 overflow-y-auto space-y-2">
                            {modalData.entries.map((game, index) => (
                              <div key={index} className="bg-surface-sidebar rounded-lg p-3">
                                <div className="flex justify-between items-center">
                                  <div>
                                    <div className="font-medium text-white">
                                      {game.creator?.username || 'Unknown'} vs {game.opponent?.username || 'Ожидание'}
                                    </div>
                                    <div className="text-xs text-text-secondary">
                                      Ставка: {formatCurrencyWithSymbol(game.bet_amount || 0, true)} • 
                                      Статус: {game.status || 'Unknown'}
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-lg font-bold text-orange-400">
                                      {formatCurrencyWithSymbol(game.frozen_commission || 0, true)}
                                    </div>
                                    <div className="text-xs text-text-secondary">
                                      {game.commission_rate ? `${(game.commission_rate * 100).toFixed(1)}%` : '6%'}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center text-text-secondary py-8">
                          <div className="text-lg mb-2">🔒</div>
                          <p className="text-sm">Нет активных игр с замороженными средствами</p>
                          <p className="text-xs mt-1">Данные появятся при создании новых игр</p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Модальное окно для общей прибыли */}
              {activeModal === 'total_revenue' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                        <svg className="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"/>
                        </svg>
                      </div>
                      <div>
                        <h4 className="font-rajdhani text-lg font-bold text-white">Общая прибыль</h4>
                        <p className="text-sm text-text-secondary">Сводка по всем источникам дохода платформы</p>
                      </div>
                    </div>
                    
                    {/* Переключатель периодов */}
                    <div className="flex bg-surface-sidebar rounded-lg p-1">
                      {[
                        { key: 'day', label: 'День' },
                        { key: 'week', label: 'Неделя' },
                        { key: 'month', label: 'Месяц' },
                        { key: 'all', label: 'Все' }
                      ].map((period) => (
                        <button
                          key={period.key}
                          onClick={() => handlePeriodChange(period.key)}
                          className={`px-3 py-1 text-xs rounded-md transition-colors ${
                            activePeriod === period.key
                              ? 'bg-yellow-500 text-white'
                              : 'text-text-secondary hover:text-white'
                          }`}
                        >
                          {period.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {modalLoading ? (
                    <div className="text-center py-8">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
                      <p className="text-sm text-text-secondary mt-2">Загрузка данных...</p>
                    </div>
                  ) : modalError ? (
                    <div className="text-center py-8">
                      <div className="text-red-400 mb-2">⚠️</div>
                      <p className="text-sm text-red-400">{modalError}</p>
                      <button 
                        onClick={() => loadModalData('total_revenue')}
                        className="mt-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-sm"
                      >
                        Повторить попытку
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="text-center mb-6">
                        <div className="text-4xl font-bold text-yellow-400">
                          {formatCurrencyWithSymbol(modalData.total_revenue || 0, true)}
                        </div>
                        <div className="text-sm text-text-secondary">
                          Общая прибыль 
                          {modalData.period === 'day' && ' за день'}
                          {modalData.period === 'week' && ' за неделю'}
                          {modalData.period === 'month' && ' за месяц'}
                          {modalData.period === 'all' && ' за все время'}
                        </div>
                      </div>

                      {/* График разбивки доходов */}
                      {modalData.breakdown && modalData.breakdown.length > 0 && (
                        <div className="bg-surface-sidebar rounded-lg p-4 mb-6">
                          <h5 className="font-rajdhani text-lg font-bold text-yellow-400 mb-4">
                            🥧 Распределение доходов
                          </h5>
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            <div className="h-64">
                              <ProfitChart
                                type="doughnut"
                                data={generateRevenueBreakdownData(modalData.breakdown)}
                              />
                            </div>
                            <div className="space-y-3">
                              {modalData.breakdown.map((item, index) => (
                                <div key={index} className="flex items-center justify-between p-3 bg-surface-card rounded-lg">
                                  <div className="flex items-center space-x-3">
                                    <div className={`w-4 h-4 rounded-full`} style={{
                                      backgroundColor: ['#4A90E2', '#22C55E', '#FBBF24', '#9333EA', '#F97316'][index % 5]
                                    }}></div>
                                    <span className="text-sm text-white">{item.name}</span>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-lg font-bold text-yellow-400">
                                      {formatCurrencyWithSymbol(item.amount || 0, true)}
                                    </div>
                                    <div className="text-xs text-text-secondary">
                                      {item.percentage?.toFixed(1)}%
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {modalData.breakdown && modalData.breakdown.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-3">
                            {modalData.breakdown.map((item, index) => (
                              <div key={index} className={`bg-${item.color}-500/10 border border-${item.color}-500/30 rounded-lg p-4`}>
                                <div className="flex items-center space-x-2">
                                  <div className={`w-4 h-4 bg-${item.color}-400 rounded-full`}></div>
                                  <span className={`text-sm text-${item.color}-400`}>{item.name}</span>
                                </div>
                                <div className={`text-xl font-bold text-${item.color}-400 mt-1`}>
                                  {formatCurrencyWithSymbol(item.amount || 0, true)}
                                </div>
                                <div className="text-xs text-text-secondary">
                                  {item.percentage?.toFixed(1)}% • {item.transactions} транзакций
                                </div>
                              </div>
                            ))}
                          </div>
                          
                          <div className="space-y-3">
                            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                              <h5 className="font-rajdhani text-sm font-bold text-yellow-400 mb-2">Статистика:</h5>
                              <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-text-secondary">Всего транзакций:</span>
                                  <span className="text-yellow-400">{modalData.summary?.total_transactions || 0}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-text-secondary">Средняя сумма:</span>
                                  <span className="text-yellow-400">
                                    {formatCurrencyWithSymbol(modalData.summary?.avg_revenue_per_transaction || 0, true)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-text-secondary">Топ источник:</span>
                                  <span className="text-yellow-400">
                                    {modalData.breakdown?.find(b => b.source === modalData.summary?.top_source)?.name || 'N/A'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center text-text-secondary py-8">
                          <div className="text-lg mb-2">📊</div>
                          <p className="text-sm">Нет данных о доходах</p>
                          <p className="text-xs mt-1">Данные появятся после первых транзакций</p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Модальное окно для расходов */}
              {activeModal === 'expenses' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                        <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"/>
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                      </div>
                      <div>
                        <h4 className="font-rajdhani text-lg font-bold text-white">Расходы</h4>
                        <p className="text-sm text-text-secondary">Операционные расходы и затраты платформы</p>
                      </div>
                    </div>
                    
                    {/* Переключатель периодов */}
                    <div className="flex bg-surface-sidebar rounded-lg p-1">
                      {[
                        { key: 'day', label: 'День' },
                        { key: 'week', label: 'Неделя' },
                        { key: 'month', label: 'Месяц' },
                        { key: 'all', label: 'Все' }
                      ].map((period) => (
                        <button
                          key={period.key}
                          onClick={() => handlePeriodChange(period.key)}
                          className={`px-3 py-1 text-xs rounded-md transition-colors ${
                            activePeriod === period.key
                              ? 'bg-red-500 text-white'
                              : 'text-text-secondary hover:text-white'
                          }`}
                        >
                          {period.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {modalLoading ? (
                    <div className="text-center py-8">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-red-400"></div>
                      <p className="text-sm text-text-secondary mt-2">Загрузка данных...</p>
                    </div>
                  ) : modalError ? (
                    <div className="text-center py-8">
                      <div className="text-red-400 mb-2">⚠️</div>
                      <p className="text-sm text-red-400">{modalError}</p>
                      <button 
                        onClick={() => loadModalData('expenses')}
                        className="mt-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                      >
                        Повторить попытку
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Общие расходы:</span>
                          <div className="text-2xl font-bold text-red-400">
                            {formatCurrencyWithSymbol(modalData.total_expenses || 0, true)}
                          </div>
                          <div className="text-xs text-red-300 mt-1">
                            {modalData.period === 'day' && 'за день'}
                            {modalData.period === 'week' && 'за неделю'}
                            {modalData.period === 'month' && 'за месяц'}
                            {modalData.period === 'all' && 'за все время'}
                          </div>
                        </div>
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Процент от прибыли:</span>
                          <div className="text-2xl font-bold text-red-400">{modalData.expense_percentage || 60}%</div>
                          <div className="text-xs text-red-300 mt-1">настроенный процент</div>
                        </div>
                      </div>

                      {/* График расходов */}
                      <div className="bg-surface-sidebar rounded-lg p-4 mb-6">
                        <h5 className="font-rajdhani text-lg font-bold text-red-400 mb-4">
                          📊 Динамика расходов
                        </h5>
                        <ProfitChart
                          type="bar"
                          data={generateExpensesData(activePeriod)}
                          title={`Расходы ${
                            modalData.period === 'day' ? 'за день' :
                            modalData.period === 'week' ? 'за неделю' :
                            modalData.period === 'month' ? 'за месяц' :
                            'за все время'
                          }`}
                        />
                      </div>

                      {modalData.breakdown && modalData.breakdown.length > 0 && (
                        <div className="space-y-3">
                          <h5 className="font-rajdhani text-sm font-bold text-red-400 mb-2">Структура расходов:</h5>
                          {modalData.breakdown.map((expense, index) => (
                            <div key={index} className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                              <div className="flex justify-between items-center">
                                <div>
                                  <span className="text-sm text-red-400">{expense.name}</span>
                                  <div className="text-xs text-text-secondary">{expense.calculation}</div>
                                </div>
                                <div className="text-lg font-bold text-red-400">
                                  {formatCurrencyWithSymbol(expense.amount || 0, true)}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {modalData.statistics && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                          <h5 className="font-rajdhani text-sm font-bold text-red-400 mb-2">Статистика:</h5>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-text-secondary">Соотношение расходов:</span>
                              <span className="text-red-400">{modalData.statistics.expense_ratio?.toFixed(1) || 0}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-text-secondary">Среднемесячные расходы:</span>
                              <span className="text-red-400">
                                {formatCurrencyWithSymbol(modalData.statistics.monthly_avg || 0, true)}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-text-secondary">Оценка эффективности:</span>
                              <span className="text-red-400">{modalData.statistics.efficiency_score?.toFixed(1) || 0}/100</span>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                        <h5 className="font-rajdhani text-sm font-bold text-red-400 mb-2">Настройка расходов:</h5>
                        <p className="text-sm text-red-300">
                          Расходы рассчитываются автоматически как процент от общей прибыли плюс дополнительные фиксированные расходы. 
                          Настройки можно изменить в плитке "Расходы".
                        </p>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Модальное окно для чистой прибыли */}
              {activeModal === 'net_profit' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                        <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                      </div>
                      <div>
                        <h4 className="font-rajdhani text-lg font-bold text-white">Чистая прибыль</h4>
                        <p className="text-sm text-text-secondary">Итоговая прибыль после вычета всех расходов</p>
                      </div>
                    </div>
                    
                    {/* Переключатель периодов */}
                    <div className="flex bg-surface-sidebar rounded-lg p-1">
                      {[
                        { key: 'day', label: 'День' },
                        { key: 'week', label: 'Неделя' },
                        { key: 'month', label: 'Месяц' },
                        { key: 'all', label: 'Все' }
                      ].map((period) => (
                        <button
                          key={period.key}
                          onClick={() => handlePeriodChange(period.key)}
                          className={`px-3 py-1 text-xs rounded-md transition-colors ${
                            activePeriod === period.key
                              ? 'bg-emerald-500 text-white'
                              : 'text-text-secondary hover:text-white'
                          }`}
                        >
                          {period.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {modalLoading ? (
                    <div className="text-center py-8">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400"></div>
                      <p className="text-sm text-text-secondary mt-2">Загрузка данных...</p>
                    </div>
                  ) : modalError ? (
                    <div className="text-center py-8">
                      <div className="text-red-400 mb-2">⚠️</div>
                      <p className="text-sm text-red-400">{modalError}</p>
                      <button 
                        onClick={() => loadModalData('net_profit')}
                        className="mt-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm"
                      >
                        Повторить попытку
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="text-center mb-6">
                        <div className="text-4xl font-bold text-emerald-400">
                          {formatCurrencyWithSymbol(modalData.summary?.net_profit || 0, true)}
                        </div>
                        <div className="text-sm text-text-secondary">
                          Чистая прибыль
                          {modalData.period === 'day' && ' за день'}
                          {modalData.period === 'week' && ' за неделю'}
                          {modalData.period === 'month' && ' за месяц'}
                          {modalData.period === 'all' && ' за все время'}
                        </div>
                        <div className="text-xs text-emerald-400 mt-1">
                          {modalData.summary?.profit_margin?.toFixed(1) || 0}% маржа
                        </div>
                      </div>

                      {/* График чистой прибыли */}
                      <div className="bg-surface-sidebar rounded-lg p-4 mb-6">
                        <h5 className="font-rajdhani text-lg font-bold text-emerald-400 mb-4">
                          💹 Динамика прибыли и расходов
                        </h5>
                        <ProfitChart
                          type="line"
                          data={generateNetProfitData(activePeriod)}
                          title={`Анализ прибыли ${
                            modalData.period === 'day' ? 'за день' :
                            modalData.period === 'week' ? 'за неделю' :
                            modalData.period === 'month' ? 'за месяц' :
                            'за все время'
                          }`}
                        />
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Общая прибыль:</span>
                          <div className="text-xl font-bold text-yellow-400">
                            {formatCurrencyWithSymbol(modalData.summary?.total_revenue || 0, true)}
                          </div>
                        </div>
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Расходы:</span>
                          <div className="text-xl font-bold text-red-400">
                            {formatCurrencyWithSymbol(modalData.summary?.total_expenses || 0, true)}
                          </div>
                        </div>
                        <div className="bg-surface-sidebar rounded-lg p-4">
                          <span className="text-sm text-text-secondary">Чистая прибыль:</span>
                          <div className="text-xl font-bold text-emerald-400">
                            {formatCurrencyWithSymbol(modalData.summary?.net_profit || 0, true)}
                          </div>
                        </div>
                      </div>

                      {modalData.calculation_steps && modalData.calculation_steps.length > 0 && (
                        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                          <h5 className="font-rajdhani text-sm font-bold text-emerald-400 mb-2">Пошаговый расчет:</h5>
                          <div className="space-y-2 text-sm">
                            {modalData.calculation_steps.map((step, index) => (
                              <div key={index} className="flex justify-between">
                                <span className="text-emerald-300">{step.description}:</span>
                                <span className={`text-emerald-300 ${step.amount < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                  {step.amount < 0 ? '' : '+'}
                                  {formatCurrencyWithSymbol(step.amount || 0, true)}
                                </span>
                              </div>
                            ))}
                            <div className="border-t border-emerald-500/30 pt-2">
                              <div className="flex justify-between font-bold">
                                <span className="text-emerald-400">Итоговый результат:</span>
                                <span className="text-emerald-400">
                                  {formatCurrencyWithSymbol(modalData.summary?.net_profit || 0, true)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {modalData.analysis?.trends && (
                        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
                          <h5 className="font-rajdhani text-sm font-bold text-emerald-400 mb-2">Анализ трендов:</h5>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-emerald-300">Прибыльность:</span>
                              <span className={`${modalData.analysis.trends.is_profitable ? 'text-emerald-400' : 'text-red-400'}`}>
                                {modalData.analysis.trends.is_profitable ? 'Прибыльно' : 'Убыточно'}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-emerald-300">Рейтинг эффективности:</span>
                              <span className="text-emerald-400">{modalData.analysis.trends.efficiency_rating || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-emerald-300">Потенциал роста:</span>
                              <span className="text-emerald-400">{modalData.analysis.trends.growth_potential || 'N/A'}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Заглушка для других модальных окон */}
              {activeModal !== 'bet_commission' && activeModal !== 'gift_commission' && 
               activeModal !== 'bot_revenue' && activeModal !== 'frozen_funds' && 
               activeModal !== 'total_revenue' && activeModal !== 'expenses' && 
               activeModal !== 'net_profit' && (
                <div className="text-center text-text-secondary py-8">
                  <div className="text-4xl mb-4">📊</div>
                  <h4 className="font-rajdhani text-lg font-bold mb-2">Детализация в разработке</h4>
                  <p>Здесь будет отображаться подробная информация о {getModalTitle(activeModal)}</p>
                  <p className="text-sm mt-2">История операций, графики и аналитика</p>
                </div>
              )}
            </div>

            <div className="flex justify-between p-6 border-t border-border-primary">
              <button
                onClick={() => setActiveModal(null)}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Закрыть
              </button>
              
              {/* Кнопка сохранения только для модальных окон настройки комиссий */}
              {(activeModal === 'bet_commission' || activeModal === 'gift_commission') && (
                <button
                  onClick={saveCommissionSettings}
                  disabled={savingCommission}
                  className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/80 disabled:opacity-50"
                >
                  {savingCommission ? 'Сохранение...' : 'Сохранить настройки'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfitAdmin;