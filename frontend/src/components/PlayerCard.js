import React from 'react';

const PlayerCard = ({ 
  game, 
  isMyBet = false, 
  isOngoing = false,
  onAccept, 
  onCancel,
  currentTime = new Date()
}) => {
  // Gem definitions with colors and order
  const gemDefinitions = [
    { name: 'Ruby', color: 'text-red-500', icon: '/gems/gem-red.svg' },
    { name: 'Amber', color: 'text-orange-500', icon: '/gems/gem-orange.svg' },
    { name: 'Topaz', color: 'text-yellow-500', icon: '/gems/gem-yellow.svg' },
    { name: 'Emerald', color: 'text-green-500', icon: '/gems/gem-green.svg' },
    { name: 'Aquamarine', color: 'text-cyan-500', icon: '/gems/gem-cyan.svg' },
    { name: 'Sapphire', color: 'text-blue-500', icon: '/gems/gem-blue.svg' },
    { name: 'Magic', color: 'text-purple-500', icon: '/gems/gem-purple.svg' }
  ];

  // Get time remaining for auto-cancel
  const getTimeRemaining = () => {
    if (!game.auto_cancel_at) return null;
    
    const cancelTime = new Date(game.auto_cancel_at);
    const now = currentTime;
    const diff = cancelTime - now;
    
    if (diff <= 0) return null;
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  };

  // Get card background color based on time remaining
  const getCardBackground = () => {
    if (!game.auto_cancel_at) return 'bg-surface-card';
    
    const cancelTime = new Date(game.auto_cancel_at);
    const now = currentTime;
    const diff = cancelTime - now;
    const hoursRemaining = diff / (1000 * 60 * 60);
    
    if (hoursRemaining <= 1) return 'bg-red-900/20 border-red-500/50';
    if (hoursRemaining <= 3) return 'bg-yellow-900/20 border-yellow-500/50';
    return 'bg-surface-card';
  };

  // Format username to max 15 characters
  const formatUsername = (username) => {
    if (!username) return 'Player';
    return username.length > 15 ? username.substring(0, 15) + '...' : username;
  };

  // Calculate total bet amount
  const calculateTotalBet = () => {
    let total = parseFloat(game.bet_amount) || 0;
    
    if (game.bet_gems && typeof game.bet_gems === 'object') {
      // Add gem values (simplified calculation)
      Object.entries(game.bet_gems).forEach(([type, quantity]) => {
        if (quantity > 0) {
          // Simple gem pricing
          const gemPrices = {
            'Ruby': 5, 'Amber': 3, 'Topaz': 2, 'Emerald': 8, 
            'Aquamarine': 6, 'Sapphire': 10, 'Magic': 15
          };
          total += (gemPrices[type] || 1) * quantity;
        }
      });
    }
    
    return total;
  };

  // Sort gems by value (ascending order)
  const getSortedGems = () => {
    if (!game.bet_gems || typeof game.bet_gems !== 'object') return [];
    
    return gemDefinitions
      .filter(gem => game.bet_gems[gem.name] > 0)
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
    <div className={`${cardBackground} border border-border-primary rounded-lg p-4 hover:border-accent-primary transition-all duration-300 flex-shrink-0`}>
      {/* Top row: Avatar, Username, Time */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          {/* Avatar */}
          <div className="w-10 h-10 rounded-full bg-surface-sidebar flex items-center justify-center overflow-hidden">
            <img 
              src={game.creator?.gender === 'female' ? '/Women.svg' : '/Men.svg'} 
              alt="Avatar" 
              className="w-8 h-8"
            />
          </div>
          
          {/* Username */}
          <div>
            <h3 className="font-rajdhani font-bold text-white text-lg">
              {formatUsername(game.creator?.username || game.creator_username)}
            </h3>
            {isMyBet && (
              <span className="px-2 py-1 bg-green-600 text-white text-xs rounded-full font-rajdhani font-bold">
                Моя ставка
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
              автоотмена
            </div>
          </div>
        )}
      </div>

      {/* Gems row */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          {sortedGems.map((gem) => (
            <div key={gem.name} className="flex items-center space-x-1">
              <img 
                src={gem.icon} 
                alt={gem.name} 
                className="w-4 h-4"
              />
              <span className="text-white font-rajdhani text-sm font-bold">
                {gem.quantity}
              </span>
            </div>
          ))}
          {sortedGems.length === 0 && (
            <span className="text-text-secondary text-sm font-roboto">
              Нет гемов
            </span>
          )}
        </div>
        
        {/* Total bet amount */}
        <div className="text-right">
          <div className="text-accent-primary font-rajdhani font-bold text-xl">
            ${totalBet.toFixed(2)}
          </div>
          <div className="text-text-secondary text-xs">
            общая ставка
          </div>
        </div>
      </div>

      {/* Action button */}
      <div className="flex justify-end">
        {isOngoing ? (
          <div className="px-4 py-2 bg-blue-600 text-white font-rajdhani font-bold rounded-lg text-sm">
            В процессе
          </div>
        ) : isMyBet ? (
          <button
            onClick={() => onCancel && onCancel(game.id)}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-rajdhani font-bold rounded-lg transition-colors text-sm"
          >
            Отменить
          </button>
        ) : (
          <button
            onClick={() => onAccept && onAccept(game.id)}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-rajdhani font-bold rounded-lg transition-colors text-sm"
          >
            Принять
          </button>
        )}
      </div>
    </div>
  );
};

export default PlayerCard;