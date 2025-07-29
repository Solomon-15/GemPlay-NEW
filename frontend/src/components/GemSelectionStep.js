import React from 'react';
import { calculateGemCombination } from '../utils/gemCombinationAlgorithms';

const GemSelectionStep = ({
  targetAmount,
  commissionAmount,
  selectedGems,
  onSelectedGemsChange,
  gemsData,
  loading,
  onStrategySelect,
  showError
}) => {
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

  const totalGemValue = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
    const gem = gemsData.find(g => g.type === gemType);
    return sum + (gem ? gem.price * quantity : 0);
  }, 0);

  const handleGemQuantityChange = (gemType, quantity) => {
    const gem = gemsData.find(g => g.type === gemType);
    if (!gem) return;
    
    const maxQuantity = gem.available_quantity;
    const validQuantity = Math.max(0, Math.min(maxQuantity, quantity));
    
    const newSelectedGems = { ...selectedGems };
    
    if (validQuantity <= 0) {
      delete newSelectedGems[gemType];
    } else {
      newSelectedGems[gemType] = validQuantity;
    }
    
    onSelectedGemsChange(newSelectedGems);
  };

  // NEW STRATEGY HANDLER - Uses pure frontend algorithms
  const handleStrategyClick = (strategy) => {
    try {
      // Use new frontend algorithms
      const result = calculateGemCombination(strategy, gemsData, targetAmount);
      
      if (result.success) {
        // Convert result to internal format
        const autoSelected = {};
        result.combination.forEach(item => {
          autoSelected[item.type] = item.quantity;
        });
        
        onSelectedGemsChange(autoSelected);
        
        // Call original onStrategySelect if provided (for loading state)
        if (onStrategySelect) {
          onStrategySelect(strategy);
        }
      } else {
        showError(result.message);
      }
    } catch (error) {
      console.error('Error calculating gem combination:', error);
      showError('Error calculating gem combination');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h3 className="text-white font-rajdhani text-xl mb-2">Match Opponent's Bet</h3>
        <div className="text-green-400 font-rajdhani text-2xl font-bold">
          {formatCurrency(targetAmount)}
        </div>
        <div className="text-blue-400 font-rajdhani text-lg">
          Your Bet: {formatCurrency(totalGemValue)}
        </div>
        {commissionAmount > 0 && (
          <div className="text-orange-400 font-rajdhani text-sm">
            Commission: {formatCurrency(commissionAmount)}
          </div>
        )}
        
        {Math.abs(totalGemValue - targetAmount) > 0.01 && (
          <div className="text-red-400 text-sm mt-1">
            ⚠️ Amount mismatch: {formatCurrency(Math.abs(totalGemValue - targetAmount))}
          </div>
        )}
      </div>

      {/* Auto Combination Buttons - NEW IMPLEMENTATION */}
      <div className="space-y-3">
        <h4 className="text-white font-rajdhani text-lg">Auto Combination</h4>
        <div className="grid grid-cols-3 gap-3">
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleStrategyClick('small');
            }}
            disabled={loading}
            className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center text-sm"
            title="🔴 Use more cheap gems (Ruby, Amber, then others)"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              '🔴 Small'
            )}
          </button>
          
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleStrategyClick('smart');
            }}
            disabled={loading}
            className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center text-sm"
            title="🟢 Balanced mid-range gems (60% mid, 30% low, 10% high)"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              '🟢 Smart'
            )}
          </button>
          
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleStrategyClick('big');
            }}
            disabled={loading}
            className="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center text-sm"
            title="🟣 Use fewer expensive gems (Magic, Sapphire, then others)"
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
      <div className="bg-surface-sidebar rounded-lg p-4">
        <h5 className="text-white font-rajdhani font-bold mb-2">Selected Gems</h5>
        {Object.keys(selectedGems).length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {Object.entries(selectedGems)
              .map(([gemType, quantity]) => {
                const gem = gemsData.find(g => g.type === gemType);
                if (!gem) return null;
                return { ...gem, quantity };
              })
              .filter(Boolean)
              .sort((a, b) => a.price - b.price)
              .map((gem) => {
                const gemTotal = gem.quantity * gem.price;
                return (
                  <div key={gem.type} className="flex items-center space-x-1 bg-surface-card rounded-lg px-3 py-2 border border-opacity-30" style={{ borderColor: gem.color }}>
                    <img src={gem.icon} alt={gem.name} className="w-5 h-5" />
                    <span className="text-text-secondary text-xs font-rajdhani">x{gem.quantity}</span>
                    <span className="text-green-400 text-xs font-rajdhani font-bold">= {formatCurrency(gemTotal)}</span>
                  </div>
                );
              })}
          </div>
        ) : (
          <div className="text-text-secondary text-center py-4">
            No gems selected. Use Auto Combination or select manually below.
          </div>
        )}
      </div>

      {/* Mini-Inventory */}
      <div className="space-y-3">
        <h5 className="text-white font-rajdhani font-bold">Your Inventory</h5>
        <div className="flex flex-wrap gap-3">
          {gemsData && Array.isArray(gemsData) ? gemsData.map(gem => {
            const available = gem.available_quantity || 0;
            const selected = selectedGems[gem.type] || 0;
            
            if (!gem.has_available && selected <= 0) return null;
            
            return (
              <div key={gem.type} className="bg-surface-card rounded-lg p-3 border border-opacity-20 min-w-[140px]" style={{ borderColor: gem.color }}>
                <div className="flex items-center space-x-2 mb-2">
                  <img src={gem.icon} alt={gem.name} className="w-5 h-5" />
                  <div>
                    <div className="text-white font-rajdhani font-bold text-xs">{gem.name}</div>
                    <div className="text-text-secondary text-xs">{formatCurrency(gem.price)}</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-1">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleGemQuantityChange(gem.type, Math.max(0, selected - 1));
                    }}
                    disabled={selected <= 0}
                    className="w-5 h-5 bg-red-600 text-white rounded text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:scale-110 transition-all"
                  >
                    −
                  </button>
                  
                  <div className="flex-1 text-center">
                    <div className="text-white font-rajdhani font-bold text-xs">{selected}</div>
                    <div className="text-text-secondary text-xs">/{available}</div>
                  </div>
                  
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleGemQuantityChange(gem.type, selected + 1);
                    }}
                    disabled={selected >= available}
                    className="w-5 h-5 bg-green-600 text-white rounded text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:scale-110 transition-all"
                  >
                    +
                  </button>
                </div>
              </div>
            );
          }) : (
            <div className="text-center text-text-secondary py-4 w-full">
              Loading gems...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GemSelectionStep;