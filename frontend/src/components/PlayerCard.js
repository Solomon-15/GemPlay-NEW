import React, { useState } from 'react';
import { useGems } from './GemsContext';
import { formatCurrencyWithSymbol } from '../utils/economy';

const PlayerCard = ({ 
  game, 
  isMyBet = false, 
  isOngoing = false,
  onAccept, 
  onCancel,
  onOpenJoinBattle,  // Новый пропс для открытия модального окна
  onUpdateUser,
  currentTime = new Date(),
  user
}) => {
  const { gemsDefinitions, getGemByType } = useGems();
  // Убираем локальное состояние модального окна
  // const [showAcceptModal, setShowAcceptModal] = useState(false);

  // ВРЕМЕННЫЙ ЛОГ ДЛЯ ОТЛАДКИ
  console.log('🔄 PlayerCard render:', {
    gameId: game.game_id || game.id,
    // showAcceptModal,
    timestamp: new Date().toISOString()
  });

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

  // Get card background color based on game status and type
  const getCardBackground = () => {
    // Основной фон для всех карточек - тёмно-синий мистический
    const baseBackground = 'bg-[#09295e]';
    
    // Если это карточка в процессе игры (ACTIVE status для создателя)
    if (isMyBet && game.status === 'ACTIVE') {
      return `bg-[#23233e] border-[#23d364] border-opacity-40 hover:border-opacity-60`;
    }
    
    // Стандартное оформление с зелёной рамкой
    return `${baseBackground} border-[#23d364] border-opacity-30 hover:border-opacity-50`;
  };

  // Format username to max 15 characters
  const formatUsername = (username) => {
    if (!username) return 'Player';
    return username.length > 15 ? username.substring(0, 15) + '...' : username;
  };

  // Calculate total bet amount
  const getTotalBetAmount = () => {
    if (!game.bet_gems) return 0;
    
    return Object.entries(game.bet_gems).reduce((total, [gemType, quantity]) => {
      const gem = getGemByType(gemType);
      return total + (gem ? gem.price * quantity : 0);
    }, 0);
  };

  // Get sorted gems by price (ascending) - ONLY from Inventory data
  const getSortedGems = () => {
    if (!game.bet_gems) return [];
    
    return Object.entries(game.bet_gems)
      .map(([gemType, quantity]) => {
        const gem = getGemByType(gemType);
        return gem ? { ...gem, quantity } : null;
      })
      .filter(Boolean)
      .sort((a, b) => a.price - b.price); // Sort by price ascending
  };

  // Determine avatar based on gender
  const getAvatarIcon = () => {
    const gender = game.creator?.gender || 'male';
    return gender === 'female' ? '/Women.svg' : '/Men.svg';
  };

  const handleAcceptClick = () => {
    if (onAccept) {
      onAccept(game.game_id || game.id); // Передаем ID игры, а не объект
    } else if (onOpenJoinBattle) {
      onOpenJoinBattle(game); // Передаем весь объект игры
    }
  };

  const handleCancelClick = () => {
    if (onCancel) {
      onCancel(game.game_id || game.id);
    }
  };

  const totalAmount = getTotalBetAmount();
  const timeRemaining = getTimeRemaining();
  const sortedGems = getSortedGems();

  return (
    <>
      <div className={`${getCardBackground()} border rounded-lg p-4 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg`}>
        <div className="flex items-center space-x-4">
          {/* Avatar */}
          <div className="flex-shrink-0">
            <img 
              src={getAvatarIcon()} 
              alt="Player Avatar" 
              className="w-12 h-12 rounded-full bg-surface-sidebar p-1"
            />
          </div>

          {/* Player Info */}
          <div className="flex-1 min-w-0">
            {/* Username */}
            <div className="flex items-center space-x-2 mb-1">
              <h3 className="text-white font-rajdhani font-bold text-lg truncate">
                {formatUsername(game.creator?.username || 'Player')}
              </h3>
              {isMyBet && (
                <span className="bg-blue-600 text-white text-xs font-rajdhani font-bold px-2 py-1 rounded">
                  My Bet
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
              {formatCurrencyWithSymbol(totalAmount)}
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
              <button
                onClick={handleCancelClick}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 hover:scale-105"
              >
                Cancel
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
};

export default PlayerCard;