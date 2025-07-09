import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const History = ({ user }) => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [dateFilter, setDateFilter] = useState('all');
  const [stats, setStats] = useState({
    total_games: 0,
    total_won: 0,
    total_lost: 0,
    total_draw: 0,
    total_winnings: 0,
    total_losses: 0
  });
  
  const itemsPerPage = 10;

  useEffect(() => {
    fetchGameHistory();
  }, [activeTab, dateFilter]);

  const fetchGameHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/games/history`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          status: activeTab !== 'all' ? activeTab : undefined,
          date_filter: dateFilter !== 'all' ? dateFilter : undefined
        }
      });
      setGames(response.data.games || []);
      setStats(response.data.stats || stats);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching game history:', error);
      // Mock data for demonstration
      setGames(generateMockHistory());
      setStats(generateMockStats());
      setLoading(false);
    }
  };

  const generateMockHistory = () => {
    const mockGames = [];
    const opponents = [
      'GemMaster2024', 'DiamondKing', 'CrystalQueen', 'RubyHunter', 'EmeraldWin',
      'SapphireBot', 'TopazTitan', 'GemCollector', 'JewelBot', 'PreciousPlayer'
    ];
    const moves = ['rock', 'paper', 'scissors'];
    const outcomes = ['won', 'lost', 'draw'];
    const gemTypes = ['Ruby', 'Emerald', 'Sapphire', 'Diamond', 'Topaz', 'Amber', 'Magic'];

    for (let i = 0; i < 50; i++) {
      const outcome = outcomes[Math.floor(Math.random() * outcomes.length)];
      const betAmount = Math.floor(Math.random() * 1000) + 100;
      const isBot = Math.random() < 0.3;
      
      mockGames.push({
        id: `game_${i + 1}`,
        opponent_username: opponents[Math.floor(Math.random() * opponents.length)],
        opponent_id: `opponent_${i + 1}`,
        is_bot_game: isBot,
        my_move: moves[Math.floor(Math.random() * moves.length)],
        opponent_move: moves[Math.floor(Math.random() * moves.length)],
        bet_amount: betAmount,
        bet_gems: {
          [gemTypes[Math.floor(Math.random() * gemTypes.length)]]: Math.floor(Math.random() * 5) + 1
        },
        status: 'COMPLETED',
        result: outcome,
        winnings: outcome === 'won' ? betAmount * 1.94 : 0, // 3% commission
        created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
        completed_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
        game_duration: Math.floor(Math.random() * 300) + 30 // 30 seconds to 5 minutes
      });
    }

    return mockGames.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  };

  const generateMockStats = () => {
    const totalGames = 50;
    const totalWon = Math.floor(totalGames * 0.55); // 55% win rate
    const totalLost = Math.floor(totalGames * 0.4); // 40% loss rate
    const totalDraw = totalGames - totalWon - totalLost; // 5% draw rate

    return {
      total_games: totalGames,
      total_won: totalWon,
      total_lost: totalLost,
      total_draw: totalDraw,
      total_winnings: Math.floor(Math.random() * 50000) + 10000,
      total_losses: Math.floor(Math.random() * 30000) + 5000
    };
  };

  const getFilteredGames = () => {
    let filtered = games;

    if (activeTab !== 'all') {
      filtered = filtered.filter(game => game.result === activeTab);
    }

    return filtered;
  };

  const getPaginatedGames = () => {
    const filtered = getFilteredGames();
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filtered.slice(startIndex, endIndex);
  };

  const getMoveIcon = (move) => {
    switch (move) {
      case 'rock': return '🪨';
      case 'paper': return '📄';
      case 'scissors': return '✂️';
      default: return '❓';
    }
  };

  const getResultColor = (result) => {
    switch (result) {
      case 'won': return 'text-green-400';
      case 'lost': return 'text-red-400';
      case 'draw': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getResultLabel = (result) => {
    switch (result) {
      case 'won': return 'WON';
      case 'lost': return 'LOST';
      case 'draw': return 'DRAW';
      default: return 'UNKNOWN';
    }
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatGems = (betGems) => {
    if (!betGems || typeof betGems !== 'object') return 'No gems';
    return Object.entries(betGems)
      .map(([type, quantity]) => `${type}: ${quantity}`)
      .join(', ');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Loading History...</div>
      </div>
    );
  }

  const filteredGames = getFilteredGames();
  const paginatedGames = getPaginatedGames();
  const totalPages = Math.ceil(filteredGames.length / itemsPerPage);

  return (
    <div className="min-h-screen bg-gradient-primary p-4 sm:p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-3xl sm:text-4xl md:text-6xl text-accent-primary mb-4">
          Game History
        </h1>
        <p className="font-roboto text-lg sm:text-xl text-text-secondary">
          Review your past battles and track your progress
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8 max-w-6xl mx-auto">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <h3 className="font-rajdhani font-bold text-lg text-white">Total Games</h3>
          <p className="font-roboto text-2xl font-bold text-accent-primary">{stats.total_games}</p>
        </div>
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <h3 className="font-rajdhani font-bold text-lg text-white">Won</h3>
          <p className="font-roboto text-2xl font-bold text-green-400">{stats.total_won}</p>
        </div>
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <h3 className="font-rajdhani font-bold text-lg text-white">Lost</h3>
          <p className="font-roboto text-2xl font-bold text-red-400">{stats.total_lost}</p>
        </div>
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <h3 className="font-rajdhani font-bold text-lg text-white">Draw</h3>
          <p className="font-roboto text-2xl font-bold text-yellow-400">{stats.total_draw}</p>
        </div>
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <h3 className="font-rajdhani font-bold text-lg text-white">Win Rate</h3>
          <p className="font-roboto text-2xl font-bold text-purple-400">
            {stats.total_games > 0 ? Math.round((stats.total_won / stats.total_games) * 100) : 0}%
          </p>
        </div>
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <h3 className="font-rajdhani font-bold text-lg text-white">Net Profit</h3>
          <p className={`font-roboto text-2xl font-bold ${
            (stats.total_winnings - stats.total_losses) >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            ${(stats.total_winnings - stats.total_losses).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-6xl mx-auto mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Result Filter */}
          <div className="flex space-x-1 bg-surface-sidebar rounded-lg p-1">
            {[
              { id: 'all', label: 'All Games', icon: '🎮' },
              { id: 'won', label: 'Won', icon: '🏆' },
              { id: 'lost', label: 'Lost', icon: '💔' },
              { id: 'draw', label: 'Draw', icon: '🤝' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setCurrentPage(1);
                }}
                className={`flex-1 py-2 px-3 rounded-lg font-rajdhani font-bold transition-all duration-300 text-sm ${
                  activeTab === tab.id
                    ? 'bg-accent-primary text-white shadow-lg'
                    : 'text-text-secondary hover:text-white hover:bg-surface-card'
                }`}
              >
                <span className="mr-1">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>

          {/* Date Filter */}
          <div className="flex space-x-1 bg-surface-sidebar rounded-lg p-1">
            {[
              { id: 'all', label: 'All Time' },
              { id: 'today', label: 'Today' },
              { id: 'week', label: 'This Week' },
              { id: 'month', label: 'This Month' }
            ].map((filter) => (
              <button
                key={filter.id}
                onClick={() => {
                  setDateFilter(filter.id);
                  setCurrentPage(1);
                }}
                className={`flex-1 py-2 px-3 rounded-lg font-rajdhani font-bold transition-all duration-300 text-sm ${
                  dateFilter === filter.id
                    ? 'bg-accent-primary text-white shadow-lg'
                    : 'text-text-secondary hover:text-white hover:bg-surface-card'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Games List */}
      <div className="max-w-6xl mx-auto">
        {paginatedGames.length > 0 ? (
          <div className="space-y-4">
            {paginatedGames.map((game) => (
              <div
                key={game.id}
                className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 hover:border-accent-primary hover:border-opacity-100 transition-all duration-300"
              >
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
                  {/* Game Result */}
                  <div className="lg:col-span-2">
                    <div className="flex items-center space-x-2">
                      <span className={`font-russo font-bold text-lg ${getResultColor(game.result)}`}>
                        {getResultLabel(game.result)}
                      </span>
                      <span className="text-sm text-text-secondary">
                        {game.is_bot_game ? '🤖' : '👤'}
                      </span>
                    </div>
                    <p className="font-roboto text-text-secondary text-xs">
                      {new Date(game.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  {/* Opponent */}
                  <div className="lg:col-span-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-accent rounded-full flex items-center justify-center">
                        <span className="font-russo text-white text-sm">
                          {game.opponent_username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <h4 className="font-rajdhani font-bold text-white">{game.opponent_username}</h4>
                        <p className="font-roboto text-text-secondary text-sm">
                          {game.is_bot_game ? 'Bot Player' : 'Human Player'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Moves */}
                  <div className="lg:col-span-2">
                    <div className="flex items-center space-x-4">
                      <div className="text-center">
                        <div className="text-2xl">{getMoveIcon(game.my_move)}</div>
                        <p className="font-roboto text-text-secondary text-xs">You</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl text-text-secondary">VS</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl">{getMoveIcon(game.opponent_move)}</div>
                        <p className="font-roboto text-text-secondary text-xs">Them</p>
                      </div>
                    </div>
                  </div>

                  {/* Bet Info */}
                  <div className="lg:col-span-3">
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="font-roboto text-text-secondary text-sm">Bet:</span>
                        <span className="font-rajdhani text-white font-bold">${game.bet_amount}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="font-roboto text-text-secondary text-sm">Gems:</span>
                        <span className="font-rajdhani text-accent-primary text-xs">
                          {formatGems(game.bet_gems)}
                        </span>
                      </div>
                      {game.result === 'won' && (
                        <div className="flex justify-between">
                          <span className="font-roboto text-text-secondary text-sm">Won:</span>
                          <span className="font-rajdhani text-green-400 font-bold">
                            +${game.winnings?.toLocaleString() || 0}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Duration */}
                  <div className="lg:col-span-2">
                    <div className="text-center">
                      <p className="font-rajdhani text-white font-bold">
                        {formatDuration(game.game_duration)}
                      </p>
                      <p className="font-roboto text-text-secondary text-xs">Duration</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">📜</div>
            <h2 className="font-russo text-2xl text-accent-secondary mb-2">
              No Games Found
            </h2>
            <p className="font-roboto text-text-secondary">
              {activeTab === 'all' 
                ? 'You haven\'t played any games yet. Start your first battle!'
                : `No ${activeTab} games found for the selected filters.`
              }
            </p>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center space-x-2 mt-8">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white disabled:opacity-50 transition-colors"
            >
              Previous
            </button>
            
            <div className="flex space-x-1">
              {[...Array(Math.min(totalPages, 5))].map((_, index) => {
                const pageNum = currentPage <= 3 ? index + 1 : currentPage - 2 + index;
                if (pageNum > totalPages) return null;
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
                      currentPage === pageNum
                        ? 'bg-accent-primary text-white'
                        : 'bg-surface-card border border-accent-primary border-opacity-30 text-text-secondary hover:text-white'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white disabled:opacity-50 transition-colors"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default History;