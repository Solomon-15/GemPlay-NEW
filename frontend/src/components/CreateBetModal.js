import React, { useState, useEffect } from 'react';
import { useGems } from './GemsContext';
import { useNotifications } from './NotificationContext';
import { formatCurrencyWithSymbol } from '../utils/economy';

const CreateBetModal = ({ user, onClose, onUpdateUser }) => {
  const { 
    gemsData, 
    getAvailableGems, 
    validateGemOperation, 
    refreshInventory,
    getSortedGems
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
  
  // Constants
  const MIN_BET = 1;
  const MAX_BET = 3000;
  const COMMISSION_RATE = 0.06; // 6%
  
  const moves = [
    { id: 'rock', name: 'Rock', icon: '/Rock.svg' },
    { id: 'paper', name: 'Paper', icon: '/Paper.svg' },
    { id: 'scissors', name: 'Scissors', icon: '/Scissors.svg' }
  ];

  const steps = [
    { id: 1, name: 'Gem Selection', description: 'Choose gems and amount' },
    { id: 2, name: 'Move', description: 'Choose your move' },
    { id: 3, name: 'Confirm', description: 'Create bet' }
  ];

  // IMPROVED AUTO-COMBINATION STRATEGIES with exact amount matching
  const autoSelectSmall = (amount) => {
    // Small: Use cheapest gems first (Ruby, Amber, Topaz)
    const cheapGems = getSortedGems('price', 'asc').filter(gem => 
      gem.has_available && ['Ruby', 'Amber', 'Topaz'].includes(gem.type)
    );
    return selectGemsWithExactStrategy(cheapGems, amount, 'small');
  };

  const autoSelectSmart = (amount) => {
    // Smart: Use medium-priced gems (Topaz, Emerald, Aquamarine)
    const mediumGems = getSortedGems('price', 'asc').filter(gem => 
      gem.has_available && ['Topaz', 'Emerald', 'Aquamarine'].includes(gem.type)
    );
    return selectGemsWithExactStrategy(mediumGems, amount, 'smart');
  };

  const autoSelectBig = (amount) => {
    // Big: Use expensive gems first (Magic, Sapphire, Aquamarine)
    const expensiveGems = getSortedGems('price', 'desc').filter(gem => 
      gem.has_available && ['Magic', 'Sapphire', 'Aquamarine'].includes(gem.type)
    );
    return selectGemsWithExactStrategy(expensiveGems, amount, 'big');
  };

  const selectGemsWithExactStrategy = (gems, targetAmount, strategy) => {
    const result = {};
    let remainingAmount = targetAmount;
    
    // First pass: try to get as close as possible with the preferred strategy
    for (const gem of gems) {
      if (remainingAmount <= 0) break;
      
      const maxQuantityForAmount = Math.floor(remainingAmount / gem.price);
      const quantityToUse = Math.min(maxQuantityForAmount, gem.available_quantity);
      
      if (quantityToUse > 0) {
        result[gem.type] = quantityToUse;
        remainingAmount -= quantityToUse * gem.price;
      }
    }
    
    // Second pass: if we still have remaining amount, use any available gems to reach exact amount
    if (remainingAmount > 0) {
      const allAvailableGems = getSortedGems('price', 'asc').filter(gem => gem.has_available);
      
      for (const gem of allAvailableGems) {
        if (remainingAmount <= 0) break;
        
        const currentUsed = result[gem.type] || 0;
        const stillAvailable = gem.available_quantity - currentUsed;
        const maxQuantityForRemaining = Math.floor(remainingAmount / gem.price);
        const quantityToAdd = Math.min(maxQuantityForRemaining, stillAvailable);
        
        if (quantityToAdd > 0) {
          result[gem.type] = (result[gem.type] || 0) + quantityToAdd;
          remainingAmount -= quantityToAdd * gem.price;
        }
      }
    }
    
    // Check if we achieved exact amount
    const actualTotal = Object.entries(result).reduce((sum, [gemType, quantity]) => {
      const gem = gemsData.find(g => g.type === gemType);
      return sum + (gem ? gem.price * quantity : 0);
    }, 0);
    
    if (actualTotal !== targetAmount) {
      // Could not achieve exact amount with available gems
      return { error: 'Insufficient available gems to form the exact bet amount.' };
    }
    
    return result;
  };

  // Calculate total value
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

  const handleStrategySelect = (strategy) => {
    if (!betAmount || parseFloat(betAmount) <= 0) {
      showError('Please enter bet amount first');
      return;
    }
    
    const amount = parseFloat(betAmount);
    let autoSelected = {};
    
    switch (strategy) {
      case 'small':
        autoSelected = autoSelectSmall(amount);
        break;
      case 'smart':
        autoSelected = autoSelectSmart(amount);
        break;
      case 'big':
        autoSelected = autoSelectBig(amount);
        break;
    }
    
    // Check if there was an error (insufficient gems)
    if (autoSelected.error) {
      showError(autoSelected.error);
      return;
    }
    
    setSelectedGems(autoSelected);
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

    // Check commission
    const commission = totalGemValue * COMMISSION_RATE;
    const availableBalance = user?.virtual_balance || 0;
    const frozenBalance = user?.frozen_balance || 0;
    const actualAvailable = availableBalance - frozenBalance;
    
    if (actualAvailable < commission) {
      showError(`Insufficient balance for commission. Required: ${formatCurrencyWithSymbol(commission)}, Available: ${formatCurrencyWithSymbol(actualAvailable)}`);
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
    let isValid = false;
    
    switch (currentStep) {
      case 1:
        isValid = validateStep1();
        break;
      case 2:
        isValid = validateStep2();
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

  const handleCreateBet = async () => {
    if (!validateStep2()) return;
    
    setLoading(true);
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
        showSuccess(`Bet created! ${formatCurrencyWithSymbol(totalGemValue * COMMISSION_RATE)} (6%) frozen until game completion.`);
        await refreshInventory();
        onUpdateUser?.();
        onClose();
      } else {
        showError(data.detail || 'Failed to create bet');
      }
    } catch (error) {
      showError('Network error. Please try again.');
    } finally {
      setLoading(false);
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
              <span className="text-green-400 text-xs font-rajdhani font-bold">= {formatCurrencyWithSymbol(gemTotal)}</span>
            </div>
          );
        })}
      </div>
    );
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      {/* Fixed Bet Amount at Top */}
      <div className="sticky top-0 bg-surface-card border-b border-border-primary p-4 -m-4 mb-2 z-10">
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
            className="w-full px-4 py-3 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-white text-xl font-rajdhani font-bold text-center focus:outline-none focus:border-accent-primary"
          />
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-green-400 text-xl font-bold">
            $
          </div>
        </div>
        <div className="flex justify-between text-text-secondary text-sm mt-2">
          <span>Min: ${MIN_BET}</span>
          <span>Max: ${MAX_BET}</span>
        </div>
      </div>

      {/* Strategy Buttons */}
      <div>
        <label className="block text-white font-rajdhani text-lg mb-3">
          Auto Combination
        </label>
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => handleStrategySelect('small')}
            disabled={!betAmount || parseFloat(betAmount) <= 0}
            className="px-4 py-3 bg-red-600 hover:bg-red-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Use more cheap gems"
          >
            Small
          </button>
          <button
            onClick={() => handleStrategySelect('smart')}
            disabled={!betAmount || parseFloat(betAmount) <= 0}
            className="px-4 py-3 bg-green-600 hover:bg-green-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Balance bet with medium gems"
          >
            Smart
          </button>
          <button
            onClick={() => handleStrategySelect('big')}
            disabled={!betAmount || parseFloat(betAmount) <= 0}
            className="px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Use minimum quantity of expensive gems"
          >
            Big
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
            {formatCurrencyWithSymbol(totalGemValue)}
            {betAmount && parseFloat(betAmount) > 0 && (
              <span className="text-text-secondary text-sm ml-2">
                / {formatCurrencyWithSymbol(parseFloat(betAmount))}
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
      <div>
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
                  <img src={gem.icon} alt={gem.name} className="w-8 h-8 mx-auto mb-1" />
                  <div className="text-white font-rajdhani font-bold text-xs">{gem.name}</div>
                  <div className="text-text-secondary text-xs">{formatCurrencyWithSymbol(gem.price)}</div>
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
        <p className="text-text-secondary">Select your strategy for the battle</p>
        <div className="text-green-400 font-rajdhani text-lg mt-2">
          Betting: {formatCurrencyWithSymbol(totalGemValue)}
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

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-white font-rajdhani text-xl mb-4">Confirm Your Bet</h3>
      </div>

      <div className="bg-surface-sidebar rounded-lg p-4 space-y-3">
        <div className="flex justify-between">
          <span className="text-text-secondary">Bet Amount:</span>
          <span className="text-white font-rajdhani font-bold">{formatCurrencyWithSymbol(totalGemValue)}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-text-secondary">Commission (6%):</span>
          <span className="text-orange-400 font-rajdhani font-bold">
            {formatCurrencyWithSymbol(totalGemValue * COMMISSION_RATE)}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-text-secondary">Your Move:</span>
          <span className="text-white font-rajdhani font-bold capitalize">{selectedMove}</span>
        </div>

        <div className="border-t border-border-primary pt-3 mt-3">
          <div className="text-text-secondary text-sm mb-2">Selected Gems (from Inventory):</div>
          <div className="space-y-2">
            {renderSelectedGems()}
          </div>
        </div>
      </div>

      <div className="bg-yellow-900 bg-opacity-20 border border-yellow-500 border-opacity-30 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <svg className="w-5 h-5 text-yellow-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <div className="text-yellow-400 text-sm">
            <div className="font-bold mb-1">Important:</div>
            <div>Your gems and commission will be frozen in inventory until the game completes. The bet will auto-cancel in 24 hours if no opponent joins.</div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg w-full max-w-lg max-h-[90vh] overflow-hidden">
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
            
            {currentStep < 3 ? (
              <button
                onClick={handleNext}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300 disabled:opacity-50"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleCreateBet}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-green-600 to-green-700 text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Bet'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateBetModal;