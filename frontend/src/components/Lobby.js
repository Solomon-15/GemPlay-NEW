import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Lobby = ({ user, onUpdateUser }) => {
  const [stats, setStats] = useState({ available: 0, gems: 0, total: 0 });
  const [myBets, setMyBets] = useState([]);
  const [availableBets, setAvailableBets] = useState([]);
  const [ongoingBattles, setOngoingBattles] = useState([]);
  const [availableBots, setAvailableBots] = useState([]);
  const [ongoingBotBattles, setOngoingBotBattles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('live-players');
  const [currentPage, setCurrentPage] = useState({
    myBets: 1,
    availableBets: 1,
    ongoingBattles: 1,
    availableBots: 1,
    ongoingBotBattles: 1
  });

  const itemsPerPage = 10;

  useEffect(() => {
    fetchLobbyData();
    // Обновляем данные каждые 10 секунд
    const interval = setInterval(fetchLobbyData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchLobbyData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch user stats
      const balanceResponse = await axios.get(`${API}/economy/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Fetch games data
      const gamesResponse = await axios.get(`${API}/games/available`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const myBetsResponse = await axios.get(`${API}/games/my-bets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setStats({
        available: balanceResponse.data.virtual_balance || 0,
        gems: balanceResponse.data.total_gem_value || 0,
        total: balanceResponse.data.total_value || 0
      });
      
      // Filter games
      const allGames = gamesResponse.data || [];
      setAvailableBets(allGames.filter(game => !game.is_bot_game));
      setAvailableBots(allGames.filter(game => game.is_bot_game));
      
      const userGames = myBetsResponse.data || [];
      setMyBets(userGames.filter(game => game.status === 'WAITING'));
      setOngoingBattles(userGames.filter(game => game.status === 'ACTIVE'));
      setOngoingBotBattles(userGames.filter(game => game.status === 'ACTIVE' && game.is_bot_game));
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching lobby data:', error);
      setLoading(false);
    }
  };

  const InfoBlock = ({ title, value, icon, color }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg mb-2 ${color}`}>
        {icon}
      </div>
      <h3 className="font-rajdhani font-bold text-lg text-white">{title}</h3>
      <p className="font-roboto text-2xl font-bold text-accent-primary">
        {typeof value === 'number' ? `$${value.toFixed(2)}` : value}
      </p>
    </div>
  );

  const GameCard = ({ game, onJoin, isBot = false }) => (
    <div className="bg-surface-sidebar border border-accent-primary rounded-lg p-4 hover:border-accent-primary hover:shadow-lg hover:shadow-accent-primary/20 transition-all duration-300">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isBot ? 'bg-blue-700' : 'bg-green-700'}`}>
            {isBot ? '🤖' : '👤'}
          </div>
          <div>
            <h4 className="font-rajdhani font-bold text-white">{game.creator_username || 'Player'}</h4>
            <p className="font-roboto text-xs text-text-secondary">
              {new Date(game.created_at).toLocaleTimeString()}
            </p>
          </div>
        </div>
        <span className="px-2 py-1 bg-green-700 text-white text-xs rounded-full font-rajdhani">
          WAITING
        </span>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="flex justify-between">
          <span className="font-roboto text-text-secondary">Bet Amount:</span>
          <span className="font-rajdhani text-green-400 font-bold">${game.bet_amount}</span>
        </div>
        <div className="flex justify-between">
          <span className="font-roboto text-text-secondary">Gems:</span>
          <span className="font-rajdhani text-white text-sm">
            {Object.entries(game.bet_gems || {}).map(([type, qty]) => `${type}: ${qty}`).join(', ')}
          </span>
        </div>
      </div>
      
      <button
        onClick={() => onJoin(game.id)}
        className="w-full py-2 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300"
      >
        JOIN BATTLE
      </button>
    </div>
  );

  const SectionBlock = ({ title, icon, count, children, color = 'text-blue-400' }) => (
    <div className="bg-surface-card border border-accent-primary rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className={color}>{icon}</div>
          <h3 className="font-rajdhani font-bold text-lg text-white">{title}</h3>
        </div>
        <span className="px-2 py-1 bg-accent-dark text-white text-xs rounded-full font-rajdhani">
          {count}
        </span>
      </div>
      {children}
    </div>
  );

  const PaginationControls = ({ currentPage, totalItems, onPageChange, section }) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    if (totalPages <= 1) return null;

    return (
      <div className="flex justify-center items-center space-x-2 mt-4">
        <button
          onClick={() => onPageChange(section, Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="px-3 py-1 bg-surface-sidebar border border-accent-primary rounded-lg text-text-secondary hover:text-white disabled:opacity-50"
        >
          Previous
        </button>
        <span className="font-roboto text-text-secondary">
          {currentPage} of {totalPages}
        </span>
        <button
          onClick={() => onPageChange(section, Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          className="px-3 py-1 bg-surface-sidebar border border-accent-primary rounded-lg text-text-secondary hover:text-white disabled:opacity-50"
        >
          Next
        </button>
      </div>
    );
  };

  const handlePageChange = (section, newPage) => {
    setCurrentPage(prev => ({ ...prev, [section]: newPage }));
  };

  const handleJoinGame = async (gameId) => {
    // This would redirect to the create game component with join functionality
    console.log('Joining game:', gameId);
  };

  const getPaginatedItems = (items, page) => {
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return items.slice(startIndex, endIndex);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Loading Lobby...</div>
      </div>
    );
  }

  const LivePlayersContent = () => (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
      {/* Left Column - My Bets & Ongoing Battles */}
      <div className="space-y-6">
        {/* My Bets */}
        <SectionBlock
          title="My Bets"
          count={myBets.length}
          color="text-green-400"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          }
        >
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {getPaginatedItems(myBets, currentPage.myBets).map((game) => (
              <GameCard key={game.id} game={game} onJoin={handleJoinGame} />
            ))}
            {myBets.length === 0 && (
              <p className="text-text-secondary text-center py-8">No active bets</p>
            )}
          </div>
          <PaginationControls
            currentPage={currentPage.myBets}
            totalItems={myBets.length}
            onPageChange={handlePageChange}
            section="myBets"
          />
        </SectionBlock>

        {/* Ongoing Battles */}
        <SectionBlock
          title="Ongoing Battles"
          count={ongoingBattles.length}
          color="text-orange-400"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          }
        >
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {getPaginatedItems(ongoingBattles, currentPage.ongoingBattles).map((game) => (
              <GameCard key={game.id} game={game} onJoin={handleJoinGame} />
            ))}
            {ongoingBattles.length === 0 && (
              <p className="text-text-secondary text-center py-8">No ongoing battles</p>
            )}
          </div>
          <PaginationControls
            currentPage={currentPage.ongoingBattles}
            totalItems={ongoingBattles.length}
            onPageChange={handlePageChange}
            section="ongoingBattles"
          />
        </SectionBlock>
      </div>

      {/* Right Column - Available Bets */}
      <div className="lg:col-span-2">
        <SectionBlock
          title="Available Bets"
          count={availableBets.length}
          color="text-blue-400"
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
            {getPaginatedItems(availableBets, currentPage.availableBets).map((game) => (
              <GameCard key={game.id} game={game} onJoin={handleJoinGame} />
            ))}
            {availableBets.length === 0 && (
              <div className="col-span-full text-text-secondary text-center py-8">
                No available bets
              </div>
            )}
          </div>
          <PaginationControls
            currentPage={currentPage.availableBets}
            totalItems={availableBets.length}
            onPageChange={handlePageChange}
            section="availableBets"
          />
        </SectionBlock>
      </div>
    </div>
  );

  const BotPlayersContent = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-6xl mx-auto">
      {/* Available Bots */}
      <SectionBlock
        title="Available Bots"
        count={availableBots.length}
        color="text-cyan-400"
        icon={
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        }
      >
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {getPaginatedItems(availableBots, currentPage.availableBots).map((game) => (
            <GameCard key={game.id} game={game} onJoin={handleJoinGame} isBot={true} />
          ))}
          {availableBots.length === 0 && (
            <p className="text-text-secondary text-center py-8">No available bots</p>
          )}
        </div>
        <PaginationControls
          currentPage={currentPage.availableBots}
          totalItems={availableBots.length}
          onPageChange={handlePageChange}
          section="availableBots"
        />
      </SectionBlock>

      {/* Ongoing Bot Battles */}
      <SectionBlock
        title="Ongoing Bot Battles"
        count={ongoingBotBattles.length}
        color="text-red-400"
        icon={
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        }
      >
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {getPaginatedItems(ongoingBotBattles, currentPage.ongoingBotBattles).map((game) => (
            <GameCard key={game.id} game={game} onJoin={handleJoinGame} isBot={true} />
          ))}
          {ongoingBotBattles.length === 0 && (
            <p className="text-text-secondary text-center py-8">No ongoing bot battles</p>
          )}
        </div>
        <PaginationControls
          currentPage={currentPage.ongoingBotBattles}
          totalItems={ongoingBotBattles.length}
          onPageChange={handlePageChange}
          section="ongoingBotBattles"
        />
      </SectionBlock>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-primary p-4 sm:p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-3xl sm:text-4xl md:text-6xl text-accent-primary mb-4">
          Game Lobby
        </h1>
        <p className="font-roboto text-lg sm:text-xl text-text-secondary">
          Join battles, create bets, and dominate the arena
        </p>
      </div>

      {/* Info Blocks */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 max-w-4xl mx-auto">
        <InfoBlock
          title="Available"
          value={stats.available}
          color="bg-green-600/20"
          icon={
            <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          }
        />
        <InfoBlock
          title="Gems"
          value={stats.gems}
          color="bg-purple-600/20"
          icon={
            <svg className="w-6 h-6 text-purple-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6,2L2,8L12,22L22,8L18,2H6M6.5,3H17.5L20.5,8L12,19L3.5,8L6.5,3Z" />
            </svg>
          }
        />
        <InfoBlock
          title="Total"
          value={stats.total}
          color="bg-accent-primary/20"
          icon={
            <svg className="w-6 h-6 text-accent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
        />
      </div>

      {/* Create Bet Button */}
      <div className="text-center mb-8">
        <button 
          onClick={() => window.location.href = '#create-game'}
          className="px-8 py-4 bg-gradient-to-r from-green-700 to-green-800 text-white font-rajdhani font-bold text-xl rounded-lg hover:scale-105 transition-all duration-300 animate-pulse hover:animate-none shadow-lg hover:shadow-green-500/25"
        >
          <svg className="w-6 h-6 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          CREATE BET
        </button>
      </div>

      {/* Tabs */}
      <div className="max-w-6xl mx-auto mb-8">
        <div className="flex space-x-1 bg-surface-sidebar rounded-lg p-1">
          {[
            { id: 'live-players', label: 'Live Players', icon: '👥', count: availableBets.length + myBets.length + ongoingBattles.length },
            { id: 'bot-players', label: 'Bot Players', icon: '🤖', count: availableBots.length + ongoingBotBattles.length }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 px-4 rounded-lg font-rajdhani font-bold transition-all duration-300 ${
                activeTab === tab.id
                  ? 'bg-accent-primary text-white shadow-lg'
                  : 'text-text-secondary hover:text-white hover:bg-surface-card'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
              <span className="ml-2 px-2 py-1 bg-white/20 rounded-full text-xs">
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div>
        {activeTab === 'live-players' && <LivePlayersContent />}
        {activeTab === 'bot-players' && <BotPlayersContent />}
      </div>
    </div>
  );
};

export default Lobby;