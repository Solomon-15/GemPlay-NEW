import React from 'react';
import { formatGemValue, formatDollarAmount } from '../utils/economy';

const BattleResultStep = ({
  battleResult,
  selectedMove,
  targetAmount,
  totalGemValue,
  commissionAmount,
  playerData, // Новый пропс для данных игроков
  onClose
}) => {
  const [timeUntilAutoClose, setTimeUntilAutoClose] = React.useState(30);

  // Автозакрытие через 7 секунд
  React.useEffect(() => {
    const timer = setInterval(() => {
      setTimeUntilAutoClose(prev => {
        if (prev <= 1) {
          onClose();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [onClose]);

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
      {/* Result Header с увеличенным размером */}
      <div className="text-center py-4">
        <h3 className={`text-5xl font-russo mb-6 ${resultConfig.color} animate-pulse`}>
          {resultConfig.title}
        </h3>
        
        {/* Auto-close timer */}
        <div className="text-text-secondary text-sm">
          Auto-closing in {timeUntilAutoClose} seconds
        </div>
      </div>

      {/* Players Battle Section с аватарами */}
      <div className={`${resultConfig.bgColor} bg-opacity-10 border-2 ${resultConfig.borderColor} rounded-xl p-6`}>
        <div className="grid grid-cols-3 gap-4 items-center">
          
          {/* Player (You) */}
          <div className="text-center">
            <div className={`w-20 h-20 mx-auto mb-3 rounded-full border-4 ${
              result === 'win' ? 'border-green-400' : result === 'lose' ? 'border-red-400' : 'border-yellow-400'
            } bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center`}>
              <span className="text-white font-russo text-xl">
                {playerData?.player?.username?.charAt(0)?.toUpperCase() || 'Y'}
              </span>
            </div>
            <div className="text-white font-rajdhani font-bold text-lg mb-2">
              {playerData?.player?.username || 'You'}
            </div>
            <div className={`text-sm font-bold ${
              result === 'win' ? 'text-green-400' : result === 'lose' ? 'text-red-400' : 'text-yellow-400'
            }`}>
              {result === 'win' ? 'WINNER' : result === 'lose' ? 'LOSER' : 'DRAW'}
            </div>
            
            {/* Your Move */}
            <div className="mt-4">
              <img 
                src={moves.find(m => m.id === selectedMove)?.icon} 
                alt={selectedMove} 
                className="w-16 h-16 mx-auto mb-2" 
              />
              <div className="text-accent-primary font-rajdhani capitalize font-bold">
                {moves.find(m => m.id === selectedMove)?.name}
              </div>
            </div>
          </div>

          {/* VS Section */}
          <div className="text-center">
            <div className="text-4xl font-russo text-white mb-2">VS</div>
            <div className="text-text-secondary text-sm">Rock Paper Scissors</div>
          </div>

          {/* Opponent */}
          <div className="text-center">
            <div className={`w-20 h-20 mx-auto mb-3 rounded-full border-4 ${
              result === 'lose' ? 'border-green-400' : result === 'win' ? 'border-red-400' : 'border-yellow-400'
            } bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center`}>
              <span className="text-white font-russo text-xl">
                {playerData?.opponent?.username?.charAt(0)?.toUpperCase() || 'O'}
              </span>
            </div>
            <div className="text-white font-rajdhani font-bold text-lg mb-2">
              {playerData?.opponent?.username || 'Opponent'}
            </div>
            <div className={`text-sm font-bold ${
              result === 'lose' ? 'text-green-400' : result === 'win' ? 'text-red-400' : 'text-yellow-400'
            }`}>
              {result === 'lose' ? 'WINNER' : result === 'win' ? 'LOSER' : 'DRAW'}
            </div>
            
            {/* Opponent Move */}
            <div className="mt-4">
              <img 
                src={moves.find(m => m.id === opponentMove)?.icon} 
                alt={opponentMove} 
                className="w-16 h-16 mx-auto mb-2" 
              />
              <div className="text-accent-primary font-rajdhani capitalize font-bold">
                {moves.find(m => m.id === opponentMove)?.name}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Financial Summary - улучшенный дизайн */}
      <div className="bg-surface-sidebar rounded-xl p-6 border border-border-primary">
        <h5 className="text-white font-rajdhani font-bold text-xl mb-4 text-center">💰 Battle Summary</h5>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-border-primary border-opacity-30">
            <span className="text-text-secondary font-rajdhani">Total Bet Amount:</span>
            <span className="text-white font-rajdhani font-bold text-lg">{formatGemValue(totalGemValue)}</span>
          </div>
          
          {commissionAmount > 0 && (
            <div className="flex justify-between items-center py-2 border-b border-border-primary border-opacity-30">
              <span className="text-text-secondary font-rajdhani">Platform Commission (6%):</span>
              <span className="text-orange-400 font-rajdhani font-bold">
                -{formatDollarAmount(commissionAmount)}
              </span>
            </div>
          )}
          
          <div className="flex justify-between items-center py-2 border-b border-border-primary border-opacity-30">
            <span className="text-text-secondary font-rajdhani">Prize Pool:</span>
            <span className="text-green-400 font-rajdhani font-bold text-lg">
              {formatGemValue(totalGemValue * 2 - commissionAmount)}
            </span>
          </div>
          
          <div className="pt-3 border-t-2 border-accent-primary border-opacity-30">
            <div className="flex justify-between items-center">
              <span className="text-white font-rajdhani font-bold text-lg">Your Result:</span>
              <span className={`font-rajdhani font-bold text-xl ${resultConfig.color}`}>
                {result === 'win' ? 
                  `+${formatGemValue(totalGemValue * 2 - commissionAmount)}` : 
                 result === 'lose' ? 
                  `-${formatGemValue(totalGemValue)}` : 
                  `±${formatGemValue(0)}`}
              </span>
            </div>
            <div className="text-center mt-2">
              <span className={`text-sm font-rajdhani ${resultConfig.color}`}>
                {result === 'win' ? 'You won all gems!' : 
                 result === 'lose' ? 'You lost your gems!' : 'All gems returned!'}
              </span>
            </div>
          </div>
        </div>
        
        {gameData && (
          <div className="text-xs text-text-secondary text-center mt-4 pt-3 border-t border-border-primary border-opacity-20">
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
          className={`w-full py-4 text-white font-rajdhani font-bold text-lg rounded-xl hover:scale-105 transition-all duration-300 ${
            result === 'win' ? 'bg-gradient-to-r from-green-600 to-green-700' :
            result === 'lose' ? 'bg-gradient-to-r from-red-600 to-red-700' :
            'bg-gradient-to-r from-yellow-600 to-yellow-700'
          }`}
        >
          {result === 'win' ? '🎉 Claim Victory!' : 
           result === 'lose' ? '💔 Accept Defeat' : '🤝 Continue Playing'} (OK)
        </button>
        
        <div className="text-center text-text-secondary text-sm">
          <div className="flex items-center justify-center space-x-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Window closes automatically in {timeUntilAutoClose} seconds</span>
          </div>
          <div className="mt-1">Your balance and gems have been updated automatically</div>
        </div>
      </div>
    </div>
  );
};

export default BattleResultStep;