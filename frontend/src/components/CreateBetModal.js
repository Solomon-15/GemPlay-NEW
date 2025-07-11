import React, { useState, useEffect } from 'react';
import { useGems } from './GemsContext';
import { useNotifications } from './NotificationContext';
import { formatCurrencyWithSymbol, autoSelectGems } from '../utils/economy';

const CreateBetModal = ({ user, onClose, onUpdateUser }) => {
  const { gemsDefinitions, refreshGemsData } = useGems();
  const { showSuccess, showError } = useNotifications();
  
  // Modal state
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Step 1: Amount input
  const [betAmount, setBetAmount] = useState('');
  const [useAuto, setUseAuto] = useState(true);
  
  // Step 2: Gems selection
  const [selectedGems, setSelectedGems] = useState({});
  const [totalGemValue, setTotalGemValue] = useState(0);
  
  // Step 3: Move selection
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
    { id: 1, name: 'Amount', description: 'Enter bet amount' },
    { id: 2, name: 'Gems', description: 'Select gems' },
    { id: 3, name: 'Move', description: 'Choose your move' },
    { id: 4, name: 'Confirm', description: 'Create bet' }
  ];

  // Auto-select gems from most expensive
  const autoSelectGemsFromAmount = (amount) => {
    if (!gemsDefinitions.length || amount <= 0) return {};
    
    const availableGems = gemsDefinitions
      .filter(gem => gem.quantity > gem.frozen_quantity)
      .sort((a, b) => b.price - a.price); // Sort by price descending (most expensive first)
    
    const result = autoSelectGems(availableGems, amount);
    return result.selectedGems;
  };

  // Calculate total value of selected gems
  useEffect(() => {
    const total = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
      const gem = gemsDefinitions.find(g => g.type === gemType);
      return sum + (gem ? gem.price * quantity : 0);
    }, 0);
    setTotalGemValue(total);
  }, [selectedGems, gemsDefinitions]);

  // Auto-select gems when amount changes and auto mode is on
  useEffect(() => {
    if (useAuto && betAmount && parseFloat(betAmount) > 0) {
      const amount = parseFloat(betAmount);
      const autoSelected = autoSelectGemsFromAmount(amount);
      setSelectedGems(autoSelected);
    }
  }, [betAmount, useAuto, gemsDefinitions]);

  const handleAmountChange = (value) => {
    const numValue = parseFloat(value);
    if (isNaN(numValue) || numValue < MIN_BET || numValue > MAX_BET) {
      setBetAmount(value);
      return;
    }
    setBetAmount(value);
  };

  const handleAutoSelect = () => {
    if (!betAmount || parseFloat(betAmount) <= 0) return;
    
    const amount = parseFloat(betAmount);
    const autoSelected = autoSelectGemsFromAmount(amount);
    setSelectedGems(autoSelected);
    setUseAuto(true);
  };

  const handleGemQuantityChange = (gemType, quantity) => {
    setUseAuto(false);
    setSelectedGems(prev => {
      if (quantity <= 0) {
        const newGems = { ...prev };
        delete newGems[gemType];
        return newGems;
      }
      return { ...prev, [gemType]: quantity };
    });
  };

  const validateStep1 = () => {
    const amount = parseFloat(betAmount);
    if (isNaN(amount) || amount < MIN_BET || amount > MAX_BET) {
      showError(`Bet amount must be between $${MIN_BET} and $${MAX_BET}`);
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (Object.keys(selectedGems).length === 0) {
      showError('Please select at least one gem');
      return false;
    }

    // Check if user has enough gems
    for (const [gemType, quantity] of Object.entries(selectedGems)) {
      const gem = gemsDefinitions.find(g => g.type === gemType);
      if (!gem) {
        showError(`Invalid gem type: ${gemType}`);
        return false;
      }
      
      const available = gem.quantity - gem.frozen_quantity;
      if (available < quantity) {
        showError(`Not enough ${gemType} gems. Available: ${available}, Required: ${quantity}`);
        return false;
      }
    }

    // Check commission
    const commission = totalGemValue * COMMISSION_RATE;
    const availableBalance = user.virtual_balance - (user.frozen_balance || 0);
    
    if (availableBalance < commission) {
      showError(`Insufficient balance for commission. Required: ${formatCurrencyWithSymbol(commission)}, Available: ${formatCurrencyWithSymbol(availableBalance)}`);
      return false;
    }

    return true;
  };

  const validateStep3 = () => {
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
      case 3:
        isValid = validateStep3();
        break;
    }
    
    if (isValid && currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleCreateBet = async () => {
    if (!validateStep3()) return;
    
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
        refreshGemsData();
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

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-white font-rajdhani text-lg mb-2">
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

      <div className="text-center">
        <button
          onClick={handleAutoSelect}
          disabled={!betAmount || parseFloat(betAmount) <= 0}
          className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          AUTO SELECT GEMS
        </button>
        <p className="text-text-secondary text-sm mt-2">
          Automatically selects gems starting from most expensive
        </p>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-white font-rajdhani text-xl mb-2">Selected Gems</h3>
        <div className="text-green-400 font-rajdhani text-2xl font-bold">
          {formatCurrencyWithSymbol(totalGemValue)}
        </div>
        {betAmount && Math.abs(totalGemValue - parseFloat(betAmount)) > 0.01 && (
          <div className="text-orange-400 text-sm mt-1">
            Target: {formatCurrencyWithSymbol(parseFloat(betAmount))} 
            (Difference: {formatCurrencyWithSymbol(Math.abs(totalGemValue - parseFloat(betAmount)))})
          </div>
        )}
      </div>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-white font-rajdhani text-lg">Gem Selection</h4>
          <button
            onClick={handleAutoSelect}
            disabled={!betAmount}
            className="px-4 py-2 bg-blue-600 text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300 disabled:opacity-50"
          >
            Auto
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3 max-h-64 overflow-y-auto">
          {gemsDefinitions.map(gem => {
            const available = gem.quantity - gem.frozen_quantity;
            const selected = selectedGems[gem.type] || 0;
            
            if (available <= 0 && selected <= 0) return null;
            
            return (
              <div key={gem.type} className="bg-surface-sidebar rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <img src={gem.icon} alt={gem.name} className="w-6 h-6" />
                  <div>
                    <div className="text-white font-rajdhani font-bold text-sm">{gem.name}</div>
                    <div className="text-text-secondary text-xs">{formatCurrencyWithSymbol(gem.price)}</div>
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
          })}
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-white font-rajdhani text-xl mb-2">Choose Your Move</h3>
        <p className="text-text-secondary">Select your strategy for the battle</p>
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

  const renderStep4 = () => (
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
          <div className="text-text-secondary text-sm mb-2">Selected Gems:</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(selectedGems).map(([gemType, quantity]) => {
              const gem = gemsDefinitions.find(g => g.type === gemType);
              return gem ? (
                <div key={gemType} className="flex items-center space-x-1 bg-surface-card rounded px-2 py-1">
                  <img src={gem.icon} alt={gem.name} className="w-4 h-4" />
                  <span className="text-white text-sm">{quantity}</span>
                </div>
              ) : null;
            })}
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
            <div>Your gems and commission will be frozen until the game completes. The bet will auto-cancel in 24 hours if no opponent joins.</div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden">
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
          {currentStep === 4 && renderStep4()}
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
            
            {currentStep < 4 ? (
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