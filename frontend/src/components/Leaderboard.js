import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Leaderboard = ({ user }) => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('winnings');
  const [currentPage, setCurrentPage] = useState(1);
  const [userRank, setUserRank] = useState(null);
  
  const itemsPerPage = 10;

  useEffect(() => {
    fetchLeaderboard();
  }, [activeTab]);

  const fetchLeaderboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/leaderboard/${activeTab}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLeaderboard(response.data.leaderboard || []);
      setUserRank(response.data.user_rank || null);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
      // Show empty state instead of mock data
      setLeaderboard([]);
      setUserRank(null);
      setLoading(false);
    }
  };

  const generateMockLeaderboard = () => {
    const mockUsers = [
      'GemMaster2024', 'DiamondKing', 'CrystalQueen', 'RubyHunter', 'EmeraldWin',
      'SapphireStorm', 'TopazTitan', 'GemCollector', 'JewelJuggernaut', 'PreciousPlayer',
      'StoneSeeker', 'GemGuru', 'CrystalCrusher', 'DiamondDealer', 'RockRoyal',
      'GemGenius', 'JewelJedi', 'CrystalChamp', 'DiamondDynamo', 'EmeraldExpert'
    ];

    return mockUsers.map((username, index) => ({
      rank: index + 1,
      user_id: `user_${index + 1}`,
      username: username,
      total_winnings: Math.floor(Math.random() * 50000) + 5000,
      games_won: Math.floor(Math.random() * 200) + 10,
      games_played: Math.floor(Math.random() * 300) + 50,
      win_rate: Math.floor(Math.random() * 40) + 40, // 40-80% win rate
      avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`,
      level: Math.floor(Math.random() * 20) + 1,
      favorite_gem: ['Ruby', 'Emerald', 'Sapphire', 'Diamond', 'Topaz'][Math.floor(Math.random() * 5)]
    }));
  };

  const getPaginatedData = () => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return leaderboard.slice(startIndex, endIndex);
  };

  const getStatValue = (player, stat) => {
    switch (stat) {
      case 'winnings':
        return `$${player.total_winnings?.toLocaleString() || '0'}`;
      case 'wins':
        return player.games_won || 0;
      case 'winrate':
        return `${player.win_rate || 0}%`;
      case 'games':
        return player.games_played || 0;
      default:
        return player.total_winnings || 0;
    }
  };

  const getStatLabel = (stat) => {
    switch (stat) {
      case 'winnings': return 'Total Winnings';
      case 'wins': return 'Games Won';
      case 'winrate': return 'Win Rate';
      case 'games': return 'Games Played';
      default: return 'Total Winnings';
    }
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return '👑';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return '🏆';
  };

  const getRankColor = (rank) => {
    if (rank === 1) return 'text-yellow-400';
    if (rank === 2) return 'text-gray-300';
    if (rank === 3) return 'text-amber-600';
    return 'text-blue-400';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Loading Leaderboard...</div>
      </div>
    );
  }

  const totalPages = Math.ceil(leaderboard.length / itemsPerPage);
  const paginatedData = getPaginatedData();

  return (
    <div className="min-h-screen bg-gradient-primary p-4 sm:p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-3xl sm:text-4xl md:text-6xl text-accent-primary mb-4">
          Leaderboard
        </h1>
        <p className="font-roboto text-lg sm:text-xl text-text-secondary">
          Compete with the best players and climb the rankings
        </p>
      </div>

      {/* User Rank Card */}
      {userRank && (
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-accent rounded-full flex items-center justify-center">
                  <span className="font-russo text-white">
                    {user.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <h3 className="font-rajdhani font-bold text-white text-lg">{user.username}</h3>
                  <p className="font-roboto text-text-secondary">Your Position</p>
                </div>
              </div>
              <div className="text-center">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{getRankIcon(userRank)}</span>
                  <span className={`font-russo text-3xl font-bold ${getRankColor(userRank)}`}>
                    #{userRank}
                  </span>
                </div>
                <p className="font-roboto text-text-secondary text-sm">Current Rank</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="max-w-6xl mx-auto mb-8">
        <div className="flex space-x-1 bg-surface-sidebar rounded-lg p-1">
          {[
            { id: 'winnings', label: 'Total Winnings', icon: '💰' },
            { id: 'wins', label: 'Most Wins', icon: '🏆' },
            { id: 'winrate', label: 'Win Rate', icon: '📊' },
            { id: 'games', label: 'Most Active', icon: '🎮' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setCurrentPage(1);
              }}
              className={`flex-1 py-3 px-4 rounded-lg font-rajdhani font-bold transition-all duration-300 ${
                activeTab === tab.id
                  ? 'bg-accent-primary text-white shadow-lg'
                  : 'text-text-secondary hover:text-white hover:bg-surface-card'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="max-w-6xl mx-auto">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
          {/* Table Header */}
          <div className="bg-surface-sidebar border-b border-accent-primary border-opacity-30 p-4">
            <div className="grid grid-cols-12 gap-4 items-center">
              <div className="col-span-1 font-rajdhani font-bold text-text-secondary">Rank</div>
              <div className="col-span-4 font-rajdhani font-bold text-text-secondary">Player</div>
              <div className="col-span-2 font-rajdhani font-bold text-text-secondary">{getStatLabel(activeTab)}</div>
              <div className="col-span-2 font-rajdhani font-bold text-text-secondary">Games</div>
              <div className="col-span-2 font-rajdhani font-bold text-text-secondary">Win Rate</div>
              <div className="col-span-1 font-rajdhani font-bold text-text-secondary">Level</div>
            </div>
          </div>

          {/* Table Body */}
          <div className="divide-y divide-accent-primary divide-opacity-20">
            {paginatedData.map((player, index) => (
              <div
                key={player.user_id}
                className={`p-4 hover:bg-surface-sidebar transition-colors ${
                  player.user_id === user.id ? 'bg-accent-primary/10' : ''
                }`}
              >
                <div className="grid grid-cols-12 gap-4 items-center">
                  {/* Rank */}
                  <div className="col-span-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getRankIcon(player.rank)}</span>
                      <span className={`font-russo font-bold ${getRankColor(player.rank)}`}>
                        {player.rank}
                      </span>
                    </div>
                  </div>

                  {/* Player */}
                  <div className="col-span-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-accent rounded-full flex items-center justify-center">
                        <span className="font-russo text-white text-sm">
                          {player.username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <h4 className="font-rajdhani font-bold text-white">{player.username}</h4>
                        <p className="font-roboto text-text-secondary text-xs">
                          Favorite: {player.favorite_gem}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Stat Value */}
                  <div className="col-span-2">
                    <span className="font-rajdhani font-bold text-accent-primary text-lg">
                      {getStatValue(player, activeTab)}
                    </span>
                  </div>

                  {/* Games */}
                  <div className="col-span-2">
                    <span className="font-rajdhani text-white">
                      {player.games_played || 0}
                    </span>
                  </div>

                  {/* Win Rate */}
                  <div className="col-span-2">
                    <div className="flex items-center space-x-2">
                      <div className="flex-1 bg-surface-sidebar rounded-full h-2">
                        <div
                          className="bg-green-400 h-2 rounded-full"
                          style={{ width: `${player.win_rate || 0}%` }}
                        ></div>
                      </div>
                      <span className="font-rajdhani text-white text-sm">
                        {player.win_rate || 0}%
                      </span>
                    </div>
                  </div>

                  {/* Level */}
                  <div className="col-span-1">
                    <span className="font-rajdhani font-bold text-purple-400">
                      {player.level || 1}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

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
              {[...Array(totalPages)].map((_, index) => (
                <button
                  key={index + 1}
                  onClick={() => setCurrentPage(index + 1)}
                  className={`px-3 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
                    currentPage === index + 1
                      ? 'bg-accent-primary text-white'
                      : 'bg-surface-card border border-accent-primary border-opacity-30 text-text-secondary hover:text-white'
                  }`}
                >
                  {index + 1}
                </button>
              ))}
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

export default Leaderboard;