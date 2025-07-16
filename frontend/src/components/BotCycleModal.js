import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationContext';
import { useApi } from '../hooks/useApi';

const BotCycleModal = ({ bot, onClose }) => {
  const [cycleData, setCycleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { showErrorRU } = useNotifications();

  useEffect(() => {
    if (bot && bot.id) {
      fetchCycleData();
    }
  }, [bot]);

  const fetchCycleData = async () => {
    try {
      const response = await axios.get(`${API}/admin/bots/${bot.id}/cycle-bets`, getApiConfig());
      
      if (response.data.success) {
        setCycleData(response.data);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching cycle data:', error);
      showErrorRU('Ошибка загрузки данных цикла');
      setLoading(false);
    }
  };

  const formatGems = (gems) => {
    if (!gems || typeof gems !== 'object') return '-';
    
    return Object.entries(gems)
      .filter(([_, quantity]) => quantity > 0)
      .map(([gem, quantity]) => `${gem}: ${quantity}`)
      .join(', ');
  };

  const formatTime = (dateString) => {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-600 text-white';
      case 'active':
        return 'bg-yellow-600 text-white';
      case 'waiting':
        return 'bg-gray-600 text-gray-300';
      case 'cancelled':
        return 'bg-red-600 text-white';
      default:
        return 'bg-gray-600 text-gray-300';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Завершено';
      case 'active':
        return 'Активно';
      case 'waiting':
        return 'Ожидание';
      case 'cancelled':
        return 'Отменено';
      default:
        return 'Неизвестно';
    }
  };

  const getResultText = (result) => {
    switch (result) {
      case 'win':
        return <span className="font-bold text-green-400">Победа</span>;
      case 'loss':
        return <span className="font-bold text-red-400">Поражение</span>;
      case 'draw':
        return <span className="font-bold text-yellow-400">Ничья</span>;
      default:
        return <span className="text-gray-400">-</span>;
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary mx-auto mb-2"></div>
          <p className="text-text-secondary">Загрузка данных цикла...</p>
        </div>
      </div>
    );
  }

  if (!cycleData) {
    return (
      <div className="space-y-4">
        <div className="text-center py-8">
          <p className="text-text-secondary">Не удалось загрузить данные цикла</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Статистика цикла */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="bg-surface-sidebar rounded-lg p-3">
          <div className="text-text-secondary text-sm">Текущий цикл</div>
          <div className="text-lg font-bold text-white">
            {cycleData.current_cycle}/{cycleData.cycle_total}
          </div>
        </div>
        <div className="bg-surface-sidebar rounded-lg p-3">
          <div className="text-text-secondary text-sm">Сумма цикла</div>
          <div className="text-lg font-bold text-blue-400">
            ${cycleData.cycle_total_amount}
          </div>
        </div>
        <div className="bg-surface-sidebar rounded-lg p-3">
          <div className="text-text-secondary text-sm">Целевой Win Rate</div>
          <div className="text-lg font-bold text-green-400">
            {cycleData.win_rate_percent}%
          </div>
        </div>
      </div>

      {/* Таблица ставок */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-text-secondary">
          <thead className="text-xs text-text-secondary uppercase bg-surface-sidebar">
            <tr>
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">Сумма</th>
              <th className="px-4 py-3">Гемы</th>
              <th className="px-4 py-3">Противник</th>
              <th className="px-4 py-3">Статус</th>
              <th className="px-4 py-3">Результат</th>
              <th className="px-4 py-3">Время</th>
            </tr>
          </thead>
          <tbody>
            {cycleData.bets.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-text-secondary">
                  Нет ставок в текущем цикле
                </td>
              </tr>
            ) : (
              cycleData.bets.map((bet, index) => (
                <tr key={index} className="bg-surface-card border-b border-border-primary">
                  <td className="px-4 py-3 font-bold text-white">{bet.position}</td>
                  <td className="px-4 py-3 text-blue-400">${bet.amount}</td>
                  <td className="px-4 py-3">
                    <span className="text-purple-400">
                      {formatGems(bet.gems)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-white">
                    {bet.opponent || 'Ожидание'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(bet.status)}`}>
                      {getStatusText(bet.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {getResultText(bet.result)}
                  </td>
                  <td className="px-4 py-3 text-text-secondary">
                    {formatTime(bet.created_at)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <button
          onClick={onClose}
          className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold"
        >
          Закрыть
        </button>
      </div>
    </div>
  );
};

export default BotCycleModal;