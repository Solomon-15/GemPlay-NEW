import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { formatCurrencyWithSymbol } from '../utils/economy';
import Pagination from './Pagination';
import usePagination from '../hooks/usePagination';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProfitAdmin = ({ user }) => {
  const [stats, setStats] = useState(null);
  const [entries, setEntries] = useState([]);
  const [commissionSettings, setCommissionSettings] = useState(null);
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

  // Пагинация для истории прибыли
  const pagination = usePagination(1, 10);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeTab === 'history') {
      // Сброс на первую страницу при смене категории
      if (pagination.currentPage > 1) {
        pagination.handlePageChange(1);
      } else {
        fetchEntries();
      }
    }
  }, [activeTab, activeCategory, sortBy, sortOrder, dateFilter]);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchEntries();
    }
  }, [pagination.currentPage]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const [statsResponse, settingsResponse] = await Promise.all([
        axios.get(`${API}/admin/profit/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/profit/commission-settings`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setStats(statsResponse.data);
      setCommissionSettings(settingsResponse.data);
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
    'BOT_REVENUE': {
      name: 'Доход от ботов от ставок',
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
      'BOT_REVENUE': 'bg-blue-600', 
      'GIFT_COMMISSION': 'bg-purple-600'
    };
    return colors[categoryKey] || 'bg-gray-600';
  };

  const getCategoryBadgeOpacity = (categoryKey) => {
    const colors = {
      'BET_COMMISSION': 'bg-green-600/20',
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
            <div className="bg-surface-card border border-blue-500/30 rounded-lg p-6 hover:border-blue-500/60 transition-colors duration-200 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Комиссия от ставок</h3>
                  <p className="font-russo text-2xl font-bold text-blue-400">{formatCurrencyWithSymbol(stats.bet_commission || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">3% от выигрышей в PvP</p>
                </div>
              </div>
            </div>

            {/* Комиссия от подарков */}
            <div className="bg-surface-card border border-purple-500/30 rounded-lg p-6 hover:border-purple-500/60 transition-colors duration-200 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Комиссия от подарков</h3>
                  <p className="font-russo text-2xl font-bold text-purple-400">{formatCurrencyWithSymbol(stats.gift_commission || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">3% за передачу гемов</p>
                </div>
              </div>
            </div>

            {/* Доход от ботов */}
            <div className="bg-surface-card border border-cyan-500/30 rounded-lg p-6 hover:border-cyan-500/60 transition-colors duration-200 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Доход от ботов</h3>
                  <p className="font-russo text-2xl font-bold text-cyan-400">{formatCurrencyWithSymbol(stats.bot_revenue || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">Матчи против ботов</p>
                </div>
              </div>
            </div>

            {/* Общая прибыль */}
            <div className="bg-surface-card border border-green-500/30 rounded-lg p-6 hover:border-green-500/60 transition-colors duration-200 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Общая прибыль</h3>
                  <p className="font-russo text-2xl font-bold text-green-400">{formatCurrencyWithSymbol(stats.total_revenue || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">Сумма всех доходов</p>
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
                    className={`px-6 py-4 font-rajdhani font-bold text-sm transition-all duration-200 border-b-2 flex items-center space-x-2 ${
                      activeCategory === key
                        ? (category.color === 'green' ? 'border-green-500 bg-green-500/10 text-green-400' :
                           category.color === 'blue' ? 'border-blue-500 bg-blue-500/10 text-blue-400' :
                           'border-purple-500 bg-purple-500/10 text-purple-400')
                        : 'border-transparent text-text-secondary hover:text-white hover:bg-surface-card'
                    }`}
                  >
                    <div className={`${
                      activeCategory === key
                        ? (category.color === 'green' ? 'text-green-400' :
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
                  
                  {/* Фильтры по дате */}
                  <div className="flex items-center space-x-2">
                    <span className="text-text-secondary text-sm">Период:</span>
                    <input
                      type="date"
                      value={dateFilter.from}
                      onChange={(e) => setDateFilter(prev => ({ ...prev, from: e.target.value }))}
                      className="bg-surface-card border border-border-primary rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-accent-primary"
                    />
                    <span className="text-text-secondary">—</span>
                    <input
                      type="date"
                      value={dateFilter.to}
                      onChange={(e) => setDateFilter(prev => ({ ...prev, to: e.target.value }))}
                      className="bg-surface-card border border-border-primary rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-accent-primary"
                    />
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
            </div>

            {/* Таблица транзакций */}
            <div className="overflow-hidden">
              {entries.length === 0 ? (
                <div className="text-center py-16">
                  <div className="text-6xl mb-4">{categories[activeCategory]?.icon || '📊'}</div>
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
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">ID</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Дата и время</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Сумма</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Тип действия</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Игрок</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Описание</th>
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
                                <div className="text-sm font-rajdhani font-bold text-white">{date}</div>
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
                                <div className="text-sm text-white">
                                  {getPlayerInfo(entry)}
                                </div>
                                {entry.source_user_id && (
                                  <div className="text-xs text-accent-primary font-mono">
                                    ID: {entry.source_user_id.substring(0, 8)}...
                                  </div>
                                )}
                              </td>
                              <td className="px-4 py-3 text-sm text-text-secondary max-w-xs">
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
                                <div className="text-sm font-rajdhani font-bold text-white">{date}</div>
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
    </div>
  );
};

export default ProfitAdmin;