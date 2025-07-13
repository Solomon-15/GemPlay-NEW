import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BetsManagement = () => {
  const [stats, setStats] = useState({
    total_bets: 0,
    total_bets_value: 0,
    active_bets: 0,
    completed_bets: 0,
    cancelled_bets: 0,
    expired_bets: 0,
    average_bet: 0
  });
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchStats();
    fetchBets();
  }, [statusFilter]);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bets/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Ошибка загрузки статистики ставок:', error);
    }
  };

  const fetchBets = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({ limit: '50' });
      if (statusFilter) params.append('status', statusFilter);
      
      // Используем существующий endpoint для игр
      const response = await axios.get(`${API}/admin/games/stats?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setBets(response.data.games || []);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки ставок:', error);
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'COMPLETED': { color: 'bg-green-600', text: 'Завершена' },
      'CANCELLED': { color: 'bg-red-600', text: 'Отменена' },
      'WAITING': { color: 'bg-yellow-600', text: 'Ожидается' },
      'ACTIVE': { color: 'bg-blue-600', text: 'Активна' }
    };
    
    const statusInfo = statusMap[status] || { color: 'bg-gray-600', text: status };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold ${statusInfo.color}`}>
        {statusInfo.text}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Информационные блоки */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Всего ставок</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.total_bets}</p>
              <p className="text-accent-primary text-xs">${stats.total_bets_value.toFixed(2)}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Активных сейчас</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.active_bets}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Завершённых</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.completed_bets}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-red-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Отменённых</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.cancelled_bets}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-orange-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Просроченных</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.expired_bets}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-purple-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Средняя сумма</p>
              <p className="text-white text-lg font-rajdhani font-bold">${stats.average_bet.toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Фильтрация */}
      <div className="flex space-x-2">
        <button
          onClick={() => setStatusFilter('')}
          className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
            statusFilter === '' ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary hover:text-white'
          }`}
        >
          Все
        </button>
        <button
          onClick={() => setStatusFilter('WAITING')}
          className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
            statusFilter === 'WAITING' ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary hover:text-white'
          }`}
        >
          Ожидают
        </button>
        <button
          onClick={() => setStatusFilter('COMPLETED')}
          className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
            statusFilter === 'COMPLETED' ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary hover:text-white'
          }`}
        >
          Завершённые
        </button>
        <button
          onClick={() => setStatusFilter('CANCELLED')}
          className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
            statusFilter === 'CANCELLED' ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary hover:text-white'
          }`}
        >
          Отменённые
        </button>
      </div>

      {/* Таблица ставок */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-white text-lg font-roboto">Загрузка ставок...</div>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-surface-sidebar">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    ID Ставки
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Создатель
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Противник
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Сумма
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Комиссия
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Статус
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Дата создания
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-primary">
                {bets.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-4 py-8 text-center text-text-secondary">
                      Нет данных для отображения
                    </td>
                  </tr>
                ) : (
                  bets.map((bet) => (
                    <tr key={bet.id} className="hover:bg-surface-sidebar hover:bg-opacity-50">
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm font-mono">
                          {bet.id ? bet.id.substring(0, 8) : 'N/A'}...
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm">
                          {bet.creator_username || 'N/A'}
                        </div>
                        <div className="text-text-secondary text-xs">
                          {bet.creator_email || ''}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm">
                          {bet.opponent_username || 'Нет'}
                        </div>
                        {bet.opponent_email && (
                          <div className="text-text-secondary text-xs">
                            {bet.opponent_email}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-accent-primary font-rajdhani font-bold">
                          ${bet.bet_amount?.toFixed(2) || '0.00'}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-yellow-400 font-rajdhani font-bold">
                          ${((bet.bet_amount || 0) * 0.06).toFixed(2)}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        {getStatusBadge(bet.status)}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm">
                          {formatDate(bet.created_at)}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="flex space-x-2">
                          <button className="p-1 bg-blue-600 text-white rounded hover:bg-blue-700" title="Просмотр деталей">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          </button>
                          {bet.status === 'WAITING' && (
                            <button className="p-1 bg-red-600 text-white rounded hover:bg-red-700" title="Отменить">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default BetsManagement;