import React, { useState } from 'react';
import { useGems } from './GemsContext';
import AcceptBetModal from './AcceptBetModal';
import { formatCurrencyWithSymbol } from '../utils/economy';

const PlayerCard = ({ 
  game, 
  isMyBet = false, 
  isOngoing = false,
  onAccept, 
  onCancel,
  currentTime = new Date(),
  user
}) => {
  const { gemsDefinitions, getGemByType } = useGems();
  const [showAcceptModal, setShowAcceptModal] = useState(false);

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

  // Get card background color based on time remaining
  const getCardBackground = () => {
    if (!game.created_at) return 'bg-surface-card border-border-primary';
    
    const createdTime = new Date(game.created_at);
    const cancelTime = new Date(createdTime.getTime() + 24 * 60 * 60 * 1000);
    const now = currentTime;
    const diff = cancelTime - now;
    const hoursRemaining = diff / (1000 * 60 * 60);
    
    if (hoursRemaining <= 1) return 'bg-red-900/20 border-red-500/50';
    if (hoursRemaining <= 3) return 'bg-yellow-900/20 border-yellow-500/50';
    return 'bg-surface-card border-border-primary';
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

  // Get sorted gems by price (ascending)
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
      onAccept(game);
    } else {
      setShowAcceptModal(true);
    }
  };

  const handleCancelClick = () => {
    if (onCancel) {
      onCancel(game.id);
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

      {/* Accept Bet Modal */}
      {showAcceptModal && (
        <AcceptBetModal
          bet={{
            bet_amount: totalAmount,
            bet_gems: game.bet_gems,
            creator: game.creator
          }}
          onClose={() => setShowAcceptModal(false)}
          onUpdateUser={() => {
            // Refresh user data if needed
          }}
        />
      )}
    </>
  );
};

export default PlayerCard;
  const calculateTotalBet = () => {
    let total = parseFloat(game.bet_amount) || 0;
    
    if (game.bet_gems && typeof game.bet_gems === 'object') {
      Object.entries(game.bet_gems).forEach(([type, quantity]) => {
        if (quantity > 0) {
          const gem = getGemByType(type);
          const gemValue = gem ? gem.value : 1;
          total += gemValue * quantity;
        }
      });
    }
    
    return total;
  };

  // Sort gems by value (ascending order)
  const getSortedGems = () => {
    if (!game.bet_gems || typeof game.bet_gems !== 'object') return [];
    
    return gemsDefinitions
      .filter(gem => game.bet_gems[gem.name] > 0)
      .sort((a, b) => a.value - b.value)
      .map(gem => ({
        ...gem,
        quantity: game.bet_gems[gem.name]
      }));
  };

  const timeRemaining = getTimeRemaining();
  const cardBackground = getCardBackground();
  const totalBet = calculateTotalBet();
  const sortedGems = getSortedGems();

  return (
    <div className={`${cardBackground} border rounded-lg p-4 hover:border-accent-primary transition-all duration-300 min-w-[280px] max-w-[320px]`}>
      {/* Top row: Avatar, Username, Badge, Time */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          {/* Avatar */}
          <div className="w-12 h-12 rounded-full bg-surface-sidebar flex items-center justify-center overflow-hidden">
            <img 
              src={game.creator?.gender === 'female' ? '/Women.svg' : '/Men.svg'} 
              alt="Avatar" 
              className="w-10 h-10"
            />
          </div>
          
          {/* Username and Badge */}
          <div>
            <h3 className="font-rajdhani font-bold text-white text-lg leading-tight">
              {formatUsername(game.creator?.username || game.creator_username)}
            </h3>
            {isMyBet && (
              <span className="px-2 py-1 bg-green-600 text-white text-xs rounded-full font-rajdhani font-bold">
                My Bet
              </span>
            )}
          </div>
        </div>
        
        {/* Timer */}
        {timeRemaining && (
          <div className="text-right">
            <div className="text-white font-rajdhani font-bold text-sm">
              {timeRemaining}
            </div>
            <div className="text-text-secondary text-xs">
              auto-cancel
            </div>
          </div>
        )}
      </div>

      {/* Bottom row: Gems, Total, Button */}
      <div className="flex items-center justify-between">
        {/* Gems */}
        <div className="flex items-center space-x-2 flex-1">
          {sortedGems.map((gem) => (
            <div key={gem.name} className="flex items-center space-x-1">
              <img 
                src={gem.icon} 
                alt={gem.name} 
                className="w-5 h-5"
              />
              <span className="text-white font-rajdhani text-sm font-bold">
                {gem.quantity}
              </span>
            </div>
          ))}
          {sortedGems.length === 0 && (
            <span className="text-text-secondary text-sm font-roboto">
              No gems
            </span>
          )}
        </div>
        
        {/* Total amount */}
        <div className="text-right mx-4">
          <div className="text-accent-primary font-rajdhani font-bold text-xl">
            ${totalBet.toFixed(2)}
          </div>
        </div>

        {/* Action button */}
        <div className="flex-shrink-0">
          {isOngoing ? (
            <div className="px-4 py-2 bg-blue-600 text-white font-rajdhani font-bold rounded-lg text-sm">
              In Progress
            </div>
          ) : isMyBet ? (
            <button
              onClick={() => {
                console.log('Cancel button clicked for game:', game.id);
                onCancel && onCancel(game.id);
              }}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-rajdhani font-bold rounded-lg transition-colors text-sm"
            >
              Cancel
            </button>
          ) : (
            <button
              onClick={() => {
                console.log('Accept button clicked for game:', game.id);
                onAccept && onAccept(game.id);
              }}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-rajdhani font-bold rounded-lg transition-colors text-sm"
            >
              Accept
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayerCard;