import React from 'react';

const BattleResultStep = ({
  battleResult,
  selectedMove,
  targetAmount,
  totalGemValue,
  commissionAmount,
  onClose
}) => {
  // Безопасное форматирование валюты
  const formatCurrency = (amount) => {
    try {
      if (typeof amount !== 'number' || isNaN(amount)) {
        return '$0.00';
      }
      return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    } catch (error) {
      console.error('Error formatting currency:', error);
      return '$0.00';
    }
  };

  // Конфигурация ходов
  const moves = [
    { id: 'rock', name: 'Rock', icon: '/Rock.svg' },
    { id: 'paper', name: 'Paper', icon: '/Paper.svg' },
    { id: 'scissors', name: 'Scissors', icon: '/Scissors.svg' }
  ];

  // Получаем данные о результате битвы
  const {
    result = 'draw', // win, lose, draw
    opponentMove = 'rock',
    gameData = null
  } = battleResult || {};

  // Определяем цвета и тексты для результата
  const getResultConfig = () => {
    switch (result) {
      case 'win':
        return {
          title: 'VICTORY!',
          color: 'text-green-400',
          bgColor: 'bg-green-900',
          borderColor: 'border-green-600'
        };
      case 'lose':
        return {
          title: 'DEFEAT!',
          color: 'text-red-400',
          bgColor: 'bg-red-900',
          borderColor: 'border-red-600'
        };
      default:
        return {
          title: 'DRAW!',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-900',
          borderColor: 'border-yellow-600'
        };
    }
  };

  const resultConfig = getResultConfig();

  // Обработчик закрытия с предотвращением всплытия
  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  return (
    <div className="space-y-6">
      {/* Result Header */}
      <div className="text-center">
        <h3 className={`text-3xl font-russo mb-4 ${resultConfig.color}`}>
          {resultConfig.title}
        </h3>
      </div>

      {/* Battle Moves */}
      <div className="grid grid-cols-2 gap-6">
        {/* Your Move */}
        <div className="text-center">
          <div className="text-white font-rajdhani font-bold mb-2">Your Move</div>
          <img 
            src={moves.find(m => m.id === selectedMove)?.icon} 
            alt={selectedMove} 
            className="w-20 h-20 mx-auto mb-2" 
          />
          <div className="text-accent-primary font-rajdhani capitalize font-bold">
            {moves.find(m => m.id === selectedMove)?.name}
          </div>
        </div>

        {/* Opponent Move */}
        <div className="text-center">
          <div className="text-white font-rajdhani font-bold mb-2">Opponent Move</div>
          <img 
            src={moves.find(m => m.id === opponentMove)?.icon} 
            alt={opponentMove} 
            className="w-20 h-20 mx-auto mb-2" 
          />
          <div className="text-accent-primary font-rajdhani capitalize font-bold">
            {moves.find(m => m.id === opponentMove)?.name}
          </div>
        </div>
      </div>

      {/* Battle Summary */}
      <div className="bg-surface-sidebar rounded-lg p-4 space-y-3">
        <h5 className="text-white font-rajdhani font-bold mb-3">Battle Summary</h5>
        
        <div className="flex justify-between">
          <span className="text-text-secondary">Bet Amount:</span>
          <span className="text-white font-rajdhani font-bold">{formatCurrency(totalGemValue)}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-text-secondary">Commission:</span>
          <span className="text-orange-400 font-rajdhani font-bold">
            {formatCurrency(commissionAmount)}
          </span>
        </div>
        
        <div className="border-t border-border-primary pt-3">
          <div className="flex justify-between">
            <span className="text-text-secondary">Result:</span>
            <span className={`font-rajdhani font-bold ${resultConfig.color}`}>
              {result === 'win' ? 'You Win!' : 
               result === 'lose' ? 'You Lose!' : 'Draw!'}
            </span>
          </div>
        </div>
        
        {gameData && (
          <div className="text-xs text-text-secondary">
            Game ID: {gameData.id}
          </div>
        )}
      </div>

      {/* Result Details */}
      <div className={`${resultConfig.bgColor} bg-opacity-20 border ${resultConfig.borderColor} rounded-lg p-4`}>
        <div className={`${resultConfig.color} font-rajdhani font-bold mb-2`}>
          {result === 'win' ? '🎉 Congratulations!' : 
           result === 'lose' ? '💔 Better luck next time!' : '🤝 Fair game!'}
        </div>
        <div className="text-white text-sm">
          {result === 'win' ? 
            'You won the battle and received all the gems!' :
           result === 'lose' ? 
            'You lost the battle. Your gems went to the opponent.' :
            'It\'s a draw! All gems are returned to their original owners.'}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-3">
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            handleClose();
          }}
          className="w-full py-3 bg-gradient-accent text-white font-rajdhani font-bold text-lg rounded-lg hover:scale-105 transition-all duration-300"
        >
          Close & Return to Lobby
        </button>
        
        <div className="text-center text-text-secondary text-sm">
          Your balance and gems have been updated automatically
        </div>
      </div>
    </div>
  );
};

export default BattleResultStep;