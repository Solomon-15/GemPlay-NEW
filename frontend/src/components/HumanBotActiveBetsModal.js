import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { formatDollarsAsGems, formatBetAmountAsGems, preloadGemPrices } from '../utils/gemUtils';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HumanBotActiveBetsModal = ({ 
  isOpen, 
  onClose, 
  bot, 
  addNotification 
}) => {
  const [loading, setLoading] = useState(false);
  const [activeBetsData, setActiveBetsData] = useState(null);
  const [showAllBets, setShowAllBets] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [deletingHistory, setDeletingHistory] = useState(false);
  const [gemPrices, setGemPrices] = useState([]);

  // Загрузка цен гемов при открытии модального окна
  useEffect(() => {
    const loadGemPrices = async () => {
      await preloadGemPrices();
    };
    loadGemPrices();
  }, []);

  // Загрузка активных ставок при открытии модального окна
  useEffect(() => {
    if (isOpen && bot) {
      fetchActiveBets();
    }
  }, [isOpen, bot]);

  const fetchActiveBets = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.get(`${API}/admin/human-bots/${bot.id}/active-bets`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data) {
        setActiveBetsData(response.data);
      }
    } catch (error) {
      console.error('Ошибка загрузки активных ставок:', error);
      addNotification?.('Ошибка загрузки активных ставок', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchAllBets = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.get(`${API}/admin/human-bots/${bot.id}/all-bets`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data) {
        setActiveBetsData(response.data);
      }
    } catch (error) {
      console.error('Ошибка загрузки всех ставок:', error);
      addNotification?.('Ошибка загрузки всех ставок', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBetsHistory = async () => {
    console.log('🗑️ Starting delete bets history for bot:', bot.id);
    
    // Показать диалог подтверждения
    const confirmed = window.confirm(
      `Вы уверены, что хотите удалить всю историю завершённых ставок для Human-бота "${bot.name}"?\n\n` +
      'Будут удалены только ставки со статусом "Завершена", "Отменена" и "Архивирована".\n' +
      'Активные ставки останутся нетронутыми.\n\n' +
      'Это действие необратимо!'
    );

    if (!confirmed) {
      console.log('🗑️ User cancelled deletion');
      return;
    }

    try {
      setDeletingHistory(true);
      const token = localStorage.getItem('token');
      
      console.log('🗑️ Making API call to delete completed bets');
      const response = await axios.post(`${API}/admin/human-bots/${bot.id}/delete-completed-bets`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('🗑️ API Response:', response.data);

      if (response.data && response.data.success !== false) {
        const hiddenCount = response.data.hidden_count || 0;
        console.log('🗑️ Hidden count:', hiddenCount);
        
        addNotification?.(`Скрыто ${hiddenCount} завершённых ставок из истории`, 'success');
        
        // Перезагружаем данные
        console.log('🗑️ Reloading bets data');
        if (showAllBets) {
          await fetchAllBets();
        } else {
          await fetchActiveBets();
        }
      } else {
        console.error('🗑️ API returned failure:', response.data);
        addNotification?.('Операция не выполнена', 'error');
      }
    } catch (error) {
      console.error('🗑️ Error deleting history:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка скрытия истории ставок';
      addNotification?.(errorMessage, 'error');
    } finally {
      setDeletingHistory(false);
      console.log('🗑️ Delete operation completed');
    }
  };

  const handleClearCompletedBets = async () => {
    try {
      setClearing(true);
      const token = localStorage.getItem('token');
      
      const response = await axios.post(`${API}/admin/human-bots/${bot.id}/clear-completed-bets`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data && response.data.success !== false) {
        addNotification?.(`Очищено ${response.data.cleared_count || 0} завершенных ставок`, 'success');
        
        // Если показываем все ставки, перезагружаем их, иначе только активные
        if (showAllBets) {
          await fetchAllBets();
        } else {
          await fetchActiveBets();
        }
      }
    } catch (error) {
      console.error('Ошибка очистки завершенных ставок:', error);
      addNotification?.('Ошибка очистки завершенных ставок', 'error');
    } finally {
      setClearing(false);
    }
  };

  const handleShowAllBets = async () => {
    if (!showAllBets) {
      await fetchAllBets();
      setShowAllBets(true);
    } else {
      await fetchActiveBets();
      setShowAllBets(false);
    }
  };

  const handleClose = () => {
    setActiveBetsData(null);
    setShowAllBets(false);
    onClose();
  };

  if (!isOpen || !bot) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 w-full max-w-6xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            {/* Иконка Human-бота */}
            <div className="p-2 bg-purple-600 rounded-lg">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h3 className="font-russo text-xl text-white">
              Активные ставки — {bot.name}
            </h3>
          </div>
          
          {/* Общая сумма в правом верхнем углу */}
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-text-secondary text-sm">Общая сумма</div>
              <div className="text-accent-primary text-2xl font-rajdhani font-bold">
                {activeBetsData?.bets ? 
                  formatDollarsAsGems(activeBetsData.bets.reduce((sum, bet) => sum + (bet.bet_amount || bet.total_bet_amount || 0), 0)) : 
                  '0 Gems'}
              </div>
            </div>
            <button
              onClick={handleClose}
              className="text-text-secondary hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
        
        {loading ? (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary"></div>
            <span className="ml-3 text-text-secondary">
              {showAllBets ? 'Загрузка всех ставок...' : 'Загрузка активных ставок...'}
            </span>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Детальная статистика */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-sm">Активные ставки</div>
                <div className="text-blue-400 text-2xl font-rajdhani font-bold">
                  {activeBetsData?.activeBets || 0}
                </div>
                <div className="text-text-secondary text-xs">
                  Из {bot.bet_limit || 12} максимум
                </div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-sm">Всего ставок</div>
                <div className="text-white text-2xl font-rajdhani font-bold">
                  {activeBetsData?.totalBets || 0}
                </div>
                <div className="text-text-secondary text-xs">
                  {showAllBets ? 'Активные + завершенные' : 'Только активные'}
                </div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-sm">Выигрыши бота</div>
                <div className="text-green-400 text-2xl font-rajdhani font-bold">
                  {activeBetsData?.botWins || 0}
                </div>
                <div className="text-text-secondary text-xs">
                  Побед
                </div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-sm">Выигрыши игроков</div>
                <div className="text-orange-400 text-2xl font-rajdhani font-bold">
                  {activeBetsData?.playerWins || 0}
                </div>
                <div className="text-text-secondary text-xs">
                  Поражений
                </div>
              </div>
            </div>

            {/* Кнопки управления */}
            <div className="flex flex-wrap gap-3 mb-4">
              <button
                onClick={handleShowAllBets}
                disabled={loading}
                className={`px-4 py-2 rounded-lg font-roboto transition-colors ${
                  showAllBets 
                    ? 'bg-accent-primary text-white hover:bg-opacity-80' 
                    : 'bg-surface-sidebar text-white hover:bg-opacity-80'
                } disabled:opacity-50`}
              >
                {showAllBets ? '📋 Показать только активные' : '📜 Показать все ставки'}
              </button>
              
              {showAllBets && (
                <button
                  onClick={handleClearCompletedBets}
                  disabled={clearing || loading}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 font-roboto"
                >
                  {clearing ? '🔄 Очистка...' : '🗑️ Очистить завершенные'}
                </button>
              )}

              <button
                onClick={handleDeleteBetsHistory}
                disabled={deletingHistory || loading}
                className="px-4 py-2 bg-red-800 text-white rounded-lg hover:bg-red-900 transition-colors disabled:opacity-50 font-roboto"
              >
                {deletingHistory ? '🔄 Удаление...' : '🗑️ Удалить всю историю ставок'}
              </button>
            </div>

            {!activeBetsData?.bets || activeBetsData.bets.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-text-secondary text-lg">
                  {showAllBets ? 'У бота нет ставок' : 'У бота нет активных ставок в данный момент'}
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-surface-sidebar">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">№</th>
                      <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">ID</th>
                      <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Дата</th>
                      <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Время</th>
                      <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Сумма</th>
                      <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Ход</th>
                      <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Статус</th>
                      <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Соперник</th>
                      <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Результат</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-primary">
                    {activeBetsData.bets.map((bet, index) => {
                      const betDate = new Date(bet.created_at);
                      const dateStr = betDate.toLocaleDateString('ru-RU');
                      const timeStr = betDate.toLocaleTimeString('ru-RU');
                      
                      // Определяем является ли ставка активной
                      const isActiveBet = ['WAITING', 'ACTIVE', 'REVEAL'].includes(bet.status?.toUpperCase());
                      
                      return (
                        <tr 
                          key={bet.id || index} 
                          className={`transition-colors hover:border-l-4 ${
                            isActiveBet 
                              ? 'hover:bg-green-900 hover:bg-opacity-20 hover:border-green-400' 
                              : 'hover:bg-gray-900 hover:bg-opacity-20 hover:border-gray-400'
                          }`}
                        >
                          <td className="px-4 py-3">
                            <div className="text-sm font-roboto text-white font-bold">
                              {index + 1}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm font-roboto text-white font-mono">
                              {bet.id ? bet.id.substring(0, 8) : `#${index + 1}`}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm font-roboto text-white">
                              {dateStr}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm font-roboto text-white">
                              {timeStr}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm font-roboto font-bold text-accent-primary">
                              {formatDollarsAsGems(bet.bet_amount || bet.total_bet_amount || 0)}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm font-roboto text-white">
                              {bet.creator_gem || bet.selected_gem || '—'}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-roboto font-medium ${
                              bet.status === 'ACTIVE' ? 'bg-green-600 text-white' :
                              bet.status === 'WAITING' ? 'bg-yellow-600 text-white' :
                              bet.status === 'REVEAL' ? 'bg-blue-600 text-white' :
                              bet.status === 'COMPLETED' ? 'bg-purple-600 text-white' :
                              bet.status === 'CANCELLED' ? 'bg-red-600 text-white' :
                              bet.status === 'ARCHIVED' ? 'bg-gray-600 text-white' :
                              'bg-gray-600 text-white'
                            }`}>
                              {bet.status === 'ACTIVE' ? 'Активна' :
                               bet.status === 'WAITING' ? 'Ожидает' :
                               bet.status === 'REVEAL' ? 'Раскрытие' :
                               bet.status === 'COMPLETED' ? 'Завершена' :
                               bet.status === 'CANCELLED' ? 'Отменена' :
                               bet.status === 'ARCHIVED' ? 'Архивирована' :
                               bet.status || 'Неизвестно'}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm font-roboto text-white">
                              {bet.opponent_name || bet.opponent_id || '—'}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="text-sm font-roboto">
                              {bet.status === 'COMPLETED' ? (
                                <span className={`font-bold ${
                                  bet.winner_id === bot.id ? 'text-green-400' : 
                                  bet.winner_id ? 'text-red-400' : 'text-gray-400'
                                }`}>
                                  {bet.winner_id === bot.id ? 'Победа' : 
                                   bet.winner_id ? 'Поражение' : 'Ничья'}
                                </span>
                              ) : bet.status === 'CANCELLED' ? (
                                <span className="text-red-400 font-bold">Отменена</span>
                              ) : bet.status === 'ARCHIVED' ? (
                                <span className="text-gray-400 font-bold">Архивирована</span>
                              ) : (
                                <span className="text-text-secondary">—</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
        
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleClose}
            className="px-4 py-2 bg-surface-sidebar text-white rounded-lg hover:bg-opacity-80 transition-colors font-roboto"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
};

export default HumanBotActiveBetsModal;