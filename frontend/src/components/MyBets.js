import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MyBets = ({ user, onUpdateUser }) => {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalBets, setTotalBets] = useState(0);
  const [filters, setFilters] = useState({
    status: 'all', // all, WAITING, ACTIVE, COMPLETED
    dateRange: 'all', // all, today, week, month
    result: 'all', // all, won, lost, draw (only for completed bets)
    sortBy: 'created_at',
    sortOrder: 'desc'
  });
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedBet, setSelectedBet] = useState(null);
  const [stats, setStats] = useState({
    totalGames: 0,
    totalWon: 0,
    totalLost: 0,
    totalDraw: 0,
    netProfit: 0,
    totalWinnings: 0,
    totalLosses: 0,
    winRate: 0
  });
  
  const ITEMS_PER_PAGE = 10;

  const fetchMyBets = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        page: currentPage.toString(),
        per_page: ITEMS_PER_PAGE.toString(),
        status_filter: filters.status,
        date_filter: filters.dateRange,
        result_filter: filters.result,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder
      });

      const response = await axios.get(
        `${API}/games/my-bets-paginated?${params.toString()}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.success) {
        setBets(response.data.games);
        setTotalBets(response.data.pagination.total_count);
        setTotalPages(response.data.pagination.total_pages);

        // Update stats
        const statsData = response.data.stats;
        const commission = statsData.total_winnings * 0.03; // 3% commission
        const netProfit = statsData.total_winnings - statsData.total_losses - commission;
        
        setStats({
          totalGames: statsData.total_games,
          totalWon: statsData.total_won,
          totalLost: statsData.total_lost,
          totalDraw: statsData.total_draw,
          netProfit: netProfit,
          totalWinnings: statsData.total_winnings,
          totalLosses: statsData.total_losses,
          winRate: statsData.total_games > 0 ? (statsData.total_won / statsData.total_games * 100) : 0
        });
      }

    } catch (error) {
      console.error('Error fetching my bets:', error);
      // Fall back to old API if new one fails
      try {
        const betsResponse = await axios.get(`${API}/games/my-bets`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        const historyResponse = await axios.get(
          `${API}/games/history`,
          { headers: { Authorization: `Bearer ${token}` } }
        );

        // Combine and process data (old logic)
        const activeBets = betsResponse.data.filter(bet => 
          bet.status === 'WAITING' || bet.status === 'ACTIVE'
        );
        
        const completedBets = historyResponse.data?.games || [];
        const allBets = [...activeBets, ...completedBets];

        // Apply filters
        let filteredBets = allBets;
        if (filters.status !== 'all') {
          if (filters.status === 'COMPLETED') {
            filteredBets = completedBets;
            if (filters.result !== 'all') {
              filteredBets = filteredBets.filter(bet => bet.result === filters.result);
            }
          } else {
            filteredBets = activeBets.filter(bet => bet.status === filters.status);
          }
        }

        // Sort bets
        filteredBets.sort((a, b) => {
          let aValue, bValue;
          switch (filters.sortBy) {
            case 'bet_amount':
              aValue = a.bet_amount;
              bValue = b.bet_amount;
              break;
            case 'status':
              aValue = a.status;
              bValue = b.status;
              break;
            default:
              aValue = new Date(a.created_at);
              bValue = new Date(b.created_at);
          }
          
          if (filters.sortOrder === 'desc') {
            return aValue > bValue ? -1 : 1;
          } else {
            return aValue > bValue ? 1 : -1;
          }
        });

        // Pagination
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIndex = startIndex + ITEMS_PER_PAGE;
        const paginatedBets = filteredBets.slice(startIndex, endIndex);

        setBets(paginatedBets);
        setTotalBets(filteredBets.length);
        setTotalPages(Math.ceil(filteredBets.length / ITEMS_PER_PAGE));

        // Update stats from history API
        if (historyResponse.data?.stats) {
          const statsData = historyResponse.data.stats;
          const commission = statsData.total_winnings * 0.03; // 3% commission
          const netProfit = statsData.total_winnings - statsData.total_losses - commission;
          
          setStats({
            totalGames: statsData.total_games,
            totalWon: statsData.total_won,
            totalLost: statsData.total_lost,
            totalDraw: statsData.total_draw,
            netProfit: netProfit,
            totalWinnings: statsData.total_winnings,
            totalLosses: statsData.total_losses,
            winRate: statsData.total_games > 0 ? (statsData.total_won / statsData.total_games * 100) : 0
          });
        }
      } catch (fallbackError) {
        console.error('Error with fallback API:', fallbackError);
      }
    } finally {
      setLoading(false);
    }
  }, [filters, currentPage]);

  useEffect(() => {
    fetchMyBets();
  }, [fetchMyBets]);

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchMyBets();
    }, 10000);
    return () => clearInterval(interval);
  }, [fetchMyBets]);

  const handleCancelBet = async (gameId) => {
    if (!window.confirm('Вы уверены, что хотите отменить эту ставку?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/games/${gameId}/cancel`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchMyBets();
      onUpdateUser && onUpdateUser();
    } catch (error) {
      console.error('Error canceling bet:', error);
      alert('Ошибка при отмене ставки');
    }
  };

  const handleRepeatBet = (bet) => {
    // This would navigate to create game with pre-filled data
    // For now, just log the bet data
    console.log('Repeat bet:', bet);
    alert('Функция повтора ставки будет реализована в следующих версиях');
  };

  const showBetDetails = (bet) => {
    setSelectedBet(bet);
    setShowDetailsModal(true);
  };

  const getStatusBadge = (status, result = null) => {
    let bgColor, textColor, text;
    
    if (status === 'WAITING') {
      bgColor = 'bg-yellow-500';
      textColor = 'text-white';
      text = 'Ожидание';
    } else if (status === 'ACTIVE') {
      bgColor = 'bg-blue-500';
      textColor = 'text-white';
      text = 'Активная';
    } else if (status === 'COMPLETED') {
      if (result === 'won') {
        bgColor = 'bg-green-500';
        textColor = 'text-white';
        text = 'Победа';
      } else if (result === 'lost') {
        bgColor = 'bg-red-500';
        textColor = 'text-white';
        text = 'Поражение';
      } else {
        bgColor = 'bg-gray-500';
        textColor = 'text-white';
        text = 'Ничья';
      }
    } else {
      bgColor = 'bg-gray-500';
      textColor = 'text-white';
      text = status;
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${bgColor} ${textColor}`}>
        {text}
      </span>
    );
  };

  const renderGems = (betGems) => {
    if (!betGems || typeof betGems !== 'object') return null;
    
    return (
      <div className="flex space-x-1">
        {Object.entries(betGems).map(([gemType, quantity]) => (
          quantity > 0 && (
            <div key={gemType} className="flex items-center space-x-1 bg-gray-700 rounded px-2 py-1">
              <img 
                src={`/gems/gem-${gemType.toLowerCase()}.svg`} 
                alt={gemType}
                className="w-4 h-4"
              />
              <span className="text-xs text-white">{quantity}</span>
            </div>
          )
        ))}
      </div>
    );
  };

  if (loading && bets.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-white text-lg">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="p-6 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-russo text-white mb-4">Мои Ставки</h1>
        
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-surface-card border border-border-primary rounded-lg p-4">
            <div className="text-sm text-text-secondary mb-1">Всего игр</div>
            <div className="text-2xl font-bold text-white">{stats.totalGames}</div>
          </div>
          <div className="bg-surface-card border border-border-primary rounded-lg p-4">
            <div className="text-sm text-text-secondary mb-1">Побед</div>
            <div className="text-2xl font-bold text-green-400">{stats.totalWon}</div>
            <div className="text-xs text-text-secondary">({stats.winRate.toFixed(1)}%)</div>
          </div>
          <div className="bg-surface-card border border-border-primary rounded-lg p-4">
            <div className="text-sm text-text-secondary mb-1">Поражений</div>
            <div className="text-2xl font-bold text-red-400">{stats.totalLost}</div>
          </div>
          <div className="bg-surface-card border border-border-primary rounded-lg p-4">
            <div className="text-sm text-text-secondary mb-1">Чистая прибыль</div>
            <div className={`text-2xl font-bold ${stats.netProfit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${stats.netProfit.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-surface-card border border-border-primary rounded-lg p-4 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm text-text-secondary mb-2">Статус</label>
            <select 
              value={filters.status} 
              onChange={(e) => {
                setFilters(prev => ({...prev, status: e.target.value}));
                setCurrentPage(1);
              }}
              className="w-full bg-surface-sidebar border border-border-primary rounded px-3 py-2 text-white text-sm"
            >
              <option value="all">Все</option>
              <option value="WAITING">Ожидание</option>
              <option value="ACTIVE">Активные</option>
              <option value="COMPLETED">Завершенные</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-text-secondary mb-2">Период</label>
            <select 
              value={filters.dateRange} 
              onChange={(e) => {
                setFilters(prev => ({...prev, dateRange: e.target.value}));
                setCurrentPage(1);
              }}
              className="w-full bg-surface-sidebar border border-border-primary rounded px-3 py-2 text-white text-sm"
            >
              <option value="all">Все время</option>
              <option value="today">Сегодня</option>
              <option value="week">Неделя</option>
              <option value="month">Месяц</option>
            </select>
          </div>

          {filters.status === 'COMPLETED' && (
            <div>
              <label className="block text-sm text-text-secondary mb-2">Результат</label>
              <select 
                value={filters.result} 
                onChange={(e) => {
                  setFilters(prev => ({...prev, result: e.target.value}));
                  setCurrentPage(1);
                }}
                className="w-full bg-surface-sidebar border border-border-primary rounded px-3 py-2 text-white text-sm"
              >
                <option value="all">Все</option>
                <option value="won">Победы</option>
                <option value="lost">Поражения</option>
                <option value="draw">Ничьи</option>
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm text-text-secondary mb-2">Сортировка</label>
            <select 
              value={filters.sortBy} 
              onChange={(e) => {
                setFilters(prev => ({...prev, sortBy: e.target.value}));
                setCurrentPage(1);
              }}
              className="w-full bg-surface-sidebar border border-border-primary rounded px-3 py-2 text-white text-sm"
            >
              <option value="created_at">По дате</option>
              <option value="bet_amount">По сумме</option>
              <option value="status">По статусу</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-text-secondary mb-2">Порядок</label>
            <select 
              value={filters.sortOrder} 
              onChange={(e) => {
                setFilters(prev => ({...prev, sortOrder: e.target.value}));
                setCurrentPage(1);
              }}
              className="w-full bg-surface-sidebar border border-border-primary rounded px-3 py-2 text-white text-sm"
            >
              <option value="desc">По убыванию</option>
              <option value="asc">По возрастанию</option>
            </select>
          </div>
        </div>
      </div>

      {/* Bets List */}
      <div className="bg-surface-card border border-border-primary rounded-lg">
        {bets.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-text-secondary mb-4">Ставки не найдены</div>
            <div className="text-sm text-text-secondary">
              Попробуйте изменить фильтры или создать новую ставку
            </div>
          </div>
        ) : (
          <>
            {/* Desktop Table */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead className="bg-surface-sidebar border-b border-border-primary">
                  <tr>
                    <th className="text-left p-4 text-text-secondary font-medium">Дата</th>
                    <th className="text-left p-4 text-text-secondary font-medium">Противник</th>
                    <th className="text-left p-4 text-text-secondary font-medium">Ставка</th>
                    <th className="text-left p-4 text-text-secondary font-medium">Гемы</th>
                    <th className="text-left p-4 text-text-secondary font-medium">Статус</th>
                    <th className="text-left p-4 text-text-secondary font-medium">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {bets.map((bet, index) => (
                    <tr key={bet.game_id || bet.id || index} className="border-b border-border-primary hover:bg-surface-sidebar/50">
                      <td className="p-4">
                        <div className="text-white text-sm">
                          {new Date(bet.created_at).toLocaleString('ru-RU')}
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="text-white">
                          {bet.opponent ? bet.opponent.username : (bet.opponent_username || 'Ожидание')}
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="text-accent-primary font-bold">
                          ${bet.bet_amount.toFixed(2)}
                        </div>
                      </td>
                      <td className="p-4">
                        {renderGems(bet.bet_gems)}
                      </td>
                      <td className="p-4">
                        {getStatusBadge(bet.status, bet.result)}
                      </td>
                      <td className="p-4">
                        <div className="flex space-x-2">
                          {bet.status === 'WAITING' && bet.is_creator && (
                            <button
                              onClick={() => handleCancelBet(bet.game_id || bet.id)}
                              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
                            >
                              Отменить
                            </button>
                          )}
                          {bet.status === 'COMPLETED' && (
                            <button
                              onClick={() => handleRepeatBet(bet)}
                              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                            >
                              Повторить
                            </button>
                          )}
                          <button
                            onClick={() => showBetDetails(bet)}
                            className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded transition-colors"
                          >
                            Детали
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Cards */}
            <div className="md:hidden">
              {bets.map((bet, index) => (
                <div key={bet.game_id || bet.id || index} className="p-4 border-b border-border-primary last:border-b-0">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="text-white font-medium">
                        {bet.opponent ? bet.opponent.username : (bet.opponent_username || 'Ожидание')}
                      </div>
                      <div className="text-text-secondary text-sm">
                        {new Date(bet.created_at).toLocaleString('ru-RU')}
                      </div>
                    </div>
                    {getStatusBadge(bet.status, bet.result)}
                  </div>
                  
                  <div className="flex justify-between items-center mb-3">
                    <div className="text-accent-primary font-bold">
                      ${bet.bet_amount.toFixed(2)}
                    </div>
                    {renderGems(bet.bet_gems)}
                  </div>

                  <div className="flex space-x-2">
                    {bet.status === 'WAITING' && bet.is_creator && (
                      <button
                        onClick={() => handleCancelBet(bet.game_id || bet.id)}
                        className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
                      >
                        Отменить
                      </button>
                    )}
                    {bet.status === 'COMPLETED' && (
                      <button
                        onClick={() => handleRepeatBet(bet)}
                        className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                      >
                        Повторить
                      </button>
                    )}
                    <button
                      onClick={() => showBetDetails(bet)}
                      className="flex-1 px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded transition-colors"
                    >
                      Детали
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-border-primary">
            <div className="flex justify-between items-center">
              <div className="text-text-secondary text-sm">
                Показано {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, totalBets)}-{Math.min(currentPage * ITEMS_PER_PAGE, totalBets)} из {totalBets}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 bg-surface-sidebar border border-border-primary rounded text-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Назад
                </button>
                <span className="px-3 py-1 text-white">
                  {currentPage} / {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 bg-surface-sidebar border border-border-primary rounded text-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Далее
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {showDetailsModal && selectedBet && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-surface-card border border-border-primary rounded-lg max-w-md w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-russo text-white">Детали ставки</h3>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-text-secondary hover:text-white"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-text-secondary text-sm mb-1">ID игры</label>
                  <div className="text-white">{selectedBet.game_id || selectedBet.id}</div>
                </div>

                <div>
                  <label className="block text-text-secondary text-sm mb-1">Противник</label>
                  <div className="text-white">
                    {selectedBet.opponent ? selectedBet.opponent.username : (selectedBet.opponent_username || 'Ожидание')}
                  </div>
                </div>

                <div>
                  <label className="block text-text-secondary text-sm mb-1">Сумма ставки</label>
                  <div className="text-accent-primary font-bold">${selectedBet.bet_amount.toFixed(2)}</div>
                </div>

                <div>
                  <label className="block text-text-secondary text-sm mb-1">Выбранные гемы</label>
                  {renderGems(selectedBet.bet_gems)}
                </div>

                <div>
                  <label className="block text-text-secondary text-sm mb-1">Статус</label>
                  {getStatusBadge(selectedBet.status, selectedBet.result)}
                </div>

                {selectedBet.status === 'COMPLETED' && selectedBet.my_move && (
                  <>
                    <div>
                      <label className="block text-text-secondary text-sm mb-1">Ваш ход</label>
                      <div className="text-white">{selectedBet.my_move}</div>
                    </div>
                    <div>
                      <label className="block text-text-secondary text-sm mb-1">Ход противника</label>
                      <div className="text-white">{selectedBet.opponent_move || 'Неизвестно'}</div>
                    </div>
                  </>
                )}

                {selectedBet.status === 'COMPLETED' && selectedBet.commission !== undefined && (
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Комиссия</label>
                    <div className="text-text-secondary">${(selectedBet.commission || selectedBet.bet_amount * 0.03).toFixed(2)}</div>
                  </div>
                )}

                <div>
                  <label className="block text-text-secondary text-sm mb-1">Создана</label>
                  <div className="text-white text-sm">
                    {new Date(selectedBet.created_at).toLocaleString('ru-RU')}
                  </div>
                </div>

                {selectedBet.completed_at && (
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Завершена</label>
                    <div className="text-white text-sm">
                      {new Date(selectedBet.completed_at).toLocaleString('ru-RU')}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="px-4 py-2 bg-surface-sidebar border border-border-primary rounded text-white hover:bg-surface-card transition-colors"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyBets;