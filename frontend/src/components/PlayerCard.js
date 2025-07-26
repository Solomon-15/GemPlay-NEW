import React, { useState, useMemo, useCallback } from 'react';
import { useGems } from './GemsContext';
import { formatCurrencyWithSymbol, formatDollarAmount } from '../utils/economy';
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
  // Убираем локальное состояние модального окна
  // const [showAcceptModal, setShowAcceptModal] = useState(false);

  // УБИРАЕМ ВРЕМЕННЫЙ ЛОГ ДЛЯ ОТЛАДКИ - он вызывает лишние рендеры
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

  // Мемоизируем функцию получения фона карточки
  const cardBackground = useMemo(() => {
    // Основной фон для всех карточек - тёмно-синий мистический
    const baseBackground = 'bg-[#09295e]';
    
    // Если это карточка в процессе игры (ACTIVE status для создателя)
    if (isMyBet && game.status === 'ACTIVE') {
      return `bg-[#23233e] border-[#23d364] border-opacity-40 hover:border-opacity-60`;
    }
    
    // Стандартное оформление с зелёной рамкой
    return `${baseBackground} border-[#23d364] border-opacity-30 hover:border-opacity-50`;
  }, [isMyBet, game.status]);

  // Мемоизируем функцию форматирования имени пользователя
  const formatUsername = useCallback((username) => {
    if (!username) return 'Player';
    return username.length > 15 ? username.substring(0, 15) + '...' : username;
  }, []);

  // Мемоизируем отформатированное имя
  const formattedUsername = useMemo(() => 
    formatUsername(game.creator?.username || 'Player'), 
    [game.creator?.username, formatUsername]
  );

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

  // Determine avatar based on gender or bot type
  const getAvatarIcon = () => {
    // Проверяем, является ли это Human-ботом
    if (game.is_human_bot || game.creator_type === 'human_bot' || game.bot_type === 'HUMAN') {
      // Для Human-ботов используем аватарки по полу
      const gender = game.creator?.gender || 'male';
      return gender === 'female' ? '/Women.svg' : '/Men.svg';
    }
    // Для обычных ботов используем эмодзи робота
    if (isBot) {
      return '🤖'; // Bot emoji
    }
    // Для обычных пользователей используем аватарки по полу
    const gender = game.creator?.gender || 'male';
    return gender === 'female' ? '/Women.svg' : '/Men.svg';
  };

  // Мемоизируем функции-обработчики
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

  // Мемоизируем вычисления
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
                {isBot ? 'Bot' : formatUsername(game.creator?.username || 'Player')}
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
              // Если игра в процессе (ACTIVE или REVEAL status)
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
              // Если это ongoing battle (для пользователя)
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