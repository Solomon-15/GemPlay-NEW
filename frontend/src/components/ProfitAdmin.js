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
  const [activeCategory, setActiveCategory] = useState('bet_commission');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  // Пагинация для истории прибыли
  const pagination = usePagination(1, 10);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeTab === 'history') {
      fetchEntries();
    }
  }, [activeTab, pagination.currentPage, activeCategory, sortBy, sortOrder, dateFilter]);

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
    'bet_commission': {
      name: 'Комиссия от ставок',
      icon: '💰',
      color: 'green',
      description: '3% комиссия с PvP-игр'
    },
    'bot_profit': {
      name: 'Доход от ботов',
      icon: '🤖',
      color: 'blue',
      description: 'Прибыль от циклов ботов'
    },
    'gift_commission': {
      name: 'Комиссия от подарков',
      icon: '🎁',
      color: 'purple',
      description: '3% за передачу гемов'
    }
  };

  const getCategoryBadgeColor = (categoryKey) => {
    const colors = {
      'bet_commission': 'bg-green-600',
      'bot_profit': 'bg-blue-600', 
      'gift_commission': 'bg-purple-600'
    };
    return colors[categoryKey] || 'bg-gray-600';
  };

  const getCategoryBadgeOpacity = (categoryKey) => {
    const colors = {
      'bet_commission': 'bg-green-600/20',
      'bot_profit': 'bg-blue-600/20',
      'gift_commission': 'bg-purple-600/20'
    };
    return colors[categoryKey] || 'bg-gray-600/20';
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
          {/* Категории транзакций */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-6">Категории транзакций</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(categories).map(([key, category]) => (
                <button
                  key={key}
                  onClick={() => {
                    setActiveCategory(key);
                    pagination.goToPage(1);
                  }}
                  className={`p-6 rounded-lg border-2 transition-all duration-200 text-left hover:scale-105 ${
                    activeCategory === key
                      ? (category.color === 'green' ? 'border-green-500 bg-green-500/10' :
                         category.color === 'blue' ? 'border-blue-500 bg-blue-500/10' :
                         'border-purple-500 bg-purple-500/10')
                      : 'border-border-primary hover:border-accent-primary'
                  }`}
                >
                  <div className="flex items-center space-x-3 mb-3">
                    <div className={`p-3 rounded-lg ${getCategoryBadgeOpacity(key)}`}>
                      <span className="text-2xl">{category.icon}</span>
                    </div>
                    <div>
                      <h4 className={`font-rajdhani font-bold text-lg ${
                        activeCategory === key ? 
                          (category.color === 'green' ? 'text-green-400' :
                           category.color === 'blue' ? 'text-blue-400' :
                           'text-purple-400') : 'text-white'
                      }`}>
                        {category.name}
                      </h4>
                    </div>
                  </div>
                  <p className="text-text-secondary text-sm">{category.description}</p>
                  
                  <div className={`mt-3 text-xs font-bold ${
                    activeCategory === key ? 
                      (category.color === 'green' ? 'text-green-400' :
                       category.color === 'blue' ? 'text-blue-400' :
                       'text-purple-400') : 'text-accent-primary'
                  }`}>
                    {activeCategory === key ? `${entries.length} записей` : 'Нажмите для просмотра'}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Фильтры и сортировка */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
              <div className="flex items-center space-x-4">
                <h3 className="font-rajdhani text-lg font-bold text-white">
                  {categories[activeCategory].icon} {categories[activeCategory].name}
                </h3>
                <span className={`px-2 py-1 text-xs rounded-full font-bold ${getCategoryBadgeColor(activeCategory)} text-white`}>
                  {entries.length} записей
                </span>
              </div>
              
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
                <div className="flex space-x-2">
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-primary"
                  >
                    <option value="date">По дате</option>
                    <option value="amount">По сумме</option>
                    <option value="source">По источнику</option>
                  </select>
                  
                  <button
                    onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                    className="px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white hover:bg-surface-card transition-colors"
                    title={sortOrder === 'asc' ? 'По возрастанию' : 'По убыванию'}
                  >
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </button>
                </div>
                
                <div className="flex space-x-2">
                  <input
                    type="date"
                    value={dateFilter.from}
                    onChange={(e) => setDateFilter(prev => ({ ...prev, from: e.target.value }))}
                    className="bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-primary"
                    placeholder="От"
                  />
                  <input
                    type="date"
                    value={dateFilter.to}
                    onChange={(e) => setDateFilter(prev => ({ ...prev, to: e.target.value }))}
                    className="bg-surface-sidebar border border-border-primary rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-primary"
                    placeholder="До"
                  />
                </div>
                
                <button
                  onClick={exportToCSV}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-rajdhani font-bold rounded-lg transition-colors text-sm"
                >
                  📥 CSV
                </button>
              </div>
            </div>
          </div>

          {/* Компактные карточки транзакций */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
            <div className="space-y-2 p-4">
              {entries.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">{categories[activeCategory].icon}</div>
                  <h4 className="font-rajdhani text-xl font-bold text-white mb-2">Нет транзакций</h4>
                  <p className="text-text-secondary">В категории "{categories[activeCategory].name}" пока нет данных</p>
                </div>
              ) : (
                entries.map((entry, index) => {
                  const { date, time } = formatDateTime(entry.created_at);
                  return (
                    <div key={index} className="bg-surface-sidebar rounded-lg p-4 border border-border-primary hover:border-accent-primary transition-all duration-200 hover:shadow-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4 flex-1">
                          <div className={`w-3 h-12 rounded-full ${getCategoryBadgeColor(activeCategory)}`}></div>
                          
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-1">
                              <div className="text-white font-rajdhani font-bold">
                                {date} {time}
                              </div>
                              <div className="text-xs text-text-secondary font-mono">
                                #TX-{entry.id?.substring(0, 6) || 'XXXXXX'}
                              </div>
                            </div>
                            
                            <div className="text-sm text-text-secondary">
                              {entry.description || 'Описание отсутствует'}
                            </div>
                            
                            {entry.source && (
                              <div className="text-xs text-accent-primary mt-1">
                                Источник: {entry.source}
                              </div>
                            )}
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <div className={`text-2xl font-bold font-russo ${
                            categories[activeCategory].color === 'green' ? 'text-green-400' : 
                            categories[activeCategory].color === 'blue' ? 'text-blue-400' : 
                            'text-purple-400'
                          }`}>
                            {formatCurrencyWithSymbol(entry.amount, true)}
                          </div>
                          {entry.source_user_id && (
                            <div className="text-xs text-text-secondary font-mono">
                              ID: {entry.source_user_id.substring(0, 8)}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
            
            {pagination.totalPages > 1 && (
              <div className="border-t border-border-primary p-4">
                <Pagination
                  currentPage={pagination.currentPage}
                  totalPages={pagination.totalPages}
                  onPageChange={pagination.goToPage}
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
    </div>
  );
};

export default ProfitAdmin;