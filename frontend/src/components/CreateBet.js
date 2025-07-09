import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateBet = ({ onClose, onGameCreated }) => {
  const [selectedMove, setSelectedMove] = useState('');
  const [betAmount, setBetAmount] = useState('');
  const [selectedGems, setSelectedGems] = useState({});
  const [availableGems, setAvailableGems] = useState([]);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoMode, setAutoMode] = useState(true);

  const moves = [
    { id: 'rock', name: 'Rock', icon: '🪨', color: '#8B4513' },
    { id: 'paper', name: 'Paper', icon: '📄', color: '#E6E6FA' },
    { id: 'scissors', name: 'Scissors', icon: '✂️', color: '#C0C0C0' }
  ];

  useEffect(() => {
    fetchAvailableGems();
    fetchBalance();
  }, []);

  useEffect(() => {
    if (autoMode && betAmount && availableGems.length > 0) {
      autoSelectGems();
    }
  }, [betAmount, autoMode, availableGems]);

  const fetchAvailableGems = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/gems/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAvailableGems(response.data);
    } catch (error) {
      console.error('Error fetching gems:', error);
    }
  };

  const fetchBalance = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/economy/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBalance(response.data);
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  const autoSelectGems = () => {
    const targetAmount = parseFloat(betAmount);
    if (!targetAmount || targetAmount <= 0) return;

    // Sort gems by price descending (Sapphire, Magic first as per requirements)
    const sortedGems = [...availableGems].sort((a, b) => b.price - a.price);
    
    let remainingAmount = targetAmount;
    const newSelection = {};

    // Greedy algorithm starting with highest value gems
    for (const gem of sortedGems) {
      const availableQuantity = gem.quantity - gem.frozen_quantity;
      if (availableQuantity > 0 && remainingAmount > 0) {
        const neededQuantity = Math.min(
          Math.floor(remainingAmount / gem.price),
          availableQuantity
        );
        
        if (neededQuantity > 0) {
          newSelection[gem.type] = neededQuantity;
          remainingAmount -= neededQuantity * gem.price;
        }
      }
    }

    // If we couldn't reach exact amount, try to fill with smaller gems
    if (remainingAmount > 0) {
      const sortedGemsAsc = [...availableGems].sort((a, b) => a.price - b.price);
      for (const gem of sortedGemsAsc) {
        const availableQuantity = gem.quantity - gem.frozen_quantity;
        const currentlySelected = newSelection[gem.type] || 0;
        const canSelectMore = availableQuantity - currentlySelected;
        
        if (canSelectMore > 0 && remainingAmount >= gem.price) {
          const additionalNeeded = Math.min(
            Math.floor(remainingAmount / gem.price),
            canSelectMore
          );
          
          if (additionalNeeded > 0) {
            newSelection[gem.type] = (newSelection[gem.type] || 0) + additionalNeeded;
            remainingAmount -= additionalNeeded * gem.price;
          }
        }
      }
    }

    setSelectedGems(newSelection);
  };

  const handleManualGemChange = (gemType, quantity) => {
    const gem = availableGems.find(g => g.type === gemType);
    const maxAvailable = gem.quantity - gem.frozen_quantity;
    const newQuantity = Math.max(0, Math.min(maxAvailable, parseInt(quantity) || 0));
    
    setSelectedGems(prev => ({
      ...prev,
      [gemType]: newQuantity
    }));
    
    // Calculate new total amount
    const newTotal = Object.entries({...selectedGems, [gemType]: newQuantity})
      .reduce((total, [type, qty]) => {
        const gemData = availableGems.find(g => g.type === type);
        return total + (gemData ? gemData.price * qty : 0);
      }, 0);
    
    setBetAmount(newTotal.toString());
  };

  const getTotalBetAmount = () => {
    return Object.entries(selectedGems).reduce((total, [gemType, quantity]) => {
      const gem = availableGems.find(g => g.type === gemType);
      return total + (gem ? gem.price * quantity : 0);
    }, 0);
  };

  const getCommissionRequired = () => {
    return getTotalBetAmount() * 0.06;
  };

  const canCreateGame = () => {
    const totalAmount = getTotalBetAmount();
    const commission = getCommissionRequired();
    
    return (
      selectedMove &&
      totalAmount >= 1 &&
      totalAmount <= 3000 &&
      balance &&
      balance.virtual_balance >= commission &&
      Object.values(selectedGems).some(qty => qty > 0)
    );
  };

  const handleCreateGame = async () => {
    if (!canCreateGame()) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/games/create`, {
        move: selectedMove,
        bet_gems: selectedGems
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert(response.data.message);
      if (onGameCreated) onGameCreated();
      if (onClose) onClose();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error creating game');
    } finally {
      setLoading(false);
    }
  };

  const totalAmount = getTotalBetAmount();
  const commissionRequired = getCommissionRequired();
  const canAfford = balance && balance.virtual_balance >= commissionRequired;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-surface-card border border-border-primary rounded-xl max-w-4xl w-full max-h-screen overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="font-russo text-3xl text-accent-primary">Create New Bet</h2>
            <button
              onClick={onClose}
              className="text-text-secondary hover:text-white text-2xl"
            >
              ✕
            </button>
          </div>

          {/* Balance Info */}
          {balance && (
            <div className="bg-surface-sidebar border border-border-primary rounded-lg p-4 mb-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-text-secondary text-sm">Virtual Balance</p>
                  <p className="font-rajdhani text-xl font-bold text-green-400">
                    ${balance.virtual_balance.toFixed(2)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-text-secondary text-sm">Available Gems</p>
                  <p className="font-rajdhani text-xl font-bold text-accent-primary">
                    ${balance.available_gem_value.toFixed(2)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-text-secondary text-sm">Commission (6%)</p>
                  <p className={`font-rajdhani text-xl font-bold ${canAfford ? 'text-yellow-400' : 'text-red-400'}`}>
                    ${commissionRequired.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Move Selection */}
          <div className="mb-6">
            <h3 className="font-russo text-xl text-white mb-4">Choose Your Move</h3>
            <div className="grid grid-cols-3 gap-4">
              {moves.map((move) => (
                <button
                  key={move.id}
                  onClick={() => setSelectedMove(move.id)}
                  className={`p-6 rounded-lg border-2 transition-all duration-300 ${
                    selectedMove === move.id
                      ? 'border-accent-primary bg-accent-primary bg-opacity-20'
                      : 'border-border-primary hover:border-accent-secondary'
                  }`}
                >
                  <div className="text-4xl mb-2">{move.icon}</div>
                  <div className="font-rajdhani font-bold text-white">{move.name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Bet Amount Input */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-russo text-xl text-white">Bet Amount</h3>
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={autoMode}
                    onChange={(e) => setAutoMode(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-text-secondary">Auto Select</span>
                </label>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <input
                  type="number"
                  min="1"
                  max="3000"
                  step="0.01"
                  value={betAmount}
                  onChange={(e) => setBetAmount(e.target.value)}
                  placeholder="Enter bet amount ($1 - $3000)"
                  className="w-full px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-rajdhani text-lg"
                />
              </div>
              <div className="text-center">
                <p className="text-text-secondary text-sm">Total Selected</p>
                <p className="font-rajdhani text-xl font-bold text-accent-primary">
                  ${totalAmount.toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          {/* Gem Selection */}
          <div className="mb-6">
            <h3 className="font-russo text-xl text-white mb-4">
              Gem Selection {!autoMode && '(Manual)'}
            </h3>
            
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {availableGems.map((gem) => {
                const selectedQuantity = selectedGems[gem.type] || 0;
                const availableQuantity = gem.quantity - gem.frozen_quantity;
                
                return (
                  <div
                    key={gem.type}
                    className="bg-surface-sidebar border border-border-primary rounded-lg p-4"
                  >
                    <div className="flex justify-center mb-2">
                      <img
                        src={`/gems/${gem.icon}`}
                        alt={gem.name}
                        className="w-12 h-12 object-contain"
                      />
                    </div>
                    
                    <div className="text-center mb-3">
                      <h4 className="font-russo text-white text-sm">{gem.name}</h4>
                      <p className="font-rajdhani text-green-400 font-bold">${gem.price}</p>
                      <p className="text-text-secondary text-xs">
                        Available: {availableQuantity}
                      </p>
                    </div>
                    
                    {!autoMode && (
                      <input
                        type="number"
                        min="0"
                        max={availableQuantity}
                        value={selectedQuantity}
                        onChange={(e) => handleManualGemChange(gem.type, e.target.value)}
                        className="w-full px-2 py-1 bg-surface-card border border-border-primary rounded text-white text-center text-sm"
                        disabled={availableQuantity === 0}
                      />
                    )}
                    
                    {selectedQuantity > 0 && (
                      <div className="mt-2 text-center">
                        <span className="text-accent-primary font-bold text-sm">
                          Selected: {selectedQuantity}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button
              onClick={onClose}
              className="flex-1 py-3 px-6 bg-gray-600 text-white rounded-lg font-rajdhani font-bold hover:bg-gray-700 transition-colors"
            >
              CANCEL
            </button>
            
            <button
              onClick={handleCreateGame}
              disabled={!canCreateGame() || loading}
              className={`flex-1 py-3 px-6 rounded-lg font-rajdhani font-bold transition-colors ${
                canCreateGame() && !loading
                  ? 'bg-gradient-accent text-white hover:opacity-90'
                  : 'bg-gray-600 text-gray-400 cursor-not-allowed'
              }`}
            >
              {loading ? 'CREATING...' : 'CREATE BET'}
            </button>
          </div>

          {/* Validation Messages */}
          {totalAmount > 0 && totalAmount < 1 && (
            <p className="text-red-400 text-sm mt-2">Minimum bet is $1</p>
          )}
          {totalAmount > 3000 && (
            <p className="text-red-400 text-sm mt-2">Maximum bet is $3000</p>
          )}
          {!canAfford && totalAmount > 0 && (
            <p className="text-red-400 text-sm mt-2">
              Insufficient balance for commission. Need ${commissionRequired.toFixed(2)}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default CreateBet;