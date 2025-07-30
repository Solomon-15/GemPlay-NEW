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
        const token = localStorage.getItem('token');
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
    if (!window.confirm('Are you sure you want to cancel this bet?')) {
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
      alert('Error canceling bet');
    }
  };

  const handleRepeatBet = (bet) => {
    // This would navigate to create game with pre-filled data
    // For now, just log the bet data
    console.log('Repeat bet:', bet);
    alert('Repeat bet functionality will be implemented in future versions');
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
      text = 'Waiting';
    } else if (status === 'ACTIVE') {
      bgColor = 'bg-blue-500';
      textColor = 'text-white';
      text = 'Active';
    } else if (status === 'COMPLETED') {
      if (result === 'won') {
        bgColor = 'bg-green-500';
        textColor = 'text-white';
        text = 'Won';
      } else if (result === 'lost') {
        bgColor = 'bg-red-500';
        textColor = 'text-white';
        text = 'Lost';
      } else {
        bgColor = 'bg-gray-500';
        textColor = 'text-white';
        text = 'Draw';
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
    if (!betGems || typeof betGems !== 'object') return (
      <div className="text-text-secondary text-sm">No gems</div>
    );
    
    const gemsArray = Object.entries(betGems).filter(([gemType, quantity]) => quantity > 0);
    
    if (gemsArray.length === 0) return (
      <div className="text-text-secondary text-sm">No gems</div>
    );
    
    return (
      <div className="flex flex-wrap gap-1">
        {gemsArray.map(([gemType, quantity]) => (
          <div key={gemType} className="flex items-center space-x-1 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded px-2 py-1">
            <img 
              src={`/gems/gem-${gemType.toLowerCase()}.svg`} 
              alt={gemType}
              className="w-4 h-4"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.textContent = `${gemType.toUpperCase()}: ${quantity}`;
              }}
            />
            <span className="text-xs text-white font-rajdhani font-bold">{quantity}</span>
          </div>
        ))}
      </div>
    );
  };

  if (loading && bets.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Loading...</div>
      </div>
    );
  }

  const InfoBlock = ({ title, value, icon, color }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg mb-2 ${color}`}>
        {icon}
      </div>
      <h3 className="font-rajdhani font-bold text-lg text-white">{title}</h3>
      <p className="font-roboto text-2xl font-bold text-accent-primary">
        {typeof value === 'number' ? (value >= 0 ? `$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`) : value}
      </p>
    </div>
  );

  const SectionBlock = ({ title, icon, children, color = 'text-blue-400' }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className={color}>{icon}</div>
          <h3 className="font-rajdhani font-bold text-lg text-white">{title}</h3>
        </div>
      </div>
      {children}
    </div>
  );

  return (
    <div className="p-6 min-h-screen">
      {/* Header */}
      <div className="mb-6 max-w-7xl mx-auto">
        <h1 className="text-3xl font-russo text-white mb-4">My Bets</h1>
        
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <InfoBlock
            title="Total Games"
            value={stats.totalGames}
            color="bg-blue-600"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
          />
          <InfoBlock
            title="Wins"
            value={`${stats.totalWon} (${stats.winRate.toFixed(1)}%)`}
            color="bg-green-600"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <InfoBlock
            title="Losses"
            value={stats.totalLost}
            color="bg-red-600"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <InfoBlock
            title="Net Profit"
            value={stats.netProfit}
            color={stats.netProfit >= 0 ? "bg-green-600" : "bg-red-600"}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>
      </div>

      <div className="max-w-7xl mx-auto">
        {/* Filters */}
        <SectionBlock
          title="Filters and Sorting"
          color="text-purple-400"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.707A1 1 0 013 7V4z" />
            </svg>
          }
        >
          <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm text-text-secondary mb-2">Status</label>
                <select 
                  value={filters.status} 
                  onChange={(e) => {
                    setFilters(prev => ({...prev, status: e.target.value}));
                    setCurrentPage(1);
                  }}
                  className="w-full bg-surface-card border border-accent-primary border-opacity-30 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-primary"
                >
                  <option value="all">All</option>
                  <option value="WAITING">Waiting</option>
                  <option value="ACTIVE">Active</option>
                  <option value="COMPLETED">Completed</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-text-secondary mb-2">Period</label>
                <select 
                  value={filters.dateRange} 
                  onChange={(e) => {
                    setFilters(prev => ({...prev, dateRange: e.target.value}));
                    setCurrentPage(1);
                  }}
                  className="w-full bg-surface-card border border-accent-primary border-opacity-30 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-primary"
                >
                  <option value="all">All Time</option>
                  <option value="today">Today</option>
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                </select>
              </div>

              {filters.status === 'COMPLETED' && (
                <div>
                  <label className="block text-sm text-text-secondary mb-2">Result</label>
                  <select 
                    value={filters.result} 
                    onChange={(e) => {
                      setFilters(prev => ({...prev, result: e.target.value}));
                      setCurrentPage(1);
                    }}
                    className="w-full bg-surface-card border border-accent-primary border-opacity-30 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-primary"
                  >
                    <option value="all">All</option>
                    <option value="won">Wins</option>
                    <option value="lost">Losses</option>
                    <option value="draw">Draws</option>
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm text-text-secondary mb-2">Sort By</label>
                <select 
                  value={filters.sortBy} 
                  onChange={(e) => {
                    setFilters(prev => ({...prev, sortBy: e.target.value}));
                    setCurrentPage(1);
                  }}
                  className="w-full bg-surface-card border border-accent-primary border-opacity-30 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-primary"
                >
                  <option value="created_at">By Date</option>
                  <option value="bet_amount">By Amount</option>
                  <option value="status">By Status</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-text-secondary mb-2">Order</label>
                <select 
                  value={filters.sortOrder} 
                  onChange={(e) => {
                    setFilters(prev => ({...prev, sortOrder: e.target.value}));
                    setCurrentPage(1);
                  }}
                  className="w-full bg-surface-card border border-accent-primary border-opacity-30 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-primary"
                >
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </div>
            </div>
          </div>
        </SectionBlock>

        {/* Bets List */}
        <SectionBlock
          title="My Bets"
          color="text-green-400"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          }
        >
          {bets.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-text-secondary mb-4">No bets found</div>
              <div className="text-sm text-text-secondary">
                Try changing filters or create a new bet
              </div>
            </div>
          ) : (
            <>
              {/* Desktop Table */}
              <div className="hidden md:block overflow-x-auto">
                <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg">
                  <table className="w-full">
                    <thead className="bg-surface-sidebar border-b border-accent-primary border-opacity-30">
                      <tr>
                        <th className="text-left p-4 text-text-secondary font-rajdhani font-bold">Date</th>
                        <th className="text-left p-4 text-text-secondary font-rajdhani font-bold">Opponent</th>
                        <th className="text-left p-4 text-text-secondary font-rajdhani font-bold">Bet Amount</th>
                        <th className="text-left p-4 text-text-secondary font-rajdhani font-bold">Gems</th>
                        <th className="text-left p-4 text-text-secondary font-rajdhani font-bold">Status</th>
                        <th className="text-left p-4 text-text-secondary font-rajdhani font-bold">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bets.map((bet, index) => (
                        <tr key={bet.game_id || bet.id || index} className="border-b border-accent-primary border-opacity-10 hover:bg-surface-sidebar/30">
                          <td className="p-4">
                            <div className="text-white text-sm font-roboto">
                              {new Date(bet.created_at).toLocaleString('en-US')}
                            </div>
                          </td>
                          <td className="p-4">
                            <div className="text-white font-rajdhani font-bold">
                              {bet.opponent ? bet.opponent.username : (bet.opponent_username || 'Waiting')}
                            </div>
                          </td>
                          <td className="p-4">
                            <div className="text-accent-primary font-rajdhani font-bold text-lg">
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
                                  className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded font-rajdhani font-bold transition-colors"
                                >
                                  Cancel
                                </button>
                              )}
                              {bet.status === 'COMPLETED' && (
                                <button
                                  onClick={() => handleRepeatBet(bet)}
                                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded font-rajdhani font-bold transition-colors"
                                >
                                  Repeat
                                </button>
                              )}
                              <button
                                onClick={() => showBetDetails(bet)}
                                className="px-3 py-1 bg-surface-sidebar border border-accent-primary border-opacity-30 hover:border-opacity-50 text-white text-xs rounded font-rajdhani font-bold transition-colors"
                              >
                                Details
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Mobile Cards */}
              <div className="md:hidden space-y-4">
                {bets.map((bet, index) => (
                  <div key={bet.game_id || bet.id || index} className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="text-white font-rajdhani font-bold">
                          {bet.opponent ? bet.opponent.username : (bet.opponent_username || 'Waiting')}
                        </div>
                        <div className="text-text-secondary text-sm font-roboto">
                          {new Date(bet.created_at).toLocaleString('en-US')}
                        </div>
                      </div>
                      {getStatusBadge(bet.status, bet.result)}
                    </div>
                    
                    <div className="flex justify-between items-center mb-3">
                      <div className="text-accent-primary font-rajdhani font-bold text-lg">
                        ${bet.bet_amount.toFixed(2)}
                      </div>
                      {renderGems(bet.bet_gems)}
                    </div>

                    <div className="flex space-x-2">
                      {bet.status === 'WAITING' && bet.is_creator && (
                        <button
                          onClick={() => handleCancelBet(bet.game_id || bet.id)}
                          className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded font-rajdhani font-bold transition-colors"
                        >
                          Cancel
                        </button>
                      )}
                      {bet.status === 'COMPLETED' && (
                        <button
                          onClick={() => handleRepeatBet(bet)}
                          className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded font-rajdhani font-bold transition-colors"
                        >
                          Repeat
                        </button>
                      )}
                      <button
                        onClick={() => showBetDetails(bet)}
                        className="flex-1 px-3 py-2 bg-surface-sidebar border border-accent-primary border-opacity-30 hover:border-opacity-50 text-white text-sm rounded font-rajdhani font-bold transition-colors"
                      >
                        Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-6 flex justify-between items-center">
                  <div className="text-text-secondary text-sm font-roboto">
                    Showing {Math.min((currentPage - 1) * ITEMS_PER_PAGE + 1, totalBets)}-{Math.min(currentPage * ITEMS_PER_PAGE, totalBets)} of {totalBets}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white disabled:opacity-50 disabled:cursor-not-allowed font-rajdhani font-bold"
                    >
                      Previous
                    </button>
                    <span className="px-3 py-1 text-white font-rajdhani font-bold">
                      {currentPage} / {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white disabled:opacity-50 disabled:cursor-not-allowed font-rajdhani font-bold"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </SectionBlock>
      </div>

      {/* Details Modal */}
      {showDetailsModal && selectedBet && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg max-w-md w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-russo text-white">Детали ставки</h3>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-text-secondary hover:text-white transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                  <label className="block text-text-secondary text-sm mb-1">ID игры</label>
                  <div className="text-white font-rajdhani font-bold">{selectedBet.game_id || selectedBet.id}</div>
                </div>

                <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                  <label className="block text-text-secondary text-sm mb-1">Противник</label>
                  <div className="text-white font-rajdhani font-bold">
                    {selectedBet.opponent ? selectedBet.opponent.username : (selectedBet.opponent_username || 'Ожидание')}
                  </div>
                </div>

                <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                  <label className="block text-text-secondary text-sm mb-1">Сумма ставки</label>
                  <div className="text-accent-primary font-rajdhani font-bold text-lg">${selectedBet.bet_amount.toFixed(2)}</div>
                </div>

                <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                  <label className="block text-text-secondary text-sm mb-1">Выбранные гемы</label>
                  <div className="mt-2">
                    {renderGems(selectedBet.bet_gems)}
                  </div>
                </div>

                <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                  <label className="block text-text-secondary text-sm mb-1">Статус</label>
                  <div className="mt-2">
                    {getStatusBadge(selectedBet.status, selectedBet.result)}
                  </div>
                </div>

                {selectedBet.status === 'COMPLETED' && selectedBet.my_move && (
                  <>
                    <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                      <label className="block text-text-secondary text-sm mb-1">Ваш ход</label>
                      <div className="text-white font-rajdhani font-bold">{selectedBet.my_move}</div>
                    </div>
                    <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                      <label className="block text-text-secondary text-sm mb-1">Ход противника</label>
                      <div className="text-white font-rajdhani font-bold">{selectedBet.opponent_move || 'Неизвестно'}</div>
                    </div>
                  </>
                )}

                {selectedBet.status === 'COMPLETED' && selectedBet.commission !== undefined && (
                  <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                    <label className="block text-text-secondary text-sm mb-1">Комиссия</label>
                    <div className="text-text-secondary font-rajdhani font-bold">${(selectedBet.commission || selectedBet.bet_amount * 0.03).toFixed(2)}</div>
                  </div>
                )}

                <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                  <label className="block text-text-secondary text-sm mb-1">Создана</label>
                  <div className="text-white text-sm font-roboto">
                    {new Date(selectedBet.created_at).toLocaleString('ru-RU')}
                  </div>
                </div>

                {selectedBet.completed_at && (
                  <div className="bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-3">
                    <label className="block text-text-secondary text-sm mb-1">Завершена</label>
                    <div className="text-white text-sm font-roboto">
                      {new Date(selectedBet.completed_at).toLocaleString('ru-RU')}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="px-4 py-2 bg-surface-sidebar border border-accent-primary border-opacity-30 hover:border-opacity-50 rounded text-white font-rajdhani font-bold transition-colors"
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