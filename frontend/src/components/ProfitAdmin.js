import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { formatCurrencyWithSymbol } from '../utils/economy';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProfitAdmin = ({ user }) => {
  const [stats, setStats] = useState(null);
  const [entries, setEntries] = useState([]);
  const [commissionSettings, setCommissionSettings] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterType, setFilterType] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeTab === 'entries') {
      fetchEntries();
    }
  }, [activeTab, currentPage, filterType]);

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
        page: currentPage.toString(),
        limit: '20'
      });

      if (filterType) params.append('type', filterType);

      const response = await axios.get(`${API}/admin/profit/entries?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setEntries(response.data.entries || []);
      setTotalPages(response.data.total_pages || 1);
    } catch (error) {
      console.error('Ошибка загрузки записей прибыли:', error);
    }
  };

  const getEntryTypeName = (type) => {
    const types = {
      'game_commission': 'Комиссия с игры',
      'shop_sale': 'Продажа в магазине',
      'penalty': 'Штраф',
      'refund': 'Возврат',
      'other': 'Прочее'
    };
    return types[type] || type;
  };

  const getEntryTypeColor = (type) => {
    const colors = {
      'game_commission': 'text-green-400',
      'shop_sale': 'text-blue-400',
      'penalty': 'text-orange-400',
      'refund': 'text-red-400',
      'other': 'text-gray-400'
    };
    return colors[type] || 'text-gray-400';
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
          onClick={() => setActiveTab('entries')}
          className={`px-4 py-2 font-rajdhani font-medium transition-colors ${
            activeTab === 'entries'
              ? 'text-accent-primary border-b-2 border-accent-primary'
              : 'text-text-secondary hover:text-white'
          }`}
        >
          Записи прибыли
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
                  <p className="font-russo text-2xl font-bold text-blue-400">{formatCurrencyWithSymbol(stats.bet_commission || 0)}</p>
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
                  <p className="font-russo text-2xl font-bold text-purple-400">{formatCurrencyWithSymbol(stats.gift_commission || 0)}</p>
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
                  <p className="font-russo text-2xl font-bold text-cyan-400">{formatCurrencyWithSymbol(stats.bot_revenue || 0)}</p>
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
                  <p className="font-russo text-2xl font-bold text-yellow-400">{formatCurrencyWithSymbol(stats.frozen_funds || 0)}</p>
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
                  <p className="font-russo text-2xl font-bold text-green-400">{formatCurrencyWithSymbol(stats.total_profit || 0)}</p>
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
                  <p className="font-russo text-2xl font-bold text-red-400">{formatCurrencyWithSymbol(stats.total_expenses || 0)}</p>
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

      {/* Entries Tab */}
      {activeTab === 'entries' && (
        <div className="space-y-4">
          {/* Filter */}
          <div className="flex items-center space-x-4">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-surface-card border border-border-primary rounded-lg px-4 py-2 text-white"
            >
              <option value="">Все типы</option>
              <option value="game_commission">Комиссия с игр</option>
              <option value="shop_sale">Продажи магазина</option>
              <option value="penalty">Штрафы</option>
              <option value="refund">Возвраты</option>
              <option value="other">Прочее</option>
            </select>
          </div>

          {/* Entries List */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-surface-sidebar">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Дата
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Тип
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Сумма
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Описание
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-primary">
                {entries.map((entry, index) => (
                  <tr key={index} className="hover:bg-surface-sidebar">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      {new Date(entry.created_at).toLocaleDateString('ru-RU')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${getEntryTypeColor(entry.type)}`}>
                        {getEntryTypeName(entry.type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-400">
                      {formatCurrencyWithSymbol(entry.amount)}
                    </td>
                    <td className="px-6 py-4 text-sm text-text-secondary">
                      {entry.description || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="bg-surface-sidebar px-6 py-3 flex items-center justify-between">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white disabled:opacity-50"
                >
                  Предыдущая
                </button>
                <span className="text-text-secondary">
                  Страница {currentPage} из {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white disabled:opacity-50"
                >
                  Следующая
                </button>
              </div>
            )}
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