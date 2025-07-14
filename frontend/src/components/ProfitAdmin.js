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
  const [filterType, setFilterType] = useState('');
  const [dateFilter, setDateFilter] = useState({ from: '', to: '' });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Пагинация для истории прибыли
  const pagination = usePagination(1, 10);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchEntries();
    }
  }, [activeTab, pagination.currentPage, filterType, dateFilter]);

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
        limit: pagination.itemsPerPage.toString()
      });

      if (filterType) params.append('type', filterType);
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
      'gift_commission': 'text-pink-400',
      'bot_profit': 'text-blue-400',
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

  const exportToCSV = () => {
    const headers = ['Дата', 'Время', 'Тип операции', 'Сумма', 'Источник', 'ID игрока/бота', 'Описание'];
    const csvContent = [
      headers.join(','),
      ...entries.map(entry => [
        new Date(entry.created_at).toLocaleDateString('ru-RU'),
        new Date(entry.created_at).toLocaleTimeString('ru-RU'),
        `"${getEntryTypeName(entry.type)}"`,
        entry.amount,
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

            {/* Замороженные средства */}
            <div className="bg-surface-card border border-yellow-500/30 rounded-lg p-6 hover:border-yellow-500/60 transition-colors duration-200 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Замороженные средства</h3>
                  <p className="font-russo text-2xl font-bold text-yellow-400">{formatCurrencyWithSymbol(stats.frozen_funds || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">Активные ставки</p>
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
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Общая прибыль</h3>
                  <p className="font-russo text-2xl font-bold text-green-400">{formatCurrencyWithSymbol(stats.total_profit || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">Совокупный доход</p>
                </div>
              </div>
            </div>

            {/* Расходы */}
            <div className="bg-surface-card border border-red-500/30 rounded-lg p-6 hover:border-red-500/60 transition-colors duration-200 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-red-500/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Расходы</h3>
                  <p className="font-russo text-2xl font-bold text-red-400">{formatCurrencyWithSymbol(stats.total_expenses || 0, true)}</p>
                  <p className="text-xs text-text-secondary mt-1">Бонусы, возвраты</p>
                </div>
              </div>
            </div>

            {/* Чистая прибыль */}
            <div className="bg-surface-card border border-accent-primary/50 rounded-lg p-6 hover:border-accent-primary transition-colors duration-200 shadow-lg ring-1 ring-accent-primary/20">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-10 h-10 bg-accent-primary/20 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-accent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="font-roboto text-text-secondary text-sm mb-1">Чистая прибыль</h3>
                  <p className="font-russo text-2xl font-bold text-accent-primary">{formatCurrencyWithSymbol((stats.total_profit || 0) - (stats.total_expenses || 0))}</p>
                  <p className="text-xs text-text-secondary mt-1">Прибыль - расходы</p>
                </div>
              </div>
            </div>

          </div>

          {/* Дополнительные статистики по периодам */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-6">Статистика по периодам</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-text-secondary text-sm mb-2">Сегодня</div>
                <div className="font-russo text-3xl font-bold text-blue-400 mb-1">{formatCurrencyWithSymbol(stats.today_profit || 0)}</div>
                <div className="text-xs text-text-secondary">Прибыль за день</div>
              </div>
              
              <div className="text-center">
                <div className="text-text-secondary text-sm mb-2">Эта неделя</div>
                <div className="font-russo text-3xl font-bold text-purple-400 mb-1">{formatCurrencyWithSymbol(stats.week_profit || 0)}</div>
                <div className="text-xs text-text-secondary">Прибыль за неделю</div>
              </div>
              
              <div className="text-center">
                <div className="text-text-secondary text-sm mb-2">Этот месяц</div>
                <div className="font-russo text-3xl font-bold text-orange-400 mb-1">{formatCurrencyWithSymbol(stats.month_profit || 0)}</div>
                <div className="text-xs text-text-secondary">Прибыль за месяц</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          {/* Filters and Export */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Фильтры и экспорт</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              {/* Type Filter */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Тип операции
                </label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                >
                  <option value="">Все типы</option>
                  <option value="bet_commission">💰 Комиссия от ставок</option>
                  <option value="gift_commission">🎁 Комиссия от подарков</option>
                  <option value="bot_profit">🤖 Доход от ботов</option>
                  <option value="human_bot_profit">🤖 Доход от Human ботов</option>
                  <option value="penalty">🚨 Штрафы и удержания</option>
                  <option value="refund">🔄 Возвраты средств</option>
                  <option value="system_credit">⚙️ Системные начисления</option>
                  <option value="other">📊 Прочее</option>
                </select>
              </div>

              {/* Date From */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Дата от
                </label>
                <input
                  type="date"
                  value={dateFilter.from}
                  onChange={(e) => setDateFilter(prev => ({ ...prev, from: e.target.value }))}
                  className="w-full bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                />
              </div>

              {/* Date To */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Дата до
                </label>
                <input
                  type="date"
                  value={dateFilter.to}
                  onChange={(e) => setDateFilter(prev => ({ ...prev, to: e.target.value }))}
                  className="w-full bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                />
              </div>

              {/* Export Button */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Экспорт данных
                </label>
                <button
                  onClick={exportToCSV}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-rajdhani font-bold py-2 px-4 rounded-lg transition-colors duration-200"
                >
                  📥 Экспорт CSV
                </button>
              </div>
            </div>

            {/* Quick Filter Buttons */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  const today = new Date().toISOString().split('T')[0];
                  setDateFilter({ from: today, to: today });
                }}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                Сегодня
              </button>
              <button
                onClick={() => {
                  const today = new Date();
                  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                  setDateFilter({ 
                    from: weekAgo.toISOString().split('T')[0], 
                    to: today.toISOString().split('T')[0] 
                  });
                }}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                Неделя
              </button>
              <button
                onClick={() => {
                  const today = new Date();
                  const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
                  setDateFilter({ 
                    from: monthAgo.toISOString().split('T')[0], 
                    to: today.toISOString().split('T')[0] 
                  });
                }}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                Месяц
              </button>
              <button
                onClick={() => setDateFilter({ from: '', to: '' })}
                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition-colors"
              >
                Сбросить
              </button>
            </div>
          </div>

          {/* Profit History Table */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
            <div className="p-4 border-b border-border-primary">
              <h3 className="font-rajdhani text-lg font-bold text-white">
                История прибыли ({entries.length} записей)
              </h3>
            </div>

            {/* Desktop Table */}
            <div className="hidden lg:block overflow-x-auto">
              <table className="w-full">
                <thead className="bg-surface-sidebar">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                      Дата и время
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                      Тип операции
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                      Сумма
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                      Источник
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                      ID игрока/бота
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                      Описание
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-primary">
                  {entries.map((entry, index) => {
                    const { date, time } = formatDateTime(entry.created_at);
                    return (
                      <tr key={index} className="hover:bg-surface-sidebar transition-colors">
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="text-sm text-white font-rajdhani">{date}</div>
                          <div className="text-xs text-text-secondary">{time}</div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <span className={`text-sm font-medium font-rajdhani ${getEntryTypeColor(entry.type)}`}>
                            {getEntryTypeName(entry.type)}
                          </span>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <span className="text-sm font-bold text-green-400 font-rajdhani">
                            {formatCurrencyWithSymbol(entry.amount)}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm text-white">
                          {entry.source || '—'}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <span className="text-sm text-accent-primary font-mono">
                            {entry.source_user_id || entry.bot_id || '—'}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm text-text-secondary">
                          {entry.description || '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile Cards */}
            <div className="lg:hidden space-y-4 p-4">
              {entries.map((entry, index) => {
                const { date, time } = formatDateTime(entry.created_at);
                return (
                  <div key={index} className="bg-surface-sidebar rounded-lg p-4 border border-border-primary">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className={`text-sm font-medium font-rajdhani ${getEntryTypeColor(entry.type)}`}>
                          {getEntryTypeName(entry.type)}
                        </div>
                        <div className="text-xs text-text-secondary">{date} {time}</div>
                      </div>
                      <div className="text-sm font-bold text-green-400 font-rajdhani">
                        {formatCurrencyWithSymbol(entry.amount)}
                      </div>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Источник:</span>
                        <span className="text-white">{entry.source || '—'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-secondary">ID:</span>
                        <span className="text-accent-primary font-mono">
                          {entry.source_user_id || entry.bot_id || '—'}
                        </span>
                      </div>
                      {entry.description && (
                        <div className="flex justify-between">
                          <span className="text-text-secondary">Описание:</span>
                          <span className="text-white text-right">{entry.description}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Empty State */}
            {entries.length === 0 && (
              <div className="text-center py-12">
                <div className="text-text-secondary text-lg mb-2">Записи не найдены</div>
                <div className="text-text-secondary text-sm">Попробуйте изменить фильтры поиска</div>
              </div>
            )}

            {/* Pagination */}
            <div className="bg-surface-sidebar px-6 py-4">
              <Pagination
                currentPage={pagination.currentPage}
                totalPages={pagination.totalPages}
                onPageChange={pagination.handlePageChange}
                itemsPerPage={pagination.itemsPerPage}
                totalItems={pagination.totalItems}
                showPageNumbers={false}
              />
            </div>
          </div>
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && commissionSettings && (
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Настройки комиссии</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Комиссия с игр (%)
              </label>
              <div className="text-2xl font-bold text-green-400">
                {(commissionSettings.game_commission * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-sm text-text-secondary">
              Комиссия взимается с каждой ставки при создании игры.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfitAdmin;