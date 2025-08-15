import React, { useState, useEffect } from 'react';
import { useGems } from './GemsContext';
import { useNotifications } from './NotificationContext';
import { formatCurrencyWithSymbol, formatDollarAmount } from '../utils/economy';
import { formatDollarsAsGems } from '../utils/gemUtils';
import { calculateGemCombination } from '../utils/gemCombinationAlgorithms';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';

const CreateBetModal = ({ user, onClose, onUpdateUser }) => {
  const { 
    gemsData, 
    validateGemOperation, 
    refreshInventory
  } = useGems();
  const { showSuccess, showError } = useNotifications();
  
  // Modal state
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Unified Gem Selection
  const [betAmount, setBetAmount] = useState('');
  const [selectedGems, setSelectedGems] = useState({});
  const [totalGemValue, setTotalGemValue] = useState(0);
  
  // Step 2: Move selection
  const [selectedMove, setSelectedMove] = useState('');
  
  // Защита от многократных нажатий для кнопок стратегий
  const [lastClickedStrategy, setLastClickedStrategy] = useState(null);
  const [strategyButtonsDisabled, setStrategyButtonsDisabled] = useState({
    small: false,
    smart: false,
    big: false
  });
  
  // Защита от многократных нажатий для критических кнопок
  const [isCreatingBet, setIsCreatingBet] = useState(false);
  const [isNavigating, setIsNavigating] = useState(false);
  
  // Constants
  const MIN_BET = 1;
  const MAX_BET = 3000;
  const COMMISSION_RATE = 0.03; // 3%
  
  const moves = [
    { id: 'rock', name: 'Rock', icon: '/Rock.svg' },
    { id: 'paper', name: 'Paper', icon: '/Paper.svg' },
    { id: 'scissors', name: 'Scissors', icon: '/Scissors.svg' }
  ];

  const steps = [
  ];

  // Calculate total value when selectedGems changes
  useEffect(() => {
    const total = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
      const gem = gemsData.find(g => g.type === gemType);
      return sum + (gem ? gem.price * quantity : 0);
    }, 0);
    setTotalGemValue(total);
  }, [selectedGems, gemsData]);

  const handleAmountChange = (value) => {
    setBetAmount(value);
  };

  /**
   * Enhanced strategy handler with improved error handling
   */
  const handleStrategySelect = (strategy) => {
    // Проверка на блокировку кнопки
    if (strategyButtonsDisabled[strategy]) {
      return; // Кнопка заблокирована, игнорируем клик
    }
    
    if (!betAmount || parseFloat(betAmount) <= 0) {
      showError('Please enter a valid bet amount first');
      return;
    }
    
    const amount = parseFloat(betAmount);
    
    // Validate amount range
    if (amount < MIN_BET) {
      showError(`Minimum bet amount is $${MIN_BET}`);
      return;
    }
    
    if (amount > MAX_BET) {
      showError(`Maximum bet amount is $${MAX_BET}`);
      return;
    }
    
    setLoading(true);
    
    // Блокируем текущую кнопку и разблокируем остальные
    setStrategyButtonsDisabled({
      small: strategy === 'small',
      smart: strategy === 'smart',
      big: strategy === 'big'
    });
    setLastClickedStrategy(strategy);
    
    try {
      console.log(`Attempting ${strategy} strategy for $${amount} with gems:`, gemsData.map(g => `${g.name}: ${g.available_quantity}`));
      
      // Use enhanced frontend algorithms
      const result = calculateGemCombination(strategy, gemsData, amount);
      
      if (result.success) {
        // Convert result to internal format
        const autoSelected = {};
        result.combination.forEach(item => {
          autoSelected[item.type] = item.quantity;
        });
        
        // Final validation before setting
        const totalValue = result.combination.reduce((sum, item) => sum + item.totalValue, 0);
        if (Math.abs(totalValue - amount) > 0.01) {
          throw new Error(`Amount mismatch: expected $${amount}, got $${totalValue}`);
        }
        
        setSelectedGems(autoSelected);
        showSuccess(result.message);
        console.log(`${strategy} strategy successful:`, autoSelected);
      } else {
        showError(result.message);
        console.error(`${strategy} strategy failed:`, result.message);
      }
    } catch (error) {
      console.error('Error calculating gem combination:', error);
      const errorMsg = error.message.includes('available in inventory') 
        ? error.message 
        : 'Error calculating gem combination. Please try manually selecting gems.';
      showError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleGemQuantityChange = (gemType, quantity) => {
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
    const amount = parseFloat(betAmount);
    if (isNaN(amount) || amount < MIN_BET || amount > MAX_BET) {
      showError(`Bet amount must be between $${MIN_BET} and $${MAX_BET}`);
      return false;
    }

    if (Object.keys(selectedGems).length === 0) {
      showError('Please select at least one gem');
      return false;
    }

    // CRITICAL: Check if selected gems total matches bet amount exactly
    if (Math.abs(totalGemValue - amount) > 0.01) {
      showError(`Selected gems total ($${totalGemValue}) must match bet amount ($${amount}). Use auto-combination buttons or adjust manually.`);
      return false;
    }

    // Validate against Inventory
    const validation = validateGemOperation(selectedGems);
    if (!validation.valid) {
      showError(validation.error);
      return false;
    }

    // Check commission against total virtual balance
    const commission = totalGemValue * COMMISSION_RATE;
    const totalBalance = user?.virtual_balance || 0;
    const frozenBalance = user?.frozen_balance || 0;
    const availableForSpending = totalBalance - frozenBalance;
    
    if (availableForSpending < commission) {
      showError(`Insufficient balance for commission. Required: ${formatDollarAmount(commission)}, Available: ${formatDollarAmount(availableForSpending)}`);
      return false;
    }

    return true;
  };

  const validateStep2 = () => {
    if (!selectedMove) {
      showError('Please select your move');
      return false;
    }
    return true;
  };

  const handleNext = () => {
    if (isNavigating) return; // Защита от повторных нажатий
    
    let isValid = false;
    
    switch (currentStep) {
      case 1:
        isValid = validateStep1();
        break;
      case 2:
        isValid = validateStep2();
        break;
    }
    
    if (isValid) {
      setIsNavigating(true);
      setCurrentStep(Math.min(2, currentStep + 1));
      // Сбрасываем флаг через небольшую задержку
      setTimeout(() => setIsNavigating(false), 300);
    }
  };

  const handleBack = () => {
    if (isNavigating) return; // Защита от повторных нажатий
    
    if (currentStep > 1) {
      setIsNavigating(true);
      setCurrentStep(currentStep - 1);
      // Сбрасываем флаг через небольшую задержку
      setTimeout(() => setIsNavigating(false), 300);
    }
  };

  const handleCreateBet = async () => {
    if (isCreatingBet) return; // Защита от повторных нажатий
    
    if (!validateStep2()) return;
    
    setLoading(true);
    setIsCreatingBet(true);
    
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/games/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          move: selectedMove,
          bet_gems: selectedGems
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        showSuccess(`Bet created! ${formatDollarAmount(totalGemValue * COMMISSION_RATE)} (3%) frozen until game completion.`);
        await refreshInventory();
        onUpdateUser?.();
        
        const globalRefresh = getGlobalLobbyRefresh();
        globalRefresh.triggerLobbyRefresh();
        console.log('🎮 Bet created - triggering lobby refresh');
        
        onClose();
      } else {
        showError(data.detail || 'Failed to create bet');
        setIsCreatingBet(false); // Сбрасываем флаг при ошибке
      }
    } catch (error) {
      showError('Network error. Please try again.');
      setIsCreatingBet(false); // Сбрасываем флаг при ошибке
    } finally {
      setLoading(false);
      // Не сбрасываем isCreatingBet после успеха, т.к. модалка закрывается
    }
  };

  // Render Selected Gems inline
  const renderSelectedGems = () => {
    const sortedSelectedGems = Object.entries(selectedGems)
      .map(([gemType, quantity]) => {
        const gem = gemsData.find(g => g.type === gemType);
        return gem ? { ...gem, quantity } : null;
      })
      .filter(Boolean)
      .sort((a, b) => a.price - b.price); // Sort by price ascending

    if (sortedSelectedGems.length === 0) {
      return (
        <div className="text-text-secondary text-sm text-center py-4">
          No gems selected. Choose amount and strategy above.
        </div>
      );
    }

    return (
      <div className="flex flex-wrap gap-2">
        {sortedSelectedGems.map((gem) => {
          const gemTotal = gem.quantity * gem.price;
          return (
            <div key={gem.type} className="flex items-center space-x-1 bg-surface-sidebar rounded-lg px-3 py-2 border border-opacity-30" style={{ borderColor: gem.color }}>
              <img src={gem.icon} alt={gem.name} className="w-5 h-5" />
              <span className="text-text-secondary text-xs font-rajdhani">x{gem.quantity}</span>
              <span className="text-green-400 text-xs font-rajdhani font-bold">= {formatDollarsAsGems(gemTotal)}</span>
            </div>
          );
        })}
      </div>
    );
  };

  const renderStep1 = () => (
    <div className="space-y-4">
      {/* Fixed Bet Amount at Top */}
      <div className="sticky top-0 bg-surface-card border-b border-border-primary p-4 -mx-4 mb-0 z-10">
        <label className="block text-white font-rajdhani text-lg mb-3">
          Bet Amount
        </label>
        <div className="relative">
          <input
            type="number" 
            value={betAmount}
            onChange={(e) => handleAmountChange(e.target.value)}
            placeholder="Enter amount..."
            min={MIN_BET}
            max={MAX_BET}
            className="placeholder:text-xl w-full px-4 py-2 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-white text-3xl font-rajdhani font-bold text-center focus:outline-none focus:border-accent-primary"
          />
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-green-400 text-xl font-bold">
             <img src="/gems/gem-green.svg" alt="Gem" width="20" height="20" style={{ verticalAlign: 'middle' }} />
          </div>
        </div>
        <div className="flex justify-between text-text-secondary text-sm mt-2">
          <span>Min: {MIN_BET} </span>
          <span>Max: {MAX_BET}</span>
        </div>
      </div>

      {/* Strategy Buttons - NEW IMPLEMENTATION */}
      <div>
        <label className="block text-white font-rajdhani text-lg mb-3">
          Auto Combination
        </label>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => handleStrategySelect('small')}
            disabled={!betAmount || parseFloat(betAmount) <= 0 || loading || strategyButtonsDisabled.small}
            className={`px-4 py-3 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center ${
              strategyButtonsDisabled.small 
                ? 'bg-gray-600' 
                : 'bg-red-600 hover:bg-red-700 hover:scale-105'
            }`}
            title="🔴 Use more cheap gems (Ruby, Amber, Topaz)"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              '🔴 Small'
            )}
          </button>
          <button
            onClick={() => handleStrategySelect('smart')}
            disabled={!betAmount || parseFloat(betAmount) <= 0 || loading || strategyButtonsDisabled.smart}
            className={`px-4 py-3 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center ${
              strategyButtonsDisabled.smart 
                ? 'bg-gray-600' 
                : 'bg-green-600 hover:bg-green-700 hover:scale-105'
            }`}
            title="🟢 Balanced mid-range gems (60% mid, 30% low, 10% high)"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              '🟢 Smart'
            )}
          </button>
          <button
            onClick={() => handleStrategySelect('big')}
            disabled={!betAmount || parseFloat(betAmount) <= 0 || loading || strategyButtonsDisabled.big}
            className={`px-4 py-3 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center ${
              strategyButtonsDisabled.big 
                ? 'bg-gray-600' 
                : 'bg-purple-600 hover:bg-purple-700 hover:scale-105'
            }`}
            title="🟣 Use fewer expensive gems (Magic, Sapphire, Aquamarine)"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              '🟣 Big'
            )}
          </button>
        </div>
      </div>

      {/* Selected Gems Display */}
      <div>
        <div className="flex justify-between items-center mb-3">
          <label className="text-white font-rajdhani text-lg">Selected Gems</label>
          <div className={`font-rajdhani text-xl font-bold ${
            betAmount && Math.abs(totalGemValue - parseFloat(betAmount)) < 0.01 
              ? 'text-green-400' 
              : totalGemValue > 0 
                ? 'text-orange-400' 
                : 'text-text-secondary'
          }`}>
            {formatDollarsAsGems(totalGemValue)}
            {betAmount && parseFloat(betAmount) > 0 && (
              <span className="text-text-secondary text-sm ml-2">
                / {(parseFloat(betAmount))}
              </span>
            )}
          </div>
        </div>
        <div className="bg-surface-sidebar rounded-lg p-4 min-h-16 border border-border-primary">
          {renderSelectedGems()}
        </div>
        
        {/* Show difference warning if amounts don't match */}
        {betAmount && parseFloat(betAmount) > 0 && Math.abs(totalGemValue - parseFloat(betAmount)) > 0.01 && (
          <div className="mt-2 text-orange-400 text-sm font-rajdhani">
            ⚠️ Selected gems total (${totalGemValue}) doesn't match bet amount (${parseFloat(betAmount)}). 
            Use auto-combination buttons or adjust manually.
          </div>
        )}
      </div>

      {/* Mini Inventory for Manual Editing */}
      <div className="pb-4">
        <label className="block text-white font-rajdhani text-lg mb-3">
          Your Inventory
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 max-h-64 overflow-y-auto">
          {gemsData.map(gem => {
            const selected = selectedGems[gem.type] || 0;
            
            if (!gem.has_gems) return null;
            
            return (
              <div key={gem.type} className="bg-surface-card rounded-lg p-3 border border-opacity-20" style={{ borderColor: gem.color }}>
                <div className="text-center mb-2">
                  <img src={gem.icon} alt={gem.name} className="w-14 h-14 mx-auto mb-1" />
                  <div className="text-white font-rajdhani font-bold text-xs">{gem.name}</div>
                  <div className="text-text-secondary text-xs">{formatDollarsAsGems(gem.price)}</div>
                </div>
                
                <div className="flex items-center justify-between space-x-1">
                  <button
                    onClick={() => handleGemQuantityChange(gem.type, selected - 1)}
                    disabled={selected <= 0}
                    className="w-6 h-6 bg-red-600 text-white rounded text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:scale-110 transition-all"
                  >
                    −
                  </button>
                  
                  <div className="text-center flex-1">
                    <div className="text-white font-rajdhani font-bold text-sm">{selected}</div>
                    <div className="text-text-secondary text-xs">/{gem.available_quantity}</div>
                  </div>
                  
                  <button
                    onClick={() => handleGemQuantityChange(gem.type, selected + 1)}
                    disabled={selected >= gem.available_quantity}
                    className="w-6 h-6 bg-green-600 text-white rounded text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:scale-110 transition-all"
                  >
                    +
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-white font-rajdhani text-xl mb-2">Choose Your Move</h3>
        <div className="text-green-400 font-rajdhani text-6xl mt-2 font-bold">
          {(totalGemValue)}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
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
            <img src={move.icon} alt={move.name} className="w-24 h-24 mx-auto mb-10" />
            <div className="text-white font-rajdhani font-bold text-lg">{move.name}</div>
          </button>
        ))}
      </div>
    </div>
  );



  // Prevent body scroll while modal open (and avoid layout jumps)
  useEffect(() => {
    const { body } = document;
    const prevOverflow = body.style.overflow;
    const prevPaddingRight = body.style.paddingRight;
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
    if (scrollbarWidth > 0) {
      body.style.paddingRight = `${scrollbarWidth}px`;
    }
    body.style.overflow = 'hidden';
    return () => { 
      body.style.overflow = prevOverflow; 
      body.style.paddingRight = prevPaddingRight; 
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4" onWheel={(e)=>e.stopPropagation()} onTouchMove={(e)=>e.stopPropagation()}>
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg w-full max-w-lg max-h-[90vh] overflow-hidden" role="dialog" aria-modal="true">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-primary">
          <h2 className="text-white font-russo text-xl">Create Bet</h2>
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
        <div className="">
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
        <div className="px-4 overflow-y-auto max-h-96">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && <div className="py-4">{renderStep2()}</div>}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border-primary">
          <div className="flex space-x-3">
            {currentStep > 1 && (
              <button
                onClick={handleBack}
                disabled={loading || isNavigating}
                className={`px-4 py-2 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 ${
                  isNavigating 
                    ? 'bg-gray-600 cursor-not-allowed' 
                    : 'bg-surface-sidebar hover:scale-105'
                }`}
              >
                Back
              </button>
            )}
            
            {currentStep === 1 && (
              <button
                onClick={handleNext}
                disabled={loading || isNavigating}
                className={`flex-1 px-4 py-4 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 ${
                  isNavigating 
                    ? 'bg-gray-600 cursor-not-allowed' 
                    : 'bg-gradient-accent hover:scale-105'
                }`}
              >
                Next
              </button>
            )}
            {currentStep === 2 && (
              <button
                onClick={handleCreateBet}
                disabled={loading || isCreatingBet}
                className={`flex-1 px-4 py-4 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 ${
                  isCreatingBet 
                    ? 'bg-gray-600 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-green-600 to-green-700 hover:scale-105'
                }`}
              >
                {loading || isCreatingBet ? 'Creating...' : 'Create Bet'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateBetModal;