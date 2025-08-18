import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { formatCurrencyWithSymbol, formatDollarAmount, formatGemValue } from '../utils/economy';
import { useNotifications } from './NotificationContext';
import { useGems } from './GemsContext';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';
import GemsHeader from './GemsHeader';
import { useSound, useHoverSound } from '../hooks/useSound';
import Loader from './Loader';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Shop = ({ user, onUpdateUser }) => {
  const { showSuccess, showError } = useNotifications();
  const { getGemIconPath, refreshInventory } = useGems();
  const { gem, ui, system } = useSound();
  const hoverProps = useHoverSound(true);
  const [gems, setGems] = useState([]);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [buyingGem, setBuyingGem] = useState(null);
  const [quantities, setQuantities] = useState({});
  const [showDelayedLoader, setShowDelayedLoader] = useState(false);
  const loaderTimerRef = useRef(null);

  useEffect(() => {
    fetchGems();
    fetchBalance();
  }, []);

  useEffect(() => {
    if (loading) {
      loaderTimerRef.current = setTimeout(() => setShowDelayedLoader(true), 1000);
    } else {
      clearTimeout(loaderTimerRef.current);
      setShowDelayedLoader(false);
    }
    return () => clearTimeout(loaderTimerRef.current);
  }, [loading]);

  const fetchGems = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/gems/definitions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGems(response.data);
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
      setLoading(false);
    } catch (error) {
      console.error('Error fetching balance:', error);
      setLoading(false);
    }
  };

  const handleQuantityChange = (gemType, quantity, gemPrice) => {
    // Рассчитываем максимальное количество, которое можно купить
    const maxAffordable = balance ? Math.floor(balance.virtual_balance / gemPrice) : 0;
    const numQuantity = parseInt(quantity) || 0;
    const validQuantity = Math.max(1, Math.min(maxAffordable, numQuantity));
    
    setQuantities(prev => ({
      ...prev,
      [gemType]: validQuantity
    }));
  };

  const handleBuyGem = async (gemType) => {
    const quantity = quantities[gemType] || 1;
    setBuyingGem(gemType);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/gems/buy?gem_type=${gemType}&quantity=${quantity}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      gem.buy();
      
      showSuccess(`Successfully purchased ${quantity} ${gemType} gem${quantity > 1 ? 's' : ''}!`);
      await fetchBalance();
      
      await refreshInventory();
      
      const globalRefresh = getGlobalLobbyRefresh();
      globalRefresh.triggerLobbyRefresh();
      console.log(`💎 Bought ${quantity} ${gemType} gems - triggering lobby refresh`);
      
      if (onUpdateUser) {
        onUpdateUser();
      }
    } catch (error) {
      ui.error();
      
      const errorMessage = error.response?.data?.detail || 'Error buying gems. Please try again.';
      showError(errorMessage);
    } finally {
      setBuyingGem(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen min-h-app bg-gradient-primary flex items-center justify-center">
        {showDelayedLoader ? <Loader ariaLabel="Loading Shop" /> : null}
      </div>
    );
  }

  return (
    <div className="min-h-screen min-h-app bg-gradient-primary p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-4xl md:text-6xl text-accent-primary mb-4">
          Gem Shop
        </h1>
        <p className="font-roboto text-xl text-text-secondary">
          Purchase NFT Gems with Virtual Dollars
        </p>
      </div>

      {/* Current Gems Inventory - Identical to Lobby */}
      <GemsHeader user={user} />

      {/* Gems Grid */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {gems.map((gem, index) => {
            const quantity = quantities[gem.type] || 1;
            const totalCost = gem.price * quantity;
            const canAfford = balance && balance.virtual_balance >= totalCost;
            
            return (
              <div
                key={index}
                className="rounded-xl p-6 transition-all duration-300 hover:scale-105 hover:shadow-2xl group cursor-pointer"
                style={{
                  backgroundColor: '#081730',
                  border: `1px solid ${gem.color}`,
                  boxShadow: `0 0 20px ${gem.color}40`
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.border = `2px solid #23d364`;
                  e.currentTarget.style.boxShadow = `0 0 30px #23d36440, 0 0 20px ${gem.color}60`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.border = `1px solid ${gem.color}`;
                  e.currentTarget.style.boxShadow = `0 0 20px ${gem.color}40`;
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
                  <h3 className="font-russo text-xl text-white mb-2 transition-all duration-300 group-hover:text-green-400">
                    {gem.name}
                  </h3>
                  
                  <p className="font-roboto text-text-secondary text-sm mb-3">
                    {gem.rarity}
                  </p>
                  
                  {/* Price */}
                  <div className="mb-4">
                    <span className="font-rajdhani text-2xl font-bold text-green-400">
                      {formatDollarAmount(gem.price)}
                    </span>
                    <span className="font-roboto text-text-secondary text-sm"> each</span>
                  </div>
                  
                  {/* Quantity Selector */}
                  <div className="mb-4">
                    <label className="font-roboto text-text-secondary text-sm block mb-2">
                      Quantity:
                    </label>
                    <div className="flex items-center justify-center space-x-2">
                      <button
                        onClick={() => handleQuantityChange(gem.type, quantity - 1, gem.price)}
                        disabled={quantity <= 1}
                        className={`w-8 h-8 rounded-lg font-rajdhani font-bold text-lg transition-all duration-200 ${
                          quantity > 1
                            ? 'bg-surface-sidebar border border-accent-primary border-opacity-30 text-white hover:bg-surface-hover hover:border-opacity-60'
                            : 'bg-surface-sidebar border border-gray-700 text-gray-600 cursor-not-allowed'
                        }`}
                      >
                        -
                      </button>
                      
                      <input
                        type="number"
                        min="1"
                        max={balance ? Math.floor(balance.virtual_balance / gem.price) : 0}
                        value={quantity}
                        onChange={(e) => handleQuantityChange(gem.type, e.target.value, gem.price)}
                        onBlur={(e) => {
                          // При потере фокуса корректируем значение
                          const maxAffordable = balance ? Math.floor(balance.virtual_balance / gem.price) : 0;
                          const value = parseInt(e.target.value) || 1;
                          if (value > maxAffordable) {
                            handleQuantityChange(gem.type, maxAffordable, gem.price);
                          } else if (value < 1) {
                            handleQuantityChange(gem.type, 1, gem.price);
                          }
                        }}
                        className="w-20 px-3 py-2 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-white font-rajdhani text-center"
                      />
                      
                      <button
                        onClick={() => handleQuantityChange(gem.type, quantity + 1, gem.price)}
                        disabled={!balance || quantity >= Math.floor(balance.virtual_balance / gem.price)}
                        className={`w-8 h-8 rounded-lg font-rajdhani font-bold text-lg transition-all duration-200 ${
                          balance && quantity < Math.floor(balance.virtual_balance / gem.price)
                            ? 'bg-surface-sidebar border border-accent-primary border-opacity-30 text-white hover:bg-surface-hover hover:border-opacity-60'
                            : 'bg-surface-sidebar border border-gray-700 text-gray-600 cursor-not-allowed'
                        }`}
                      >
                        +
                      </button>
                    </div>
                    {balance && quantity >= Math.floor(balance.virtual_balance / gem.price) && (
                      <p className="text-xs text-warning mt-1">Max affordable quantity</p>
                    )}
                  </div>
                  
                  {/* Total Cost */}
                  <div className="mb-4">
                    <span className="font-roboto text-text-secondary text-sm">Total: </span>
                    <span className={`font-rajdhani text-xl font-bold ${canAfford ? 'text-green-400' : 'text-red-400'}`}>
                      {formatDollarAmount(totalCost)}
                    </span>
                  </div>
                  
                  {/* Buy Button */}
                  <button 
                    onClick={() => handleBuyGem(gem.type)}
                    disabled={!canAfford || buyingGem === gem.type}
                    {...hoverProps}
                    className={`w-full py-3 px-6 rounded-lg font-rajdhani font-bold text-lg transition-all duration-300 uppercase tracking-wider ${
                      canAfford && buyingGem !== gem.type
                        ? 'text-white hover:scale-105'
                        : 'text-gray-500 cursor-not-allowed'
                    }`}
                    style={{
                      backgroundColor: 'transparent',
                      border: `1px solid ${canAfford ? gem.color : '#666'}`,
                      color: canAfford ? gem.color : '#666',
                      boxShadow: canAfford ? `0 0 15px ${gem.color}30` : 'none'
                    }}
                  >
                    {buyingGem === gem.type ? 'BUYING...' : 'BUY'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Shop;