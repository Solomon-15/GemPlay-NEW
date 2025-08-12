import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useGems } from './GemsContext';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';
import { useNotifications } from './NotificationContext';
import { formatGemValue } from '../utils/economy';
import GiftConfirmationModal from './GiftConfirmationModal';
import Loader from './Loader';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Inventory = ({ user, onUpdateUser }) => {
  const { getGemIconPath } = useGems();
  const { showSuccess, showError } = useNotifications();
  const [gems, setGems] = useState([]);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sellingGem, setSellingGem] = useState(null);
  const [quantities, setQuantities] = useState({});
  const [tooltipVisible, setTooltipVisible] = useState(null);
  
  // Gift modal state
  const [showGiftModal, setShowGiftModal] = useState(false);
  const [selectedGemForGift, setSelectedGemForGift] = useState(null);

  useEffect(() => {
    fetchInventory();
    fetchBalance();
    
    // Set up real-time updates
    const interval = setInterval(() => {
      fetchBalance();
      fetchInventory();
    }, 10000); // Update every 10 seconds
    
    return () => clearInterval(interval);
  }, []);

  const fetchInventory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/gems/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGems(response.data);
    } catch (error) {
      console.error('Error fetching inventory:', error);
    }
  };

  const fetchBalance = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/economy/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBalance(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching balance:', error);
      setLoading(false);
    }
  };

  const handleQuantityChange = (gemType, quantity, maxQuantity) => {
    setQuantities(prev => ({
      ...prev,
      [gemType]: Math.max(1, Math.min(maxQuantity, parseInt(quantity) || 1))
    }));
  };

  const handleSellGem = async (gemType) => {
    const gem = gems.find(g => g.type === gemType);
    const quantity = quantities[gemType] || 1;
    const availableQuantity = gem.quantity - gem.frozen_quantity;
    
    if (quantity > availableQuantity) {
      showError('Cannot sell more gems than available');
      return;
    }

    setSellingGem(gemType);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/gems/sell?gem_type=${gemType}&quantity=${quantity}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const totalValue = formatGemValue(gem.price * quantity);
      const gemDisplayName = gemType === 'Ruby' ? 'Rubies' : 
                            gemType === 'Emerald' ? 'Emeralds' :
                            gemType === 'Sapphire' ? 'Sapphires' :
                            gemType === 'Aquamarine' ? 'Aquamarines' :
                            gemType === 'Topaz' ? 'Topazes' :
                            gemType === 'Amber' ? 'Ambers' :
                            gemType === 'Magic' ? 'Magic gems' : `${gemType}s`;
      
      const finalGemName = quantity === 1 ? gemType : gemDisplayName;
      showSuccess(`✅ You sold ${quantity} ${finalGemName} for $${totalValue}`);
      
      await fetchInventory();
      await fetchBalance();
      
      const globalRefresh = getGlobalLobbyRefresh();
      globalRefresh.triggerLobbyRefresh();
      console.log(`💰 Sold ${quantity} ${gemType} gems - triggering lobby refresh`);
      
      if (onUpdateUser) {
        onUpdateUser();
      }
    } catch (error) {
      showError(error.response?.data?.detail || 'Error selling gems');
    } finally {
      setSellingGem(null);
    }
  };

  const handleGiftGem = (gemType) => {
    const gem = gems.find(g => g.type === gemType);
    const quantity = quantities[gemType] || 1;
    const availableQuantity = gem.quantity - gem.frozen_quantity;
    
    if (quantity > availableQuantity) {
      showError('Cannot gift more gems than available');
      return;
    }

    setSelectedGemForGift({
      gemType,
      quantity,
      gemPrice: gem.price,
      availableQuantity
    });
    setShowGiftModal(true);
  };

  const handleGiftSuccess = async () => {
    await fetchInventory();
    await fetchBalance();
    
    if (onUpdateUser) {
      onUpdateUser();
    }
  };

  // Calculate portfolio data
  const getPortfolioData = () => {
    if (!balance) return null;
    
    const virtualBalance = balance.virtual_balance;
    const frozenBalance = balance.frozen_balance;
    const totalGemsCount = gems.reduce((sum, gem) => sum + gem.quantity, 0);
    const frozenGemsCount = gems.reduce((sum, gem) => sum + gem.frozen_quantity, 0);
    const availableGemValue = balance.available_gem_value;
    const frozenGemValue = balance.total_gem_value - balance.available_gem_value;
    const totalValue = virtualBalance + frozenBalance + balance.total_gem_value;

    return {
      balance: {
        total: virtualBalance + frozenBalance,  // Полный баланс = virtual + frozen
        frozen: frozenBalance,
        available: virtualBalance  // Доступный баланс = virtual_balance
      },
      gems: {
        totalCount: totalGemsCount,
        totalValue: balance.total_gem_value,
        frozenCount: frozenGemsCount,
        frozenValue: frozenGemValue,
        availableValue: availableGemValue
      },
      total: {
        value: totalValue  // virtual_balance + frozen_balance + total_gem_value
      }
    };
  };

  const portfolioData = getPortfolioData();

  // Format numbers with commas
  const formatNumber = (number) => {
    return number.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    });
  };

  const InfoTooltip = ({ id, tooltip, children }) => {
    const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
    
    const handleMouseEnter = (e) => {
      const rect = e.currentTarget.getBoundingClientRect();
      setTooltipPosition({
        top: rect.top - 10,
        left: rect.left + rect.width / 2 - 140 // Center the tooltip
      });
      setTooltipVisible(id);
    };
    
    return (
      <div className="relative">
        {children}
        <button
          onMouseEnter={handleMouseEnter}
          onMouseLeave={() => setTooltipVisible(null)}
          onClick={handleMouseEnter}
          className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-gray-600 text-white text-xs flex items-center justify-center hover:bg-gray-500 transition-colors z-20"
        >
          i
        </button>
        {tooltipVisible === id && (
          <div 
            className="fixed w-64 bg-slate-800 text-white text-sm rounded-lg p-3 shadow-xl border border-slate-700 z-[99999]"
            style={{
              top: `${tooltipPosition.top}px`,
              left: `${tooltipPosition.left}px`,
              maxWidth: '280px',
              transform: 'translateY(-100%)'
            }}
          >
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-800"></div>
            {tooltip}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen min-h-app bg-gradient-primary flex items-center justify-center">
        <Loader ariaLabel="Loading Inventory" />
      </div>
    );
  }

  return (
    <div className="min-h-screen min-h-app bg-gradient-primary p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-4xl md:text-6xl text-accent-primary mb-4">
          My Inventory
        </h1>
        <p className="font-roboto text-xl text-text-secondary mb-8">
          Manage Your NFT Gem Collection
        </p>
        
        {/* Three Portfolio Blocks - Balance, Gems, and Total */}
        {portfolioData && (
          <div className="max-w-6xl mx-auto mb-8">
            <div className="grid grid-cols-3 gap-4 md:gap-6 min-w-0 overflow-x-auto">
              {/* Unified Balance Block */}
              <div className="relative bg-surface-card rounded-lg p-3 md:p-4 border border-border-primary min-w-0 flex-shrink-0 hover:border-green-500 transition-colors duration-200">
                <InfoTooltip 
                  id="balance" 
                  tooltip="Your virtual dollar balance. Shows total balance, frozen funds (reserved for active bets), and available amount for new bets."
                >
                  <div className="text-center pt-2">
                    <h3 className="font-rajdhani text-sm md:text-lg font-semibold text-white mb-2 md:mb-3">Balance</h3>
                    
                    <div className="mb-1 md:mb-2">
                      <div className="font-rajdhani text-lg md:text-2xl font-bold text-green-400 break-words">
                        ${formatNumber(portfolioData.balance.total)}
                      </div>
                    </div>
                    
                    {portfolioData.balance.frozen > 0 && (
                      <div className="text-xs text-orange-400 mb-1">
                        Frozen: ${formatNumber(portfolioData.balance.frozen)}
                      </div>
                    )}
                    
                    <div className="text-xs text-text-secondary">
                      Available: ${formatNumber(portfolioData.balance.available)}
                    </div>
                  </div>
                </InfoTooltip>
              </div>

              {/* Gems Block */}
              <div className="relative bg-surface-card rounded-lg p-3 md:p-4 border border-border-primary min-w-0 flex-shrink-0 hover:border-purple-500 transition-colors duration-200">
                <InfoTooltip 
                  id="gems" 
                  tooltip="Your gem collection. Gems are used to create and accept bets. Higher value gems allow for larger bets."
                >
                  <div className="text-center pt-2">
                    <h3 className="font-rajdhani text-sm md:text-lg font-semibold text-white mb-2 md:mb-3">Gems</h3>
                    
                    <div className="mb-1 md:mb-2">
                      <div className="font-rajdhani text-lg md:text-2xl font-bold text-purple-400 break-words">
                        {formatNumber(portfolioData.gems.totalCount)}/{formatNumber(portfolioData.gems.totalValue)}
                      </div>
                    </div>
                    
                    {portfolioData.gems.frozenCount > 0 && (
                      <div className="text-xs text-orange-400 mb-1">
                        Frozen: {formatNumber(portfolioData.gems.frozenCount)} / ${formatNumber(portfolioData.gems.frozenValue)}
                      </div>
                    )}
                    
                    <div className="text-xs text-text-secondary">
                      Available: ${formatNumber(portfolioData.gems.availableValue)}
                    </div>
                  </div>
                </InfoTooltip>
              </div>

              {/* Total Block */}
              <div className="relative bg-surface-card rounded-lg p-3 md:p-4 border border-border-primary min-w-0 flex-shrink-0 hover:border-accent-primary transition-colors duration-200">
                <InfoTooltip 
                  id="total" 
                  tooltip="Your total estimated value including both balance and gems."
                >
                  <div className="text-center pt-2">
                    <h3 className="font-rajdhani text-sm md:text-lg font-semibold text-white mb-2 md:mb-3">Total</h3>
                    
                    <div className="mb-1 md:mb-2">
                      <div className="font-rajdhani text-lg md:text-2xl font-bold text-accent-primary break-words">
                        ${formatNumber(portfolioData.total.value)}
                      </div>
                    </div>
                    
                    <div className="text-xs text-text-secondary">
                      {(() => {
                        const totalFrozen = portfolioData.balance.frozen + portfolioData.gems.frozenValue;
                        const totalAvailable = portfolioData.total.value - totalFrozen;
                        
                        if (totalFrozen > 0) {
                          return `${formatNumber(totalAvailable)} available`;
                        } else {
                          return 'All available';
                        }
                      })()}
                    </div>
                  </div>
                </InfoTooltip>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Gems Grid */}
      <div className="max-w-7xl mx-auto">
        {gems.length === 0 ? (
          <div className="text-center py-16">
            <h3 className="font-russo text-2xl text-text-secondary mb-4">No Gems Yet</h3>
            <p className="font-roboto text-text-muted">Visit the Shop to buy your first gems!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
            {gems.map((gem, index) => {
              const quantity = quantities[gem.type] || 1;
              const availableQuantity = gem.quantity - gem.frozen_quantity;
              const totalValue = gem.price * quantity;
              
              return (
                <div
                  key={index}
                  className="rounded-xl p-6 transition-all duration-300 hover:scale-105 hover:shadow-2xl group"
                  style={{
                    backgroundColor: '#081730',
                    border: `1px solid ${gem.color}`,
                    boxShadow: `0 0 20px ${gem.color}40`
                  }}
                >
                  {/* Gem Icon */}
                  <div className="flex justify-center mb-4">
                    <div className="w-24 h-24 flex items-center justify-center relative transition-all duration-300 group-hover:scale-110">
                      <div 
                        className="absolute inset-0 animate-pulse transition-all duration-300 group-hover:scale-125"
                        style={{
                          background: `radial-gradient(circle, ${gem.color}40, transparent 70%)`,
                          filter: 'blur(8px)',
                          transform: 'scale(1.2)'
                        }}
                      ></div>
                      
                      <img
                        src={getGemIconPath(gem.type)}
                        alt={gem.name}
                        className="w-20 h-20 object-contain drop-shadow-lg relative z-10 transition-all duration-300 group-hover:scale-110 group-hover:brightness-125"
                        style={{
                          filter: `drop-shadow(0 0 10px ${gem.color}40)`
                        }}
                      />
                    </div>
                  </div>
                  
                  {/* Gem Info */}
                  <div className="text-center">
                    <h3 className="font-russo text-xl text-white mb-2">
                      {gem.name}
                    </h3>
                    
                    {/* Quantity Display */}
                    <div className="mb-3">
                      <span className="font-rajdhani text-lg text-white">
                        {gem.quantity}
                      </span>
                      <span className="font-roboto text-text-secondary text-sm"> owned</span>
                      {gem.frozen_quantity > 0 && (
                        <div className="font-roboto text-warning text-sm font-bold">
                          {gem.frozen_quantity} frozen in bets
                        </div>
                      )}
                    </div>
                    
                    {/* Price */}
                    <div className="mb-4">
                      <span className="font-rajdhani text-xl font-bold text-green-400">
                        ${gem.price}
                      </span>
                      <span className="font-roboto text-text-secondary text-sm"> each</span>
                    </div>
                    
                    {/* Quantity Selector */}
                    <div className="mb-4">
                      <label className="font-roboto text-text-secondary text-xs block mb-2">
                        Quantity to sell/gift:
                      </label>
                      <input
                        type="number"
                        min="1"
                        max={availableQuantity}
                        value={quantity}
                        onChange={(e) => handleQuantityChange(gem.type, e.target.value, availableQuantity)}
                        className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-rajdhani text-center text-sm"
                        disabled={availableQuantity === 0}
                      />
                    </div>
                    
                    {/* Total Value */}
                    <div className="mb-4">
                      <span className="font-roboto text-text-secondary text-sm">Value: </span>
                      <span className="font-rajdhani text-lg font-bold text-green-400">
                        {formatGemValue(totalValue)}
                      </span>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="space-y-2">
                      <button 
                        onClick={() => handleSellGem(gem.type)}
                        disabled={availableQuantity === 0 || sellingGem === gem.type}
                        className={`w-full py-2 px-4 rounded-lg font-rajdhani font-bold text-sm transition-all duration-300 uppercase tracking-wider ${
                          availableQuantity > 0 && sellingGem !== gem.type
                            ? 'text-white hover:scale-105'
                            : 'text-gray-500 cursor-not-allowed'
                        }`}
                        style={{
                          backgroundColor: 'transparent',
                          border: `1px solid ${availableQuantity > 0 ? '#ff6b35' : '#666'}`,
                          color: availableQuantity > 0 ? '#ff6b35' : '#666'
                        }}
                      >
                        {sellingGem === gem.type ? 'SELLING...' : 'SELL'}
                      </button>
                      
                      <button 
                        onClick={() => handleGiftGem(gem.type)}
                        disabled={availableQuantity === 0}
                        className={`w-full py-2 px-4 rounded-lg font-rajdhani font-bold text-sm transition-all duration-300 uppercase tracking-wider ${
                          availableQuantity > 0
                            ? 'text-white hover:scale-105'
                            : 'text-gray-500 cursor-not-allowed'
                        }`}
                        style={{
                          backgroundColor: 'transparent',
                          border: `1px solid ${availableQuantity > 0 ? '#23d364' : '#666'}`,
                          color: availableQuantity > 0 ? '#23d364' : '#666'
                        }}
                      >
                        GIFT
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Gift Confirmation Modal */}
      <GiftConfirmationModal
        isOpen={showGiftModal}
        onClose={() => setShowGiftModal(false)}
        gemType={selectedGemForGift?.gemType}
        quantity={selectedGemForGift?.quantity}
        gemPrice={selectedGemForGift?.gemPrice}
        senderName={user?.username}
        senderEmail={user?.email}
        onGiftSuccess={handleGiftSuccess}
      />
    </div>
  );
};

export default Inventory;