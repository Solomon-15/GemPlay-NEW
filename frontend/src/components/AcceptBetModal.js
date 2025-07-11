import React, { useState, useEffect } from 'react';
import { useGems } from './GemsContext';
import { useNotifications } from './NotificationContext';
import { formatCurrencyWithSymbol, autoSelectGems } from '../utils/economy';

const AcceptBetModal = ({ bet, onClose, onUpdateUser }) => {
  const { gemsDefinitions, refreshGemsData } = useGems();
  const { showSuccess, showError } = useNotifications();
  
  // Modal state
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Step 1: Funds check & gem selection
  const [selectedGems, setSelectedGems] = useState({});
  const [totalGemValue, setTotalGemValue] = useState(0);
  const [useAuto, setUseAuto] = useState(true);
  
  // Step 2: Move selection
  const [selectedMove, setSelectedMove] = useState('');
  
  // Step 3: Match result
  const [matchResult, setMatchResult] = useState(null);
  const [countdown, setCountdown] = useState(3);
  const [showResult, setShowResult] = useState(false);
  
  // Constants
  const COMMISSION_RATE = 0.06; // 6%
  const targetAmount = bet?.bet_amount || 0;
  
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

  // Auto-select gems from most expensive
  const autoSelectGemsFromAmount = (amount) => {
    if (!gemsDefinitions.length || amount <= 0) return {};
    
    const availableGems = gemsDefinitions
      .filter(gem => gem.quantity > gem.frozen_quantity)
      .sort((a, b) => b.price - a.price); // Sort by price descending
    
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

  // Auto-select gems when component loads
  useEffect(() => {
    if (useAuto && targetAmount && gemsDefinitions.length > 0) {
      const autoSelected = autoSelectGemsFromAmount(targetAmount);
      setSelectedGems(autoSelected);
    }
  }, [targetAmount, useAuto, gemsDefinitions]);

  const handleAutoSelect = () => {
    const autoSelected = autoSelectGemsFromAmount(targetAmount);
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
    const commission = targetAmount * COMMISSION_RATE;
    // Note: In real app, we'd get user balance from props or context
    // For now, we'll assume the check passes
    
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
        if (isValid) {
          // Start countdown and match
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

  const startMatch = () => {
    setCurrentStep(3);
    
    // Start countdown
    let count = 3;
    setCountdown(count);
    
    const countdownInterval = setInterval(() => {
      count--;
      setCountdown(count);
      
      if (count <= 0) {
        clearInterval(countdownInterval);
        // Simulate game result
        simulateGameResult();
      }
    }, 1000);
  };

  const simulateGameResult = () => {
    // Simulate random opponent move and result
    const opponentMoves = ['rock', 'paper', 'scissors'];
    const opponentMove = opponentMoves[Math.floor(Math.random() * 3)];
    
    let result = 'draw';
    if (
      (selectedMove === 'rock' && opponentMove === 'scissors') ||
      (selectedMove === 'paper' && opponentMove === 'rock') ||
      (selectedMove === 'scissors' && opponentMove === 'paper')
    ) {
      result = 'win';
    } else if (
      (selectedMove === 'scissors' && opponentMove === 'rock') ||
      (selectedMove === 'rock' && opponentMove === 'paper') ||
      (selectedMove === 'paper' && opponentMove === 'scissors')
    ) {
      result = 'lose';
    }

    setMatchResult({
      playerMove: selectedMove,
      opponentMove,
      result,
      playerGems: selectedGems,
      opponentGems: bet?.bet_gems || {},
      commission: targetAmount * COMMISSION_RATE
    });
    
    setShowResult(true);
    
    // Auto-close after 30 seconds
    setTimeout(() => {
      onClose();
    }, 30000);
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-white font-rajdhani text-xl mb-2">Match Opponent's Bet</h3>
        <div className="text-green-400 font-rajdhani text-2xl font-bold">
          Target: {formatCurrencyWithSymbol(targetAmount)}
        </div>
        <div className="text-blue-400 font-rajdhani text-lg">
          Your Bet: {formatCurrencyWithSymbol(totalGemValue)}
        </div>
        {Math.abs(totalGemValue - targetAmount) > 0.01 && (
          <div className="text-orange-400 text-sm mt-1">
            Difference: {formatCurrencyWithSymbol(Math.abs(totalGemValue - targetAmount))}
          </div>
        )}
      </div>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h4 className="text-white font-rajdhani text-lg">Gem Selection</h4>
          <button
            onClick={handleAutoSelect}
            className="px-4 py-2 bg-blue-600 text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300"
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
        </div>
      );
    }

    const { result, playerMove, opponentMove, commission } = matchResult;
    
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
            <span className="text-white font-rajdhani font-bold">{formatCurrencyWithSymbol(totalGemValue)}</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-text-secondary">Commission:</span>
            <span className="text-orange-400 font-rajdhani font-bold">
              {formatCurrencyWithSymbol(commission)}
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
        </div>

        <div className="text-center text-text-secondary text-sm">
          This window will close automatically in 30 seconds
        </div>
      </div>
    );
  };

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
};

export default AcceptBetModal;