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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-lg font-semibold text-white mb-2">Общая прибыль</h3>
            <p className="font-russo text-2xl text-green-400">{formatCurrencyWithSymbol(stats.total_profit)}</p>
          </div>
          
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-lg font-semibold text-white mb-2">Сегодня</h3>
            <p className="font-russo text-2xl text-blue-400">{formatCurrencyWithSymbol(stats.today_profit)}</p>
          </div>
          
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-lg font-semibold text-white mb-2">Эта неделя</h3>
            <p className="font-russo text-2xl text-purple-400">{formatCurrencyWithSymbol(stats.week_profit)}</p>
          </div>
          
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-lg font-semibold text-white mb-2">Этот месяц</h3>
            <p className="font-russo text-2xl text-orange-400">{formatCurrencyWithSymbol(stats.month_profit)}</p>
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