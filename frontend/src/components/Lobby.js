import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GemsHeader from './GemsHeader';
import PlayerCard from './PlayerCard';
import CreateBetModal from './CreateBetModal';
import JoinBattleModal from './JoinBattleModal';
import { useNotifications } from './NotificationContext';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';
import { useSound, useHoverSound, useModalSound } from '../hooks/useSound';
import { formatDollarsAsGems, getGemPrices, preloadGemPrices } from '../utils/gemUtils';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Lobby = ({ user, onUpdateUser, setCurrentView }) => {
  const { showSuccess, showError } = useNotifications();
  const { game, ui } = useSound();
  const hoverProps = useHoverSound(true);
  const modalSound = useModalSound();
  const [stats, setStats] = useState({ available: 0, gems: 0, total: 0 });
  const [myBets, setMyBets] = useState([]);
  const [availableBets, setAvailableBets] = useState([]);
  const [ongoingBattles, setOngoingBattles] = useState([]);
  const [availableBots, setAvailableBots] = useState([]);
  const [ongoingBotBattles, setOngoingBotBattles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('live-players');
  const [showCreateBetModal, setShowCreateBetModal] = useState(false);
  
  // Состояние для фильтров Available Bets
  const [betFilters, setBetFilters] = useState({
    minAmount: '',
    maxAmount: ''
  });
  
  // Состояние для Join Battle модального окна
  const [selectedBetForJoin, setSelectedBetForJoin] = useState(null);
  const [showJoinBattleModal, setShowJoinBattleModal] = useState(false);
  
  const [currentPage, setCurrentPage] = useState({
    myBets: 1,
    availableBets: 1,
    ongoingBattles: 1,
    availableBots: 1,
    ongoingBotBattles: 1
  });

  // Настройки интерфейса для пагинации
  const [interfaceSettings, setInterfaceSettings] = useState({
    live_players: {
      my_bets: 10,
      available_bets: 10,
      ongoing_battles: 10
    },
    bot_players: {
      available_bots: 10,
      ongoing_bot_battles: 10
    }
  });

  useEffect(() => {
    fetchInterfaceSettings();
    fetchLobbyData();
    
    // Обновляем данные каждые 10 секунд
    const interval = setInterval(fetchLobbyData, 10000);
    
    // Регистрируем колбэк для мгновенного обновления после операций
    const globalRefresh = getGlobalLobbyRefresh();
    const unregister = globalRefresh.registerRefreshCallback(() => {
      console.log('🔄 Lobby auto-refresh triggered by operation');
      fetchLobbyData();
    });
    
    return () => {
      clearInterval(interval);
      unregister();
    };
  }, []);

  const fetchInterfaceSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/interface-settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInterfaceSettings(response.data);
    } catch (error) {
      console.error('Error fetching interface settings:', error);
      // Используем дефолтные значения при ошибке
    }
  };

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
      
      // Fetch active bot games
      const botGamesResponse = await axios.get(`${API}/bots/active-games`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setStats({
        available: balanceResponse.data.virtual_balance || 0,
        gems: balanceResponse.data.total_gem_value || 0,
        total: balanceResponse.data.total_value || 0
      });
      
      // Filter games - separate human bots from regular bots
      const allGames = gamesResponse.data || [];
      
      // Available bets should include:
      // 1. All human player games (is_bot_game is false or undefined)
      // 2. Human-bot games (is_human_bot is true)
      setAvailableBets(allGames.filter(game => {
        // If it's not a bot game at all, include it (human players)
        if (!game.is_bot_game) {
          return true;
        }
        
        // If it's a bot game, only include if it's a human bot
        if (game.is_bot_game && game.is_human_bot) {
          return true;
        }
        
        // Exclude regular bot games
        return false;
      }));
      
      // Set bot games from dedicated endpoint (only regular bots)
      const activeBotGames = botGamesResponse.data || [];
      setAvailableBots(activeBotGames.filter(game => game.is_bot_game && !game.is_human_bot));
      
      const userGames = myBetsResponse.data || [];
      setMyBets(userGames.filter(game => game.status === 'WAITING'));
      
      // Ongoing battles should include ACTIVE and REVEAL statuses
      // These are games where user is actively participating
      setOngoingBattles(userGames.filter(game => 
        game.status === 'ACTIVE' || game.status === 'REVEAL'
      ));
      
      setOngoingBotBattles(userGames.filter(game => 
        (game.status === 'ACTIVE' || game.status === 'REVEAL') && game.is_bot_game
      ));
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching lobby data:', error);
      setLoading(false);
    }
  };

  // Обработчики для Join Battle модального окна
  const handleOpenJoinBattle = (game) => {
    // Определяем, является ли это игрой с ботом
    const isBotGame = availableBots.some(botGame => 
      (botGame.game_id || botGame.id) === (game.game_id || game.id)
    ) || ongoingBotBattles.some(botGame => 
      (botGame.game_id || botGame.id) === (game.game_id || game.id)
    );
    
    // Добавляем флаг игры с ботом
    const gameWithBotFlag = {
      ...game,
      is_bot_game: isBotGame
    };
    
    setSelectedBetForJoin(gameWithBotFlag);
    setShowJoinBattleModal(true);
  };

  const handleCloseJoinBattle = () => {
    modalSound.onClose();
    setSelectedBetForJoin(null);
    setShowJoinBattleModal(false);
  };

  const InfoBlock = ({ title, value, icon, color }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg mb-2 ${color}`}>
        {icon}
      </div>
      <h3 className="font-rajdhani font-bold text-lg text-white">{title}</h3>
      <p className="font-roboto text-2xl font-bold text-accent-primary">
        {typeof value === 'number' ? `$${Math.floor(value)}` : value}
      </p>
    </div>
  );

  const GameCard = ({ game, onJoin, isBot = false }) => {
    const isActiveBotEntry = game.is_bot && game.bot_id;
    
    // For bots, use unified styling similar to PlayerCard
    if (isBot || isActiveBotEntry) {
      // Calculate total gems value (not in dollars, just gem quantity)
      const getTotalGemsValue = () => {
        if (!game.bet_gems || typeof game.bet_gems !== 'object') return 0;
        
        // Define gem prices for calculation
        const gemPrices = {
          'Ruby': 1,
          'Amber': 2, 
          'Topaz': 5,
          'Emerald': 10,
          'Aquamarine': 25,
          'Sapphire': 50,
          'Magic': 100
        };

        return Object.entries(game.bet_gems).reduce((total, [gemType, quantity]) => {
          const price = gemPrices[gemType] || 1;
          return total + (price * quantity);
        }, 0);
      };

      // Get sorted gems by price (ascending)
      const getSortedGems = () => {
        if (!game.bet_gems || typeof game.bet_gems !== 'object') return [];
        
        const gemDefinitions = {
          'Ruby': { price: 1, icon: '/gems/gem-red.svg', color: '#ef4444' },
          'Amber': { price: 2, icon: '/gems/gem-orange.svg', color: '#f97316' },
          'Topaz': { price: 5, icon: '/gems/gem-yellow.svg', color: '#eab308' },
          'Emerald': { price: 10, icon: '/gems/gem-green.svg', color: '#22c55e' },
          'Aquamarine': { price: 25, icon: '/gems/gem-cyan.svg', color: '#06b6d4' },
          'Sapphire': { price: 50, icon: '/gems/gem-blue.svg', color: '#3b82f6' },
          'Magic': { price: 100, icon: '/gems/gem-purple.svg', color: '#a855f7' }
        };

        return Object.entries(game.bet_gems)
          .map(([gemType, quantity]) => ({
            type: gemType,
            quantity: quantity,
            price: gemDefinitions[gemType]?.price || 1,
            icon: gemDefinitions[gemType]?.icon || '/gems/gem-red.svg',
            color: gemDefinitions[gemType]?.color || '#ef4444'
          }))
          .filter(gem => gem.quantity > 0)
          .sort((a, b) => a.price - b.price); // Sort by price ascending
      };

      const sortedGems = getSortedGems();
      const totalGemsValue = getTotalGemsValue();

      return (
        <div className="bg-[#09295e] border border-[#23d364] border-opacity-30 hover:border-opacity-50 rounded-lg p-4 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg">
          <div className="flex items-center space-x-4">
            {/* Bot Avatar */}
            <div className="flex-shrink-0">
              <div className="w-12 h-12 rounded-full bg-blue-700 flex items-center justify-center text-white text-lg">
                🤖
              </div>
            </div>

            {/* Bot Info */}
            <div className="flex-1 min-w-0">
              {/* Bot Name - Always show "Bot" */}
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="text-white font-rajdhani font-bold text-lg">
                  Bot
                </h3>
                <span className="bg-blue-600 text-white text-xs font-rajdhani font-bold px-2 py-1 rounded">
                  {game.bot_type === 'HUMAN' ? 'Human-like' : 'AI'}
                </span>
              </div>

              {/* Gems Row with SVG Icons */}
              {sortedGems.length > 0 && (
                <div className="flex items-center space-x-2 mb-2 overflow-x-auto">
                  {sortedGems.map((gem, index) => (
                    <div key={gem.type} className="flex items-center space-x-1 flex-shrink-0">
                      <img 
                        src={gem.icon} 
                        alt={gem.type} 
                        className="w-4 h-4" 
                        style={{ filter: `hue-rotate(0deg)` }}
                      />
                      <span className="text-text-secondary text-xs font-rajdhani font-bold">
                        ×{gem.quantity}
                      </span>
                      {index < sortedGems.length - 1 && (
                        <span className="text-text-secondary text-xs mx-1">•</span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Total Gems Value (no dollar sign, just number) */}
              <div className="text-green-400 font-rajdhani font-bold text-xl">
                {Math.round(totalGemsValue)}
              </div>

              {/* Bot Status */}
              <div className="text-text-secondary text-xs font-rajdhani mt-1">
                Available for challenge
              </div>
            </div>

            {/* Action Button */}
            <div className="flex-shrink-0">
              <button
                onClick={() => onJoin(game.game_id || game.id)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 hover:scale-105"
              >
                Accept
              </button>
            </div>
          </div>
        </div>
      );
    }

    // Original GameCard for non-bot games (if needed)
    return (
      <div className="bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg p-4 hover:border-accent-primary hover:border-opacity-100 hover:shadow-lg hover:shadow-accent-primary/20 transition-all duration-300">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full flex items-center justify-center bg-green-700">
              👤
            </div>
            <div>
              <h4 className="font-rajdhani font-bold text-white">
                {game.creator_username || game.creator?.username || 'Player'}
              </h4>
              <p className="font-roboto text-xs text-text-secondary">
                {new Date(game.created_at).toLocaleTimeString()}
              </p>
            </div>
          </div>
          <span className="px-2 py-1 text-white text-xs rounded-full font-rajdhani bg-green-700">
            WAITING
          </span>
        </div>
        
        <div className="space-y-2 mb-4">
          <div className="flex justify-between">
            <span className="font-roboto text-text-secondary">Bet Amount:</span>
            <span className="font-rajdhani text-green-400 font-bold">
              ${game.bet_amount}
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
          onClick={() => onJoin(game.game_id || game.id)}
          className="w-full py-2 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300"
        >
          JOIN BATTLE
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

  const PaginationControls = ({ currentPage, totalItems, onPageChange, section, itemsPerPage }) => {
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
      
      // All games (including bot games) now have real game IDs
      // So we can directly try to join them
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
    } catch (error) {
      console.error('Error handling game join:', error);
      
      // Extract error message safely
      let errorMessage = 'Failed to join game';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Handle different error response formats
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          // FastAPI HTTPException format
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            // Pydantic validation errors
            errorMessage = errorData.detail.map(err => err.msg || err.message || 'Validation error').join(', ');
          } else if (typeof errorData.detail === 'object') {
            errorMessage = errorData.detail.msg || errorData.detail.message || 'Validation error';
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      showError(errorMessage);
    }
  };

  const handleCancelBet = async (gameId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.delete(`${API}/games/${gameId}/cancel`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('Cancel bet response:', response.data); // Debug log
      
      if (response.data && response.data.success) {
        showSuccess('Bet cancelled successfully');
        
        // 🔄 МГНОВЕННОЕ ОБНОВЛЕНИЕ LOBBY ПОСЛЕ ОТМЕНЫ СТАВКИ
        const globalRefresh = getGlobalLobbyRefresh();
        globalRefresh.triggerLobbyRefresh();
        console.log('❌ Bet cancelled - triggering lobby refresh');
        
        // Дополнительное обновление для надежности
        await fetchLobbyData();
        if (onUpdateUser) {
          onUpdateUser();
        }
      } else {
        console.error('Cancel bet failed - no success field:', response.data);
        showError('Failed to cancel bet - unexpected response format');
      }
    } catch (error) {
      console.error('Error cancelling bet:', error);
      console.error('Error response:', error.response?.data);
      
      // Extract error message safely
      let errorMessage = 'Failed to cancel bet';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map(err => err.msg || err.message || 'Validation error').join(', ');
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      showError(errorMessage);
      // Even if the API call fails, we can still refresh the data
      await fetchLobbyData();
    }
  };

  const getPaginatedItems = (items, page, itemsPerPage) => {
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return items.slice(startIndex, endIndex);
  };

  // Функция фильтрации доступных ставок по сумме
  const getFilteredAvailableBets = () => {
    let filtered = availableBets;
    
    if (betFilters.minAmount) {
      const minAmount = parseFloat(betFilters.minAmount);
      if (!isNaN(minAmount)) {
        filtered = filtered.filter(game => (game.bet_amount || 0) >= minAmount);
      }
    }
    
    if (betFilters.maxAmount) {
      const maxAmount = parseFloat(betFilters.maxAmount);
      if (!isNaN(maxAmount)) {
        filtered = filtered.filter(game => (game.bet_amount || 0) <= maxAmount);
      }
    }
    
    return filtered;
  };

  // Обработчики для фильтров
  const handleFilterChange = (field, value) => {
    setBetFilters(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Сбросить пагинацию при изменении фильтров
    setCurrentPage(prev => ({
      ...prev,
      availableBets: 1
    }));
  };

  const clearFilters = () => {
    setBetFilters({
      minAmount: '',
      maxAmount: ''
    });
    setCurrentPage(prev => ({
      ...prev,
      availableBets: 1
    }));
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
          {getPaginatedItems(myBets, currentPage.myBets, interfaceSettings.live_players.my_bets).map((game) => (
            <PlayerCard 
              key={game.game_id || game.id} 
              game={game} 
              user={user}
              isMyBet={true}
              onCancel={handleCancelBet}
              onUpdateUser={() => {
                fetchLobbyData();
                if (onUpdateUser) {
                  onUpdateUser();
                }
              }}
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
          itemsPerPage={interfaceSettings.live_players.my_bets}
        />
      </SectionBlock>

      {/* Available Bets */}
      <SectionBlock
        title="Available Bets"
        count={getFilteredAvailableBets().length}
        color="text-blue-400"
        icon={
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        }
      >
        {/* Фильтры по сумме ставки */}
        <div className="mb-4 bg-surface-dark border border-accent-primary border-opacity-20 rounded-lg p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-text-secondary">Мин. сумма:</label>
              <input
                type="number"
                placeholder="$0"
                value={betFilters.minAmount}
                onChange={(e) => handleFilterChange('minAmount', e.target.value)}
                className="w-20 px-2 py-1 bg-surface-card border border-accent-primary border-opacity-30 rounded text-white text-sm focus:outline-none focus:border-accent-primary"
                min="0"
                step="1"
              />
            </div>
            
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-text-secondary">Макс. сумма:</label>
              <input
                type="number"
                placeholder="$∞"
                value={betFilters.maxAmount}
                onChange={(e) => handleFilterChange('maxAmount', e.target.value)}
                className="w-20 px-2 py-1 bg-surface-card border border-accent-primary border-opacity-30 rounded text-white text-sm focus:outline-none focus:border-accent-primary"
                min="0"
                step="1"
              />
            </div>
            
            {(betFilters.minAmount || betFilters.maxAmount) && (
              <button
                onClick={clearFilters}
                className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
              >
                Очистить
              </button>
            )}
            
            <div className="text-sm text-text-secondary">
              Показано: {getFilteredAvailableBets().length} из {availableBets.length} ставок
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {getPaginatedItems(getFilteredAvailableBets(), currentPage.availableBets, interfaceSettings.live_players.available_bets).map((game) => (
            <PlayerCard 
              key={game.game_id || game.id} 
              game={game} 
              user={user}
              onOpenJoinBattle={handleOpenJoinBattle}
              onUpdateUser={() => {
                fetchLobbyData();
                if (onUpdateUser) {
                  onUpdateUser();
                }
              }}
              currentTime={new Date()}
            />
          ))}
          {getFilteredAvailableBets().length === 0 && availableBets.length > 0 && (
            <div className="col-span-full text-text-secondary text-center py-8">
              Нет ставок, соответствующих фильтрам
            </div>
          )}
          {availableBets.length === 0 && (
            <div className="col-span-full text-text-secondary text-center py-8">
              No available bets
            </div>
          )}
        </div>
        <PaginationControls
          currentPage={currentPage.availableBets}
          totalItems={getFilteredAvailableBets().length}
          onPageChange={handlePageChange}
          section="availableBets"
          itemsPerPage={interfaceSettings.live_players.available_bets}
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
          {getPaginatedItems(ongoingBattles, currentPage.ongoingBattles, interfaceSettings.live_players.ongoing_battles).map((game) => (
            <PlayerCard 
              key={game.game_id || game.id} 
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
          itemsPerPage={interfaceSettings.live_players.ongoing_battles}
        />
      </SectionBlock>
    </div>
  );

  const BotPlayersContent = () => (
    <div className="space-y-6 max-w-7xl mx-auto">
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {getPaginatedItems(availableBots, currentPage.availableBots, interfaceSettings.bot_players.available_bots).map((game) => (
            <PlayerCard 
              key={game.game_id || game.id} 
              game={game} 
              user={user}
              onOpenJoinBattle={handleOpenJoinBattle}
              onUpdateUser={() => {
                fetchLobbyData();
                if (onUpdateUser) {
                  onUpdateUser();
                }
              }}
              currentTime={new Date()}
              isBot={true}
            />
          ))}
          {availableBots.length === 0 && (
            <div className="col-span-full text-text-secondary text-center py-8">
              No available bots
            </div>
          )}
        </div>
        <PaginationControls
          currentPage={currentPage.availableBots}
          totalItems={availableBots.length}
          onPageChange={handlePageChange}
          section="availableBots"
          itemsPerPage={interfaceSettings.bot_players.available_bots}
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {getPaginatedItems(ongoingBotBattles, currentPage.ongoingBotBattles, interfaceSettings.bot_players.ongoing_bot_battles).map((game) => (
            <PlayerCard 
              key={game.game_id || game.id} 
              game={game} 
              user={user}
              isOngoing={true}
              isBot={true}
              onUpdateUser={() => {
                fetchLobbyData();
                if (onUpdateUser) {
                  onUpdateUser();
                }
              }}
              currentTime={new Date()}
            />
          ))}
          {ongoingBotBattles.length === 0 && (
            <div className="col-span-full text-text-secondary text-center py-8">
              No ongoing bot battles
            </div>
          )}
        </div>
        <PaginationControls
          currentPage={currentPage.ongoingBotBattles}
          totalItems={ongoingBotBattles.length}
          onPageChange={handlePageChange}
          section="ongoingBotBattles"
          itemsPerPage={interfaceSettings.bot_players.ongoing_bot_battles}
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

      {/* Create Bet Button */}
      <div className="text-center mb-8">
        <button 
          onClick={() => {
            game.createBet();
            modalSound.onOpen();
            setShowCreateBetModal(true);
          }}
          {...hoverProps}
          className="px-8 py-4 bg-gradient-to-r from-green-500 to-green-600 text-white font-rajdhani font-bold text-xl rounded-lg hover:scale-105 hover:from-green-400 hover:to-green-500 transition-all duration-300 shadow-lg hover:shadow-green-500/50"
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
              onClick={() => {
                ui.click();
                setActiveTab(tab.id);
              }}
              {...hoverProps}
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
          onClose={() => {
            modalSound.onClose();
            setShowCreateBetModal(false);
          }}
          onUpdateUser={onUpdateUser}
        />
      )}

      {showJoinBattleModal && selectedBetForJoin && (
        <JoinBattleModal
          bet={{
            id: selectedBetForJoin.game_id || selectedBetForJoin.id,
            bet_amount: selectedBetForJoin.bet_amount,
            bet_gems: selectedBetForJoin.bet_gems,
            creator: selectedBetForJoin.creator,
            is_bot_game: selectedBetForJoin.is_bot_game  // Флаг игры с ботом
          }}
          user={user}
          onClose={handleCloseJoinBattle}
          onUpdateUser={() => {
            fetchLobbyData();
            if (onUpdateUser) {
              onUpdateUser();
            }
            // НЕ закрываем модальное окно здесь
          }}
        />
      )}
    </div>
  );
};

export default Lobby;