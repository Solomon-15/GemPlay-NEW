import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateBetModal = ({ user, onClose, onUpdateUser }) => {
  const { showSuccess, showError, showWarning } = useNotifications();
  
  const [betAmount, setBetAmount] = useState('');
  const [selectedMove, setSelectedMove] = useState('');
  const [selectedGems, setSelectedGems] = useState({});
  const [isAutoMode, setIsAutoMode] = useState(true);
  const [userGems, setUserGems] = useState([]);
  const [userBalance, setUserBalance] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [betDetails, setBetDetails] = useState(null);

  const moves = [
    { value: 'rock', label: 'Rock', icon: '🪨' },
    { value: 'paper', label: 'Paper', icon: '📄' },
    { value: 'scissors', label: 'Scissors', icon: '✂️' }
  ];

  const gemDefinitions = [
    { name: 'Magic', value: 100, icon: '/gems/gem-purple.svg' },
    { name: 'Sapphire', value: 50, icon: '/gems/gem-blue.svg' },
    { name: 'Aquamarine', value: 25, icon: '/gems/gem-cyan.svg' },
    { name: 'Emerald', value: 10, icon: '/gems/gem-green.svg' },
    { name: 'Topaz', value: 5, icon: '/gems/gem-yellow.svg' },
    { name: 'Amber', value: 2, icon: '/gems/gem-orange.svg' },
    { name: 'Ruby', value: 1, icon: '/gems/gem-red.svg' }
  ];

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch user gems inventory
      const gemsResponse = await axios.get(`${API}/gems/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Fetch user balance
      const balanceResponse = await axios.get(`${API}/economy/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setUserGems(gemsResponse.data.gems || []);
      setUserBalance(balanceResponse.data.virtual_balance || 0);
    } catch (error) {
      console.error('Error fetching user data:', error);
      showError('Failed to load user data');
    }
  };

  const autoSelectGems = (targetAmount) => {
    if (!userGems || userGems.length === 0) {
      return {};
    }
    
    const availableGems = userGems.filter(gem => gem.quantity > 0);
    let remainingAmount = targetAmount;
    let selectedGems = {};
    
    // Sort gems by value (descending - start with most valuable)
    const sortedGems = availableGems.sort((a, b) => {
      const aValue = gemDefinitions.find(g => g.name === a.gem_type)?.value || 0;
      const bValue = gemDefinitions.find(g => g.name === b.gem_type)?.value || 0;
      return bValue - aValue;
    });
    
    for (const gem of sortedGems) {
      const gemData = gemDefinitions.find(g => g.name === gem.gem_type);
      if (!gemData) continue;
      
      const maxQuantity = Math.min(gem.quantity, Math.floor(remainingAmount / gemData.value));
      if (maxQuantity > 0) {
        selectedGems[gem.gem_type] = maxQuantity;
        remainingAmount -= maxQuantity * gemData.value;
      }
      
      if (remainingAmount <= 0) break;
    }
    
    return selectedGems;
  };

  const handleBetAmountChange = (value) => {
    setBetAmount(value);
    
    if (isAutoMode && value) {
      const amount = parseFloat(value);
      if (amount > 0) {
        const autoGems = autoSelectGems(amount);
        setSelectedGems(autoGems);
      } else {
        setSelectedGems({});
      }
    }
  };

  const calculateTotalGemValue = () => {
    let total = 0;
    Object.entries(selectedGems).forEach(([gemType, quantity]) => {
      const gemData = gemDefinitions.find(g => g.name === gemType);
      if (gemData) {
        total += gemData.value * quantity;
      }
    });
    return total;
  };

  const calculateTotalBetValue = () => {
    const baseAmount = parseFloat(betAmount) || 0;
    const gemValue = calculateTotalGemValue();
    return baseAmount + gemValue;
  };

  const handleCreateBet = async () => {
    if (!betAmount || parseFloat(betAmount) < 1) {
      showWarning('Minimum bet amount is $1');
      return;
    }
    
    if (parseFloat(betAmount) > 3000) {
      showWarning('Maximum bet amount is $3000');
      return;
    }
    
    if (!selectedMove) {
      showWarning('Please select your move');
      return;
    }
    
    const totalBetValue = calculateTotalBetValue();
    const commission = totalBetValue * 0.06;
    const requiredBalance = commission;
    
    if (userBalance < requiredBalance) {
      showError(`Insufficient balance. You need $${requiredBalance.toFixed(2)} for the 6% commission`);
      return;
    }
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/games/create`, {
        bet_amount: parseFloat(betAmount),
        bet_gems: selectedGems,
        move: selectedMove
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setBetDetails({
          totalValue: totalBetValue,
          commission: commission,
          gameId: response.data.game_id
        });
        setShowConfirmation(true);
        
        // Update user data
        if (onUpdateUser) {
          onUpdateUser();
        }
      }
    } catch (error) {
      console.error('Error creating bet:', error);
      showError(error.response?.data?.detail || 'Failed to create bet');
    } finally {
      setLoading(false);
    }
  };

  const handleGemQuantityChange = (gemType, quantity) => {
    if (isAutoMode) return; // Don't allow manual changes in auto mode
    
    if (!userGems || userGems.length === 0) return;
    
    const maxQuantity = userGems.find(g => g.gem_type === gemType)?.quantity || 0;
    const newQuantity = Math.max(0, Math.min(quantity, maxQuantity));
    
    setSelectedGems(prev => ({
      ...prev,
      [gemType]: newQuantity
    }));
  };

  if (showConfirmation && betDetails) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-surface-card border border-accent-primary rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            
            <h3 className="font-rajdhani text-2xl font-bold text-white mb-4">
              Bet Created Successfully!
            </h3>
            
            <div className="space-y-3 mb-6">
              <div className="flex justify-between">
                <span className="text-text-secondary">Total Bet Value:</span>
                <span className="text-accent-primary font-bold">${betDetails.totalValue.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Commission (6%):</span>
                <span className="text-yellow-400 font-bold">${betDetails.commission.toFixed(2)} frozen</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Game ID:</span>
                <span className="text-white font-mono">{betDetails.gameId}</span>
              </div>
            </div>
            
            <p className="text-text-secondary text-sm mb-6">
              Your bet is now live and waiting for opponents!
            </p>
            
            <button
              onClick={onClose}
              className="w-full py-3 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-surface-card border border-accent-primary rounded-lg p-6 max-w-xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-russo text-xl text-accent-primary">Create Bet</h2>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          {/* Bet Amount */}
          <div>
            <label className="block text-text-secondary text-sm font-rajdhani mb-1">
              Bet Amount ($1 - $3000)
            </label>
            <input
              type="number"
              min="1"
              max="3000"
              value={betAmount}
              onChange={(e) => handleBetAmountChange(e.target.value)}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
              placeholder="Enter bet amount"
            />
          </div>

          {/* Auto/Manual Mode Toggle */}
          <div className="flex items-center justify-between">
            <span className="text-text-secondary font-rajdhani text-sm">Gem Selection:</span>
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  setIsAutoMode(true);
                  if (betAmount) {
                    const autoGems = autoSelectGems(parseFloat(betAmount));
                    setSelectedGems(autoGems);
                  }
                }}
                className={`px-3 py-1 rounded font-rajdhani text-sm ${
                  isAutoMode 
                    ? 'bg-accent-primary text-white' 
                    : 'bg-surface-sidebar text-text-secondary'
                }`}
              >
                Auto
              </button>
              <button
                onClick={() => setIsAutoMode(false)}
                className={`px-3 py-1 rounded font-rajdhani text-sm ${
                  !isAutoMode 
                    ? 'bg-accent-primary text-white' 
                    : 'bg-surface-sidebar text-text-secondary'
                }`}
              >
                Manual
              </button>
            </div>
          </div>

          {/* Mini Inventory - Compact Grid */}
          <div>
            <h3 className="text-white font-rajdhani font-bold text-sm mb-2">Gem Selection</h3>
            <div className="grid grid-cols-4 gap-2">
              {gemDefinitions.map((gem) => {
                const userGem = userGems.find(g => g.gem_type === gem.name);
                const available = userGem?.quantity || 0;
                const selected = selectedGems[gem.name] || 0;
                
                return (
                  <div key={gem.name} className="bg-surface-sidebar border border-border-primary rounded-lg p-2">
                    <div className="flex flex-col items-center space-y-1">
                      <img src={gem.icon} alt={gem.name} className="w-5 h-5" />
                      <div className="text-center">
                        <div className="text-white font-rajdhani font-bold text-xs">{gem.name}</div>
                        <div className="text-text-secondary text-xs">${gem.value}</div>
                      </div>
                      
                      <div className="flex items-center space-x-1 w-full">
                        <input
                          type="number"
                          min="0"
                          max={available}
                          value={selected}
                          onChange={(e) => handleGemQuantityChange(gem.name, parseInt(e.target.value) || 0)}
                          disabled={isAutoMode}
                          className={`w-full px-1 py-1 bg-surface-card border border-border-primary rounded text-white text-xs text-center ${
                            isAutoMode ? 'opacity-50 cursor-not-allowed' : ''
                          }`}
                        />
                      </div>
                      <div className="text-text-secondary text-xs">/{available}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Move Selection */}
          <div>
            <h3 className="text-white font-rajdhani font-bold text-sm mb-2">Select Your Move</h3>
            <div className="grid grid-cols-3 gap-3">
              {moves.map((move) => (
                <button
                  key={move.value}
                  onClick={() => setSelectedMove(move.value)}
                  className={`p-3 rounded-lg border-2 transition-all duration-300 ${
                    selectedMove === move.value
                      ? 'border-accent-primary bg-accent-primary/20 text-accent-primary'
                      : 'border-border-primary hover:border-accent-primary/50 text-text-secondary'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-2xl mb-1">{move.icon}</div>
                    <div className="font-rajdhani font-bold text-sm">{move.label}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Bet Summary */}
          <div className="bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg p-3">
            <h3 className="text-white font-rajdhani font-bold text-sm mb-2">Bet Summary</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">Base Amount:</span>
                <span className="text-white">${(parseFloat(betAmount) || 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Gems Value:</span>
                <span className="text-white">${calculateTotalGemValue().toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-border-primary pt-1">
                <span className="text-white font-bold">Total Bet Value:</span>
                <span className="text-accent-primary font-bold">${calculateTotalBetValue().toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Commission (6%):</span>
                <span className="text-yellow-400">${(calculateTotalBetValue() * 0.06).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Your Balance:</span>
                <span className="text-white">${userBalance.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Create Bet Button */}
          <button
            onClick={handleCreateBet}
            disabled={loading || !betAmount || !selectedMove}
            className={`w-full py-3 rounded-lg font-rajdhani font-bold transition-all duration-300 ${
              loading || !betAmount || !selectedMove
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-accent text-white hover:scale-105'
            }`}
          >
            {loading ? 'Creating Bet...' : 'Create Bet'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateBetModal;