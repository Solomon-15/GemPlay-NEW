import React, { memo, useCallback, useMemo, useState, useEffect } from 'react';
import { useGems } from './GemsContext';
import { formatDollarsAsGems } from '../utils/gemUtils';

const PlayerCard = memo(({ 
  game, 
  user,
  isMyBet = false,
  isOngoing = false,
  onAccept,
  onCancel,
  onOpenJoinBattle 
}) => {
  const { gemsDefinitions, getGemByType } = useGems();

  // Защита от многократных нажатий
  const [isAccepting, setIsAccepting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  
  const isBot = game.creator_type === 'bot' || game.creator_type === 'human_bot' || game.is_bot_game;
  
  // Debug logging
  if (game.creator_username === 'Bot' || game.creator_info?.username === 'Bot') {
    console.log('Bot card data:', {
      creator_type: game.creator_type,
      bot_type: game.bot_type,
      is_bot_game: game.is_bot_game,
      isBot: isBot,
      creator_username: game.creator_username || game.creator_info?.username
    });
  }
  
  // Проверка доступности средств для игры
  const canAcceptBet = useMemo(() => {
    if (!user || !game) return false;
    
    // Получаем сумму ставки
    let betAmount = 0;
    if (game.bet_amount) {
      betAmount = game.bet_amount;
    } else if (game.bet_gems && Object.keys(game.bet_gems).length > 0) {
      betAmount = Object.entries(game.bet_gems).reduce((total, [gemType, quantity]) => {
        const gem = getGemByType(gemType);
        const gemValue = gem ? gem.price * quantity : 0;
        return total + gemValue;
      }, 0);
    }
    
    const COMMISSION_RATE = 0.03;
    const isBotGame = game.is_bot_game || false;
    const commissionRequired = isBotGame ? 0 : betAmount * COMMISSION_RATE;
    
    // Проверка баланса для комиссии
    const totalBalance = user.virtual_balance || 0;
    const frozenBalance = user.frozen_balance || 0;
    const availableForCommission = totalBalance - frozenBalance;
    
    if (availableForCommission < commissionRequired) {
      return false;
    }
    
    // Проверка наличия достаточного количества гемов
    const totalGemValue = gemsDefinitions.reduce((sum, gem) => 
      sum + (gem.available_quantity * gem.price), 0
    );
    
    return totalGemValue >= betAmount;
  }, [user, game, gemsDefinitions, getGemByType]);
  
  // Эффект для автоматической разблокировки кнопки Accept когда появляются средства
  useEffect(() => {
    if (isAccepting && canAcceptBet) {
      // Если кнопка была заблокирована из-за недостатка средств,
      // но теперь средства появились - разблокируем
      setIsAccepting(false);
    }
  }, [canAcceptBet, isAccepting]);
  
  // Get time remaining for auto-cancel (static HH:MM of cancel time)
  const getCancelTimeHHMM = () => {
    if (!game.created_at) return null;
    const createdTime = new Date(game.created_at);
    const cancelTime = new Date(createdTime.getTime() + 24 * 60 * 60 * 1000); // 24 hours later
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
    if (game.bet_gems && Object.keys(game.bet_gems).length > 0) {
      const total = Object.entries(game.bet_gems).reduce((total, [gemType, quantity]) => {
        const gem = getGemByType(gemType);
        const gemValue = gem ? gem.price * quantity : 0;
        return total + gemValue;
      }, 0);
      return total;
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
      const gender = game.creator_info?.gender || game.creator?.gender || 'male';
      return gender === 'female' ? '/Women.svg' : '/Men.svg';
    }
    if (isBot) {
      return '🤖'; // Bot emoji
    }
    const gender = game.creator_info?.gender || game.creator?.gender || 'male';
    return gender === 'female' ? '/Women.svg' : '/Men.svg';
  };

  const handleAcceptClick = useCallback(() => {
    if (isAccepting) return; // Защита от повторных нажатий
    
    // Проверяем доступность средств
    if (!canAcceptBet) {
      // Получаем сумму ставки для расчета комиссии
      let betAmount = 0;
      if (game.bet_amount) {
        betAmount = game.bet_amount;
      } else if (game.bet_gems && Object.keys(game.bet_gems).length > 0) {
        betAmount = Object.entries(game.bet_gems).reduce((total, [gemType, quantity]) => {
          const gem = getGemByType(gemType);
          const gemValue = gem ? gem.price * quantity : 0;
          return total + gemValue;
        }, 0);
      }
      
      const COMMISSION_RATE = 0.03;
      const isBotGame = game.is_bot_game || false;
      const commissionRequired = isBotGame ? 0 : betAmount * COMMISSION_RATE;
      
      // Проверка баланса для комиссии
      const totalBalance = user.virtual_balance || 0;
      const frozenBalance = user.frozen_balance || 0;
      const availableForCommission = totalBalance - frozenBalance;
      
      if (availableForCommission < commissionRequired) {
        // Показываем ошибку о недостатке средств для комиссии
        if (onOpenJoinBattle) {
          onOpenJoinBattle(game); // Открываем модалку, которая покажет ошибку
        }
        return;
      }
      
      // Проверка наличия гемов
      const totalGemValue = gemsDefinitions.reduce((sum, gem) => 
        sum + (gem.available_quantity * gem.price), 0
      );
      
      if (totalGemValue < betAmount) {
        // Показываем ошибку о недостатке гемов
        if (onOpenJoinBattle) {
          onOpenJoinBattle(game); // Открываем модалку, которая покажет ошибку
        }
        return;
      }
    }
    
    setIsAccepting(true);
    
    if (onAccept) {
      onAccept(game.game_id || game.id); // Передаем ID игры, а не объект
    } else if (onOpenJoinBattle) {
      onOpenJoinBattle(game); // Передаем весь объект игры
    }
    
    // Сбрасываем флаг только если средств достаточно
    if (canAcceptBet) {
      setTimeout(() => setIsAccepting(false), 1000);
    }
    // Если средств недостаточно, флаг остается true и кнопка остается заблокированной
  }, [onAccept, onOpenJoinBattle, game, isAccepting, canAcceptBet, user, gemsDefinitions, getGemByType]);

  const handleCancelClick = useCallback(() => {
    if (isCancelling) return; // Защита от повторных нажатий
    
    setIsCancelling(true);
    
    if (onCancel) {
      onCancel(game.game_id || game.id);
    }
    
    // Сбрасываем флаг через небольшую задержку на случай ошибки
    setTimeout(() => setIsCancelling(false), 1000);
  }, [onCancel, game.game_id, game.id, isCancelling]);

  const totalAmount = useMemo(() => getTotalBetAmount(), [game.bet_amount, game.bet_gems, gemsDefinitions]);
  const cancelAtHHMM = useMemo(() => getCancelTimeHHMM(), [game.created_at]);
  const sortedGems = useMemo(() => getSortedGems(), [game.bet_gems, gemsDefinitions]);
  const avatarIcon = useMemo(() => getAvatarIcon(), [game.is_human_bot, game.creator_type, game.bot_type, game.creator?.gender, isBot]);

  return (
    <>
      <div className={`${cardBackground} border rounded-lg p-4 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg`} style={{ willChange: 'transform' }}>
        <div className="flex items-center space-x-4">
          {/* Avatar */}
          <div className="flex-shrink-0">
            {isBot && game.is_bot_game && game.bot_type !== 'HUMAN' ? (
              <div className="w-14 h-14 rounded-full bg-purple-600 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24"
                     fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <title>Bot 01 — Head + antenna</title>
                  <line x1="12" y1="4" x2="12" y2="7"/>
                  <circle cx="12" cy="3" r="1"/>
                  <rect x="5" y="7" width="14" height="10" rx="3"/>
                  <line x1="3" y1="12" x2="5" y2="12"/>
                  <line x1="19" y1="12" x2="21" y2="12"/>
                  <circle cx="9.5" cy="12" r="1" fill="white" stroke="none"/>
                  <circle cx="14.5" cy="12" r="1" fill="white" stroke="none"/>
                  <line x1="8.5" y1="15" x2="15.5" y2="15"/>
                </svg>
              </div>
            ) : (
              <img 
                src={avatarIcon} 
                alt="Player Avatar" 
                className="w-14 h-14 rounded-full object-cover"
              />
            )}
          </div>

          {/* Player Info */}
          <div className="flex-1 min-w-0">
            {/* Username */}
            <div className="flex items-center space-x-2 mb-1">
              <h3 className="text-white font-rajdhani font-bold text-lg truncate">
                {formattedUsername}
              </h3>
              {isMyBet && (
                <span className="bg-blue-600 text-white text-xs font-rajdhani font-bold px-2 py-1 rounded">
                  My Bet
                </span>
              )}
              {isBot && game.creator_type === 'bot' && (
                <span className="bg-blue-600 text-white text-xs font-rajdhani font-bold px-2 py-1 rounded">
                  AI
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
            {cancelAtHHMM && (
              <div className="text-text-secondary text-xs font-rajdhani mt-1">
                Auto-cancel: {cancelAtHHMM}
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
                  disabled={isCancelling}
                  className={`px-4 py-2 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed ${
                    isCancelling 
                      ? 'bg-gray-600' 
                      : 'bg-red-600 hover:bg-red-700 hover:scale-105'
                  }`}
                >
                  {isCancelling ? 'Cancelling...' : 'Cancel'}
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
                disabled={isAccepting || !canAcceptBet}
                className={`px-4 py-2 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed ${
                  isAccepting || !canAcceptBet
                    ? 'bg-gray-600' 
                    : 'bg-green-600 hover:bg-green-700 hover:scale-105'
                }`}
                title={!canAcceptBet ? 'Insufficient funds or gems' : ''}
              >
                {isAccepting ? 'Accepting...' : 'Accept'}
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