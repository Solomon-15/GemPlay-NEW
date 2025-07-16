import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import { 
  GAME_MOVES, 
  GAME_CONSTANTS, 
  calculateTotalBetAmount, 
  calculateCommission, 
  validateBet, 
  filterValidGems 
} from '../utils/gameUtils';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateGame = ({ user, onUpdateUser }) => {
  const { showSuccess, showError, showWarning } = useNotifications();
  const [gems, setGems] = useState([]);
  const [selectedGems, setSelectedGems] = useState({});
  const [selectedMove, setSelectedMove] = useState('');
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [balance, setBalance] = useState(null);

  // Use shared moves constant
  const moves = GAME_MOVES;

  useEffect(() => {
    fetchUserGems();
    fetchBalance();
  }, []);

  const fetchUserGems = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/gems/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGems(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching gems:', error);
      setLoading(false);
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

  const handleGemQuantityChange = (gemType, quantity) => {
    const numQuantity = Math.max(0, parseInt(quantity) || 0);
    const availableGem = gems.find(g => g.type === gemType);
    const maxQuantity = availableGem ? availableGem.quantity - availableGem.frozen_quantity : 0;
    
    setSelectedGems(prev => ({
      ...prev,
      [gemType]: Math.min(numQuantity, maxQuantity)
    }));
  };

  const getTotalBetAmount = () => {
    return calculateTotalBetAmount(selectedGems, gems);
  };

  const getCommissionAmount = () => {
    return calculateCommission(getTotalBetAmount());
  };

  const validateBetForm = () => {
    return validateBet(selectedGems, gems, balance);
  };

  const handleCreateGame = async () => {
    if (!selectedMove) {
      showWarning('Please select your move!');
      return;
    }

    const validationError = validateBet();
    if (validationError) {
      showError(validationError);
      return;
    }

    // Filter out gems with 0 quantity
    const betGems = {};
    for (const [gemType, quantity] of Object.entries(selectedGems)) {
      if (quantity > 0) {
        betGems[gemType] = quantity;
      }
    }

    if (Object.keys(betGems).length === 0) {
      showWarning('Please select at least one gem for betting');
      return;
    }

    setCreating(true);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/games/create`, {
        move: selectedMove,
        bet_gems: betGems
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Calculate and display the notification exactly like the reference image
      const commissionAmount = response.data.commission_reserved.toFixed(2);
      const commissionPercent = ((response.data.commission_reserved / response.data.bet_amount) * 100).toFixed(0);
      
      showSuccess(`Bet created! $${commissionAmount} (${commissionPercent}%) frozen until game completion.`, { 
        duration: 7000 
      });
      
      // Reset form
      setSelectedGems({});
      setSelectedMove('');
      
      // Refresh data
      await fetchUserGems();
      await fetchBalance();
      
      if (onUpdateUser) {
        onUpdateUser();
      }
    } catch (error) {
      console.error('Error creating game:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to create game. Please try again.';
      showError(errorMessage);
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Загрузка...</div>
      </div>
    );
  }

  const totalBet = getTotalBetAmount();
  const commission = getCommissionAmount();
  const validationError = validateBet();

  return (
    <div className="min-h-screen bg-gradient-primary p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-4xl md:text-6xl text-accent-primary mb-4">
          Создать игру
        </h1>
        <p className="font-roboto text-xl text-text-secondary">
          Выберите свой ход и поставьте гемы
        </p>
      </div>

      {/* Balance Info */}
      {balance && (
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="font-roboto text-text-secondary">Баланс</p>
                <p className="font-rajdhani text-2xl font-bold text-green-400">
                  ${balance.virtual_balance.toFixed(2)}
                </p>
              </div>
              <div className="text-center">
                <p className="font-roboto text-text-secondary">Ставка</p>
                <p className="font-rajdhani text-2xl font-bold text-accent-primary">
                  ${totalBet.toFixed(2)}
                </p>
              </div>
              <div className="text-center">
                <p className="font-roboto text-text-secondary">Комиссия (6%)</p>
                <p className="font-rajdhani text-2xl font-bold text-yellow-400">
                  ${commission.toFixed(2)}
                </p>
              </div>
              <div className="text-center">
                <p className="font-roboto text-text-secondary">Остаток</p>
                <p className={`font-rajdhani text-2xl font-bold ${
                  balance.virtual_balance - commission >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  ${(balance.virtual_balance - commission).toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Move Selection */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h2 className="font-russo text-2xl text-accent-secondary mb-6">
              Выберите ваш ход
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {moves.map((move) => (
                <button
                  key={move.value}
                  onClick={() => setSelectedMove(move.value)}
                  className={`p-6 rounded-lg border-2 transition-all duration-300 ${
                    selectedMove === move.value
                      ? 'border-accent-primary bg-accent-primary/20 text-accent-primary'
                      : 'border-accent-primary border-opacity-30 hover:border-accent-primary hover:border-opacity-60 text-text-secondary'
                  }`}
                >
                  <div className="text-4xl mb-2">{move.icon}</div>
                  <div className="font-rajdhani font-bold text-lg">{move.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Gem Selection */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h2 className="font-russo text-2xl text-accent-secondary mb-6">
              Выберите гемы для ставки
            </h2>
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {gems.map((gem) => {
                const availableQuantity = gem.quantity - gem.frozen_quantity;
                const selectedQuantity = selectedGems[gem.type] || 0;
                
                return (
                  <div
                    key={gem.type}
                    className="flex items-center justify-between p-4 bg-surface-sidebar rounded-lg border border-accent-primary border-opacity-30"
                  >
                    <div className="flex items-center space-x-4">
                      <img
                        src={`/gems/${gem.icon}`}
                        alt={gem.name}
                        className="w-12 h-12 object-contain"
                        style={{
                          filter: `drop-shadow(0 0 8px ${gem.color}60)`
                        }}
                      />
                      <div>
                        <h3 className="font-rajdhani font-bold text-white">{gem.name}</h3>
                        <p className="font-roboto text-text-secondary text-sm">
                          Цена: ${gem.price} | Доступно: {availableQuantity}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        min="0"
                        max={availableQuantity}
                        value={selectedQuantity}
                        onChange={(e) => handleGemQuantityChange(gem.type, e.target.value)}
                        className="w-20 px-2 py-1 bg-surface-card border border-accent-primary border-opacity-30 rounded text-center text-white font-rajdhani"
                        disabled={availableQuantity === 0}
                      />
                      <span className="font-roboto text-text-secondary text-sm">
                        = ${(gem.price * selectedQuantity).toFixed(2)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
        
        {/* Create Game Button */}
        <div className="mt-8 text-center">
          {validationError && (
            <p className="font-roboto text-red-400 mb-4">{validationError}</p>
          )}
          
          <button
            onClick={handleCreateGame}
            disabled={creating || !selectedMove || validationError}
            className={`px-8 py-4 rounded-lg font-rajdhani font-bold text-xl transition-all duration-300 ${
              creating || !selectedMove || validationError
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-accent text-white hover:scale-105 hover:shadow-lg'
            }`}
          >
            {creating ? 'СОЗДАНИЕ ИГРЫ...' : 'СОЗДАТЬ ИГРУ'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateGame;