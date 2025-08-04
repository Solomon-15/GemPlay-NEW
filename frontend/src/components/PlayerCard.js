import React, { useState, useMemo, useCallback } from 'react';
import { useGems } from './GemsContext';
import { formatDollarsAsGems } from '../utils/gemUtils';

const PlayerCard = React.memo(({ 
  game, 
  isMyBet = false, 
  isOngoing = false,
  isBot = false,
  onAccept, 
  onCancel,
  onOpenJoinBattle,  // Новый пропс для открытия модального окна
  onUpdateUser,
  currentTime = new Date(),
  user
}) => {
  const { gemsDefinitions, getGemByType } = useGems();
  // const [showAcceptModal, setShowAcceptModal] = useState(false);

  // console.log('🔄 PlayerCard render:', {
  //   gameId: game.game_id || game.id,
  //   timestamp: new Date().toISOString()
  // });

  // Get time remaining for auto-cancel (24 hours format)
  const getTimeRemaining = () => {
    if (!game.created_at) return null;
    
    const createdTime = new Date(game.created_at);
    const cancelTime = new Date(createdTime.getTime() + 24 * 60 * 60 * 1000); // 24 hours later
    const now = currentTime;
    const diff = cancelTime - now;
    
    if (diff <= 0) return null;
    
    // Return 24-hour format time when it will be cancelled
    const hours = cancelTime.getHours();
    const minutes = cancelTime.getMinutes();
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  };

  const cardBackground = useMemo(() => {
    const baseBackground = 'bg-[#09295e]';
    
    if (isMyBet && game.status === 'ACTIVE') {
      return `bg-[#23233e] border-[#23d364] border-opacity-40 hover:border-opacity-60`;
    }
    
    return `${baseBackground} border-[#23d364] border-opacity-30 hover:border-opacity-50`;
  }, [isMyBet, game.status]);

  const formatUsername = useCallback((username) => {
    if (!username) return 'Player';
    return username.length > 15 ? username.substring(0, 15) + '...' : username;
  }, []);

  const formattedUsername = useMemo(() => 
    formatUsername(game.creator_info?.username || game.creator_username || game.creator?.username || 'Unknown Player'), 
    [game.creator_info?.username, game.creator_username, game.creator?.username, formatUsername]
  );

  // Calculate total bet amount
  const getTotalBetAmount = () => {
    // Check if we have bet_gems data (old format)
    if (game.bet_gems) {
      return Object.entries(game.bet_gems).reduce((total, [gemType, quantity]) => {
        const gem = getGemByType(gemType);
        return total + (gem ? gem.price * quantity : 0);
      }, 0);
    }
    
    // Use bet_amount from API (new format)
    if (game.bet_amount) {
      return game.bet_amount;
    }
    
    return 0;
  };

  // Get sorted gems by price (ascending) - ONLY from Inventory data
  const getSortedGems = () => {
    if (!game.bet_gems) {
      // For new format with bet_amount, distribute across gem types like in Available Bets
      if (game.bet_amount && gemsDefinitions.length > 0) {
        const gems = [];
        let remainingAmount = game.bet_amount;
        
        // Sort gems by price (highest to lowest) to distribute efficiently
        const sortedGemDefs = [...gemsDefinitions].sort((a, b) => b.price - a.price);
        
        for (const gem of sortedGemDefs) {
          if (remainingAmount <= 0) break;
          
          const maxQuantity = Math.floor(remainingAmount / gem.price);
          if (maxQuantity > 0) {
            // Take some gems of this type (not all to create variety)
            const quantity = Math.min(maxQuantity, Math.max(1, Math.floor(Math.random() * 3) + 1));
            gems.push({ ...gem, quantity });
            remainingAmount -= quantity * gem.price;
          }
        }
        
        // If there's still remaining amount, add it to the cheapest gem
        if (remainingAmount > 0 && sortedGemDefs.length > 0) {
          const cheapestGem = sortedGemDefs[sortedGemDefs.length - 1];
          const additionalQuantity = Math.floor(remainingAmount / cheapestGem.price);
          if (additionalQuantity > 0) {
            const existingGem = gems.find(g => g.type === cheapestGem.type);
            if (existingGem) {
              existingGem.quantity += additionalQuantity;
            } else {
              gems.push({ ...cheapestGem, quantity: additionalQuantity });
            }
          }
        }
        
        return gems.sort((a, b) => a.price - b.price);
      }
      return [];
    }
    
    return Object.entries(game.bet_gems)
      .map(([gemType, quantity]) => {
        const gem = getGemByType(gemType);
        return gem ? { ...gem, quantity } : null;
      })
      .filter(Boolean)
      .sort((a, b) => a.price - b.price); // Sort by price ascending
  };

  // Determine avatar based on gender or bot type
  const getAvatarIcon = () => {
    if (game.is_human_bot || game.creator_type === 'human_bot' || game.bot_type === 'HUMAN') {
      const gender = game.creator?.gender || 'male';
      return gender === 'female' ? '/Women.svg' : '/Men.svg';
    }
    if (isBot) {
      return '🤖'; // Bot emoji
    }
    const gender = game.creator?.gender || 'male';
    return gender === 'female' ? '/Women.svg' : '/Men.svg';
  };

  const handleAcceptClick = useCallback(() => {
    if (onAccept) {
      onAccept(game.game_id || game.id); // Передаем ID игры, а не объект
    } else if (onOpenJoinBattle) {
      onOpenJoinBattle(game); // Передаем весь объект игры
    }
  }, [onAccept, onOpenJoinBattle, game.game_id, game.id, game]);

  const handleCancelClick = useCallback(() => {
    if (onCancel) {
      onCancel(game.game_id || game.id);
    }
  }, [onCancel, game.game_id, game.id]);

  const totalAmount = useMemo(() => getTotalBetAmount(), [game.bet_amount, game.gems, gemsDefinitions]);
  const timeRemaining = useMemo(() => getTimeRemaining(), [game.created_at, currentTime]);
  const sortedGems = useMemo(() => getSortedGems(), [game.gems, gemsDefinitions]);
  const avatarIcon = useMemo(() => getAvatarIcon(), [game.is_human_bot, game.creator_type, game.bot_type, game.creator?.gender, isBot]);

  return (
    <>
      <div className={`${cardBackground} border rounded-lg p-4 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg`}>
        <div className="flex items-center space-x-4">
          {/* Avatar */}
          <div className="flex-shrink-0">
            {isBot ? (
              <div className="w-14 h-14 rounded-full bg-blue-700 flex items-center justify-center text-white text-lg">
                🤖
              </div>
            ) : (
              <img 
                src={avatarIcon} 
                alt="Player Avatar" 
                className="w-14 h-14 rounded-full bg-surface-sidebar p-1"
              />
            )}
          </div>

          {/* Player Info */}
          <div className="flex-1 min-w-0">
            {/* Username */}
            <div className="flex items-center space-x-2 mb-1">
              <h3 className="text-white font-rajdhani font-bold text-lg truncate">
                {isBot ? 'Bot' : formattedUsername}
              </h3>
              {isMyBet && (
                <span className="bg-blue-600 text-white text-xs font-rajdhani font-bold px-2 py-1 rounded">
                  My Bet
                </span>
              )}
              {isBot && (
                <span className="bg-blue-600 text-white text-xs font-rajdhani font-bold px-2 py-1 rounded">
                  {game.bot_type === 'HUMAN' ? 'Human-like' : 'AI'}
                </span>
              )}
            </div>

            {/* Gems Row */}
            <div className="flex items-center space-x-1 mb-2 overflow-x-auto">
              {sortedGems.map((gem, index) => (
                <div key={gem.type} className="flex items-center space-x-1 flex-shrink-0">
                  <img src={gem.icon} alt={gem.name} className="w-4 h-4" />
                  <span className="text-text-secondary text-xs font-rajdhani">
                    {gem.quantity}
                  </span>
                  {index < sortedGems.length - 1 && (
                    <span className="text-text-secondary text-xs">•</span>
                  )}
                </div>
              ))}
            </div>

            {/* Total Amount */}
            <div className="text-green-400 font-rajdhani font-bold text-xl">
              {formatDollarsAsGems(totalAmount)}
            </div>

            {/* Timer */}
            {timeRemaining && (
              <div className="text-text-secondary text-xs font-rajdhani mt-1">
                Auto-cancel: {timeRemaining}
              </div>
            )}
          </div>

          {/* Action Button */}
          <div className="flex-shrink-0">
            {isMyBet ? (
              (game.status === 'ACTIVE' || game.status === 'REVEAL') ? (
                <button
                  disabled
                  className="px-4 py-2 bg-gray-600 text-gray-400 font-rajdhani font-bold rounded-lg cursor-not-allowed"
                >
                  In Progress
                </button>
              ) : (
                <button
                  onClick={handleCancelClick}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 hover:scale-105"
                >
                  Cancel
                </button>
              )
            ) : isOngoing ? (
              <button
                disabled
                className="px-4 py-2 bg-orange-600 text-white font-rajdhani font-bold rounded-lg cursor-not-allowed"
              >
                Busy
              </button>
            ) : (
              <button
                onClick={handleAcceptClick}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 hover:scale-105"
              >
                Accept
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
});

PlayerCard.displayName = 'PlayerCard';

export default PlayerCard;