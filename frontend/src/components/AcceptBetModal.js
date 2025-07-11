import React, { useState, useEffect } from 'react';
import { useGems } from './GemsContext';
import { useNotifications } from './NotificationContext';

// Safe wrapper for formatCurrencyWithSymbol
const safeFormatCurrency = (amount) => {
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

const AcceptBetModal = ({ bet, user, onClose, onUpdateUser }) => {
  // MUST call hooks first - before any conditional logic or early returns
  const { 
    gemsData = [], 
    validateGemOperation = () => ({ valid: true }), 
    refreshInventory = () => {} 
  } = useGems() || {};
  const { 
    showSuccess = () => {}, 
    showError = () => {} 
  } = useNotifications() || {};

  // Now we can safely do early returns after all hooks are called
  if (!bet || !user || !onClose) {
    console.error('AcceptBetModal: Missing required props', { bet, user, onClose });
    return null;
  }
  
  // Modal state
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Step 1: Funds check & gem selection
  const [selectedGems, setSelectedGems] = useState({});
  const [totalGemValue, setTotalGemValue] = useState(0);
  
  // Step 2: Move selection
  const [selectedMove, setSelectedMove] = useState('');
  
  // Step 3: Match result
  const [matchResult, setMatchResult] = useState(null);
  const [countdown, setCountdown] = useState(3);
  const [showResult, setShowResult] = useState(false);
  
  // Constants
  const COMMISSION_RATE = 0.06; // 6%
  const targetAmount = bet?.bet_amount || 0;
  const commissionAmount = targetAmount * COMMISSION_RATE;
  
  const moves = [
    { id: 'rock', name: 'Rock', icon: '/Rock.svg' },
    { id: 'paper', name: 'Paper', icon: '/Paper.svg' },
    { id: 'scissors', name: 'Scissors', icon: '/Scissors.svg' }
  ];

  const steps = [
    { id: 1, name: 'Gems', description: 'Select your gems' },
    { id: 2, name: 'Move', description: 'Choose your move' },
    { id: 3, name: 'Match', description: 'Battle result' }
  ];

  // Calculate total value of selected gems
  useEffect(() => {
    if (!gemsData || !Array.isArray(gemsData)) return;
    
    const total = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
      const gem = gemsData.find(g => g.type === gemType);
      return sum + (gem ? gem.price * quantity : 0);
    }, 0);
    setTotalGemValue(total);
  }, [selectedGems, gemsData]);

  // Remove auto-fill on component load - user should manually select gems

  const handleGemQuantityChange = (gemType, quantity) => {
    if (!gemsData || !Array.isArray(gemsData)) return;
    
    const gem = gemsData.find(g => g.type === gemType);
    if (!gem) return;
    
    const maxQuantity = gem.available_quantity;
    const validQuantity = Math.max(0, Math.min(maxQuantity, quantity));
    
    setSelectedGems(prev => {
      if (validQuantity <= 0) {
        const newGems = { ...prev };
        delete newGems[gemType];
        return newGems;
      }
      return { ...prev, [gemType]: validQuantity };
    });
  };

  const validateStep1 = () => {
    try {
      // Check if user has enough balance for commission
      const availableBalance = (user?.virtual_balance || 0) - (user?.frozen_balance || 0);
      
      if (availableBalance < commissionAmount) {
        showError(`Недостаточно средств для комиссии. Требуется: $${commissionAmount.toFixed(2)}, доступно: $${availableBalance.toFixed(2)}`);
        return false;
      }

      if (Object.keys(selectedGems).length === 0) {
        showError('Пожалуйста, выберите гемы для ставки');
        return false;
      }

      // Check if selected gems total matches bet amount exactly
      if (Math.abs(totalGemValue - targetAmount) > 0.01) {
        showError(`Сумма выбранных гемов ($${totalGemValue.toFixed(2)}) должна точно соответствовать ставке ($${targetAmount.toFixed(2)})`);
        return false;
      }

      // Validate against Inventory
      const validation = validateGemOperation(selectedGems);
      if (!validation.valid) {
        showError(validation.error);
        return false;
      }

      return true;
    } catch (error) {
      console.error('Error in validateStep1:', error);
      showError('Ошибка валидации данных');
      return false;
    }
  };

  const validateStep2 = () => {
    if (!selectedMove) {
      showError('Пожалуйста, выберите свой ход');
      return false;
    }
    return true;
  };

  const handleNext = () => {
    let isValid = false;
    
    switch (currentStep) {
      case 1:
        isValid = validateStep1();
        break;
      case 2:
        isValid = validateStep2();
        if (isValid) {
          // Start match
          startMatch();
        }
        break;
    }
    
    if (isValid && currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const startMatch = async () => {
    setCurrentStep(3);
    setLoading(true);
    
    // Start countdown
    let count = 3;
    setCountdown(count);
    
    const countdownInterval = setInterval(() => {
      count--;
      setCountdown(count);
      
      if (count <= 0) {
        clearInterval(countdownInterval);
        // Join the game
        joinGame();
      }
    }, 1000);
  };

  const joinGame = async () => {
    try {
      // Call the backend API to join the game
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/games/${bet.id}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          move: selectedMove
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка при присоединении к игре');
      }
      
      const result = await response.json();
      
      // Display match result
      setMatchResult({
        playerMove: selectedMove,
        opponentMove: result.creator_move,
        result: result.winner_id === user.id ? 'win' : (result.winner_id ? 'lose' : 'draw'),
        playerGems: selectedGems,
        opponentGems: bet.bet_gems || {},
        commission: commissionAmount,
        totalBet: targetAmount,
        gameResult: result
      });
      
      setShowResult(true);
      
      // Refresh user data and inventory
      await refreshInventory();
      if (onUpdateUser) {
        onUpdateUser();
      }
      
      // Show success notification
      const resultText = result.winner_id === user.id ? 'Победа!' : (result.winner_id ? 'Поражение!' : 'Ничья!');
      showSuccess(`Игра завершена! ${resultText}`);
      
      // Auto-close after 30 seconds
      setTimeout(() => {
        onClose();
      }, 30000);
      
    } catch (error) {
      console.error('Error joining game:', error);
      showError(error.message || 'Ошибка при присоединении к игре');
      setCurrentStep(2); // Go back to move selection
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-white font-rajdhani text-xl mb-2">Match Opponent's Bet</h3>
        <div className="text-green-400 font-rajdhani text-2xl font-bold">
          Target: {safeFormatCurrency(targetAmount)}
        </div>
        <div className="text-blue-400 font-rajdhani text-lg">
          Your Bet: {safeFormatCurrency(totalGemValue)}
        </div>
        <div className="text-orange-400 font-rajdhani text-sm">
          Commission: {safeFormatCurrency(commissionAmount)}
        </div>
        {Math.abs(totalGemValue - targetAmount) > 0.01 && (
          <div className="text-red-400 text-sm mt-1">
            ⚠️ Amount mismatch: {safeFormatCurrency(Math.abs(totalGemValue - targetAmount))}
          </div>
        )}
      </div>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-white font-rajdhani text-lg">Gem Selection</h4>
          <div className="text-sm text-text-secondary">
            Select gems manually to match the bet amount
          </div>
        </div>

        {/* Selected Gems Display */}
        <div className="bg-surface-sidebar rounded-lg p-4">
          <h5 className="text-white font-rajdhani font-bold mb-2">Selected Gems</h5>
          {Object.keys(selectedGems).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(selectedGems).map(([gemType, quantity]) => {
                if (!gemsData || !Array.isArray(gemsData)) return null;
                
                const gem = gemsData.find(g => g.type === gemType);
                if (!gem) return null;
                
                return (
                  <div key={gemType} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <img src={gem.icon} alt={gem.name} className="w-6 h-6" />
                      <span className="text-white font-rajdhani">{gem.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-rajdhani font-bold">{quantity}x</div>
                      <div className="text-text-secondary text-sm">{safeFormatCurrency(gem.price * quantity)}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-text-secondary text-center py-4">
              No gems selected
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 max-h-64 overflow-y-auto">
          {gemsData && Array.isArray(gemsData) ? gemsData.map(gem => {
            const available = gem.available_quantity;
            const selected = selectedGems[gem.type] || 0;
            
            if (!gem.has_available && selected <= 0) return null;
            
            return (
              <div key={gem.type} className="bg-surface-card rounded-lg p-3 border border-opacity-20" style={{ borderColor: gem.color }}>
                <div className="flex items-center space-x-2 mb-2">
                  <img src={gem.icon} alt={gem.name} className="w-6 h-6" />
                  <div>
                    <div className="text-white font-rajdhani font-bold text-sm">{gem.name}</div>
                    <div className="text-text-secondary text-xs">{safeFormatCurrency(gem.price)}</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleGemQuantityChange(gem.type, Math.max(0, selected - 1))}
                    disabled={selected <= 0}
                    className="w-8 h-8 bg-red-600 text-white rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:scale-110 transition-all"
                  >
                    −
                  </button>
                  
                  <div className="flex-1 text-center">
                    <div className="text-white font-rajdhani font-bold">{selected}</div>
                    <div className="text-text-secondary text-xs">of {available}</div>
                  </div>
                  
                  <button
                    onClick={() => handleGemQuantityChange(gem.type, selected + 1)}
                    disabled={selected >= available}
                    className="w-8 h-8 bg-green-600 text-white rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:scale-110 transition-all"
                  >
                    +
                  </button>
                </div>
              </div>
            );
          }) : (
            <div className="col-span-2 text-center text-text-secondary py-4">
              Loading gems...
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-white font-rajdhani text-xl mb-2">Choose Your Move</h3>
        <p className="text-text-secondary">Select your strategy for the battle</p>
        <div className="text-green-400 font-rajdhani text-lg mt-2">
          Betting: {safeFormatCurrency(totalGemValue)}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {moves.map(move => (
          <button
            key={move.id}
            onClick={() => setSelectedMove(move.id)}
            className={`p-6 rounded-lg border-2 transition-all duration-300 hover:scale-105 ${
              selectedMove === move.id
                ? 'border-accent-primary bg-accent-primary bg-opacity-20'
                : 'border-surface-sidebar hover:border-accent-primary border-opacity-50'
            }`}
          >
            <img src={move.icon} alt={move.name} className="w-16 h-16 mx-auto mb-3" />
            <div className="text-white font-rajdhani font-bold text-lg">{move.name}</div>
          </button>
        ))}
      </div>
    </div>
  );

  const renderStep3 = () => {
    if (!showResult) {
      return (
        <div className="space-y-6 text-center">
          <h3 className="text-white font-rajdhani text-xl mb-4">Starting Match</h3>
          
          <div className="text-6xl font-bold text-accent-primary">
            {countdown}
          </div>
          
          <div className="text-text-secondary">
            Get ready for battle...
          </div>
          
          {loading && (
            <div className="flex items-center justify-center space-x-2 mt-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent-primary"></div>
              <span className="text-text-secondary">Joining game...</span>
            </div>
          )}
        </div>
      );
    }

    const { result, playerMove, opponentMove, commission, gameResult } = matchResult;
    
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h3 className={`text-3xl font-russo mb-4 ${
            result === 'win' ? 'text-green-400' : 
            result === 'lose' ? 'text-red-400' : 'text-yellow-400'
          }`}>
            {result === 'win' ? 'VICTORY!' : 
             result === 'lose' ? 'DEFEAT!' : 'DRAW!'}
          </h3>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Your Move */}
          <div className="text-center">
            <div className="text-white font-rajdhani font-bold mb-2">Your Move</div>
            <img 
              src={moves.find(m => m.id === playerMove)?.icon} 
              alt={playerMove} 
              className="w-20 h-20 mx-auto mb-2" 
            />
            <div className="text-accent-primary font-rajdhani capitalize">{playerMove}</div>
          </div>

          {/* Opponent Move */}
          <div className="text-center">
            <div className="text-white font-rajdhani font-bold mb-2">Opponent Move</div>
            <img 
              src={moves.find(m => m.id === opponentMove)?.icon} 
              alt={opponentMove} 
              className="w-20 h-20 mx-auto mb-2" 
            />
            <div className="text-accent-primary font-rajdhani capitalize">{opponentMove}</div>
          </div>
        </div>

        <div className="bg-surface-sidebar rounded-lg p-4 space-y-3">
          <div className="flex justify-between">
            <span className="text-text-secondary">Bet Amount:</span>
            <span className="text-white font-rajdhani font-bold">{safeFormatCurrency(totalGemValue)}</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-text-secondary">Commission:</span>
            <span className="text-orange-400 font-rajdhani font-bold">
              {safeFormatCurrency(commission)}
            </span>
          </div>
          
          <div className="border-t border-border-primary pt-3">
            <div className="flex justify-between">
              <span className="text-text-secondary">Result:</span>
              <span className={`font-rajdhani font-bold ${
                result === 'win' ? 'text-green-400' : 
                result === 'lose' ? 'text-red-400' : 'text-yellow-400'
              }`}>
                {result === 'win' ? 'You Win!' : 
                 result === 'lose' ? 'You Lose!' : 'Draw!'}
              </span>
            </div>
          </div>
          
          {gameResult && (
            <div className="text-xs text-text-secondary">
              Game ID: {gameResult.id}
            </div>
          )}
        </div>

        <div className="text-center text-text-secondary text-sm">
          This window will close automatically in 30 seconds
        </div>
      </div>
    );
  };

  // Wrap entire component in error boundary
  try {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border-primary">
            <h2 className="text-white font-russo text-xl">Join Battle</h2>
            <button
              onClick={onClose}
              className="text-text-secondary hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Progress Steps */}
          <div className="p-4 border-b border-border-primary">
            <div className="flex items-center space-x-2">
              {steps.map((step, index) => (
                <React.Fragment key={step.id}>
                  <div className={`flex-1 flex items-center space-x-2 ${
                    currentStep >= step.id ? 'text-accent-primary' : 'text-text-secondary'
                  }`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      currentStep >= step.id ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary'
                    }`}>
                      {step.id}
                    </div>
                    <span className="text-xs font-rajdhani hidden sm:block">{step.name}</span>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`w-8 h-0.5 ${
                      currentStep > step.id ? 'bg-accent-primary' : 'bg-surface-sidebar'
                    }`} />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="p-4 overflow-y-auto max-h-96">
            {currentStep === 1 && renderStep1()}
            {currentStep === 2 && renderStep2()}
            {currentStep === 3 && renderStep3()}
          </div>

          {/* Footer */}
          {currentStep < 3 && (
            <div className="p-4 border-t border-border-primary">
              <div className="flex space-x-3">
                {currentStep > 1 && (
                  <button
                    onClick={handleBack}
                    disabled={loading}
                    className="px-4 py-2 bg-surface-sidebar text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300 disabled:opacity-50"
                  >
                    Back
                  </button>
                )}
                
                <button
                  onClick={handleNext}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300 disabled:opacity-50"
                >
                  {currentStep === 2 ? 'Start Battle!' : 'Next'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  } catch (error) {
    console.error('AcceptBetModal render error:', error);
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-surface-card border border-border-primary rounded-lg w-full max-w-md p-6">
          <h2 className="text-xl font-russo text-white mb-4">Error</h2>
          <p className="text-text-secondary mb-4">
            An error occurred while loading the battle interface. Please try again.
          </p>
          <button
            onClick={onClose}
            className="w-full py-2 bg-red-600 text-white font-rajdhani font-bold rounded-lg hover:bg-red-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    );
  }
};

export default AcceptBetModal;