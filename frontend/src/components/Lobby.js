import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GemsHeader from './GemsHeader';
import PlayerCard from './PlayerCard';
import CreateBetModal from './CreateBetModal';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Lobby = ({ user, onUpdateUser, setCurrentView }) => {
  const { showSuccess, showError } = useNotifications();
  const [stats, setStats] = useState({ available: 0, gems: 0, total: 0 });
  const [myBets, setMyBets] = useState([]);
  const [availableBets, setAvailableBets] = useState([]);
  const [ongoingBattles, setOngoingBattles] = useState([]);
  const [availableBots, setAvailableBots] = useState([]);
  const [ongoingBotBattles, setOngoingBotBattles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('live-players');
  const [showCreateBetModal, setShowCreateBetModal] = useState(false);
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
      
      // Fetch active bots
      const botsResponse = await axios.get(`${API}/bots/active`, {
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
      
      // Combine bot games and active bots
      const botGames = allGames.filter(game => game.is_bot_game);
      const activeBots = botsResponse.data || [];
      const botEntries = activeBots.map(bot => ({
        id: `bot-${bot.id}`,
        creator_username: bot.name,
        creator: { username: bot.name, gender: bot.avatar_gender },
        bet_amount: `${bot.min_bet} - ${bot.max_bet}`,
        bet_gems: { Ruby: '1-5', Emerald: '1-5', Sapphire: '1-5' },
        created_at: new Date(),
        is_bot: true,
        bot_id: bot.id,
        bot_type: bot.bot_type
      }));
      
      setAvailableBots([...botGames, ...botEntries]);
      
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

  const GameCard = ({ game, onJoin, isBot = false }) => {
    const isActiveBotEntry = game.is_bot && game.bot_id;
    
    return (
      <div className="bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg p-4 hover:border-accent-primary hover:border-opacity-100 hover:shadow-lg hover:shadow-accent-primary/20 transition-all duration-300">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isBot || isActiveBotEntry ? 'bg-blue-700' : 'bg-green-700'}`}>
              {isBot || isActiveBotEntry ? '🤖' : '👤'}
            </div>
            <div>
              <h4 className="font-rajdhani font-bold text-white">
                {game.creator_username || game.creator?.username || 'Player'}
              </h4>
              <p className="font-roboto text-xs text-text-secondary">
                {isActiveBotEntry ? 'Available Bot' : new Date(game.created_at).toLocaleTimeString()}
              </p>
              {isActiveBotEntry && (
                <span className="text-xs text-cyan-400 font-rajdhani">
                  {game.bot_type === 'HUMAN' ? 'Human-like' : 'Regular'} Bot
                </span>
              )}
            </div>
          </div>
          <span className={`px-2 py-1 text-white text-xs rounded-full font-rajdhani ${
            isActiveBotEntry ? 'bg-blue-700' : 'bg-green-700'
          }`}>
            {isActiveBotEntry ? 'CHALLENGE' : 'WAITING'}
          </span>
        </div>
        
        <div className="space-y-2 mb-4">
          <div className="flex justify-between">
            <span className="font-roboto text-text-secondary">
              {isActiveBotEntry ? 'Bet Range:' : 'Bet Amount:'}
            </span>
            <span className="font-rajdhani text-green-400 font-bold">
              {typeof game.bet_amount === 'string' ? game.bet_amount : `$${game.bet_amount}`}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="font-roboto text-text-secondary">Gems:</span>
            <span className="font-rajdhani text-white text-sm">
              {typeof game.bet_gems === 'object' ? 
                Object.entries(game.bet_gems).map(([type, qty]) => `${type}: ${qty}`).join(', ') : 
                'Various'
              }
            </span>
          </div>
        </div>
        
        <button
          onClick={() => onJoin(isActiveBotEntry ? game.bot_id : game.id)}
          className="w-full py-2 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300"
        >
          {isActiveBotEntry ? 'CHALLENGE BOT' : 'JOIN BATTLE'}
        </button>
      </div>
    );
  };

  const SectionBlock = ({ title, icon, count, children, color = 'text-blue-400' }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
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
          className="px-3 py-1 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white disabled:opacity-50"
        >
          Previous
        </button>
        <span className="font-roboto text-text-secondary">
          {currentPage} of {totalPages}
        </span>
        <button
          onClick={() => onPageChange(section, Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          className="px-3 py-1 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white disabled:opacity-50"
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
    try {
      console.log('Attempting to join game:', gameId);
      
      // Check if it's a bot challenge (bot ID format)
      if (typeof gameId === 'string' && gameId.startsWith('bot-')) {
        // Bot challenge
        const botId = gameId.replace('bot-', '');
        console.log('Challenging bot:', botId);
        showSuccess('Bot challenge initiated');
        // This would open a modal or redirect to challenge the bot
        // For now, we'll just log it
      } else {
        // Regular game join
        const token = localStorage.getItem('token');
        const response = await axios.post(`${API}/games/${gameId}/join`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data.success) {
          showSuccess('Successfully joined the game');
          // Refresh the lobby data after joining
          await fetchLobbyData();
          if (onUpdateUser) {
            onUpdateUser();
          }
        } else {
          showError('Failed to join game');
        }
      }
    } catch (error) {
      console.error('Error handling game join:', error);
      showError(error.response?.data?.detail || 'Failed to join game');
    }
  };

  const handleCancelBet = async (gameId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/games/${gameId}/cancel`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        showSuccess('Bet cancelled successfully');
        // Refresh the lobby data after cancellation
        await fetchLobbyData();
        if (onUpdateUser) {
          onUpdateUser();
        }
      } else {
        showError('Failed to cancel bet');
      }
    } catch (error) {
      console.error('Error cancelling bet:', error);
      showError(error.response?.data?.detail || 'Failed to cancel bet');
      // Even if the API call fails, we can still refresh the data
      await fetchLobbyData();
    }
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
    <div className="space-y-6 max-w-7xl mx-auto">
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {getPaginatedItems(myBets, currentPage.myBets).map((game) => (
            <PlayerCard 
              key={game.id} 
              game={game} 
              isMyBet={true}
              onCancel={handleCancelBet}
              currentTime={new Date()}
            />
          ))}
          {myBets.length === 0 && (
            <div className="col-span-full text-text-secondary text-center py-8">
              You have no active bets
            </div>
          )}
        </div>
        <PaginationControls
          currentPage={currentPage.myBets}
          totalItems={myBets.length}
          onPageChange={handlePageChange}
          section="myBets"
        />
      </SectionBlock>

      {/* Available Bets */}
      <SectionBlock
        title="Available Bets"
        count={availableBets.length}
        color="text-blue-400"
        icon={
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        }
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {getPaginatedItems(availableBets, currentPage.availableBets).map((game) => (
            <PlayerCard 
              key={game.id} 
              game={game} 
              onAccept={handleJoinGame}
              currentTime={new Date()}
            />
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {getPaginatedItems(ongoingBattles, currentPage.ongoingBattles).map((game) => (
            <PlayerCard 
              key={game.id} 
              game={game} 
              isOngoing={true}
              currentTime={new Date()}
            />
          ))}
          {ongoingBattles.length === 0 && (
            <div className="col-span-full text-text-secondary text-center py-8">
              No active battles
            </div>
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

      {/* Gems Header */}
      <GemsHeader user={user} />

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
          onClick={() => setShowCreateBetModal(true)}
          className="px-8 py-4 bg-gradient-to-r from-green-500 to-green-600 text-white font-rajdhani font-bold text-xl rounded-lg hover:scale-110 transition-all duration-300 shadow-lg hover:shadow-green-500/50 animate-bounce hover:animate-none focus:animate-none active:animate-none"
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

      {/* Create Bet Modal */}
      {showCreateBetModal && (
        <CreateBetModal
          user={user}
          onClose={() => setShowCreateBetModal(false)}
          onUpdateUser={onUpdateUser}
        />
      )}
    </div>
  );
};

export default Lobby;