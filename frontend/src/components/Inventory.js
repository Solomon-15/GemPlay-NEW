import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Inventory = ({ user, onUpdateUser }) => {
  const [gems, setGems] = useState([]);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sellingGem, setSellingGem] = useState(null);
  const [giftingGem, setGiftingGem] = useState(null);
  const [quantities, setQuantities] = useState({});
  const [recipientEmail, setRecipientEmail] = useState('');

  useEffect(() => {
    fetchInventory();
    fetchBalance();
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
      alert('Cannot sell more gems than available');
      return;
    }

    setSellingGem(gemType);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/gems/sell`, {
        gem_type: gemType,
        quantity: quantity
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert(response.data.message);
      await fetchInventory();
      await fetchBalance();
      
      if (onUpdateUser) {
        onUpdateUser();
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'Error selling gems');
    } finally {
      setSellingGem(null);
    }
  };

  const handleGiftGem = async (gemType) => {
    if (!recipientEmail.trim()) {
      alert('Please enter recipient email');
      return;
    }

    const gem = gems.find(g => g.type === gemType);
    const quantity = quantities[gemType] || 1;
    const availableQuantity = gem.quantity - gem.frozen_quantity;
    
    if (quantity > availableQuantity) {
      alert('Cannot gift more gems than available');
      return;
    }

    setGiftingGem(gemType);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/gems/gift`, {
        recipient_email: recipientEmail,
        gem_type: gemType,
        quantity: quantity
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert(response.data.message);
      setRecipientEmail('');
      await fetchInventory();
      await fetchBalance();
      
      if (onUpdateUser) {
        onUpdateUser();
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'Error gifting gems');
    } finally {
      setGiftingGem(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Loading Inventory...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-primary p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-4xl md:text-6xl text-accent-primary mb-4">
          My Inventory
        </h1>
        <p className="font-roboto text-xl text-text-secondary">
          Manage Your NFT Gem Collection
        </p>
      </div>

      {/* Balance Display */}
      {balance && (
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-surface-card border border-border-primary rounded-lg p-6">
            <h2 className="font-russo text-2xl text-accent-secondary mb-4">Portfolio Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="font-roboto text-text-secondary">Virtual Dollars</p>
                <p className="font-rajdhani text-2xl font-bold text-green-400">
                  ${balance.virtual_balance.toFixed(2)}
                </p>
              </div>
              <div className="text-center">
                <p className="font-roboto text-text-secondary">Available Gems</p>
                <p className="font-rajdhani text-2xl font-bold text-accent-primary">
                  ${balance.available_gem_value.toFixed(2)}
                </p>
              </div>
              <div className="text-center">
                <p className="font-roboto text-text-secondary">Frozen in Bets</p>
                <p className="font-rajdhani text-2xl font-bold text-warning">
                  ${(balance.total_gem_value - balance.available_gem_value).toFixed(2)}
                </p>
              </div>
              <div className="text-center">
                <p className="font-roboto text-text-secondary">Total Worth</p>
                <p className="font-rajdhani text-2xl font-bold text-white">
                  ${balance.total_value.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

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
                        src={`/gems/${gem.icon}`}
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
                        ${totalValue.toFixed(2)}
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
                        disabled={availableQuantity === 0 || giftingGem === gem.type}
                        className={`w-full py-2 px-4 rounded-lg font-rajdhani font-bold text-sm transition-all duration-300 uppercase tracking-wider ${
                          availableQuantity > 0 && giftingGem !== gem.type
                            ? 'text-white hover:scale-105'
                            : 'text-gray-500 cursor-not-allowed'
                        }`}
                        style={{
                          backgroundColor: 'transparent',
                          border: `1px solid ${availableQuantity > 0 ? '#23d364' : '#666'}`,
                          color: availableQuantity > 0 ? '#23d364' : '#666'
                        }}
                      >
                        {giftingGem === gem.type ? 'GIFTING...' : 'GIFT'}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Gift Modal */}
      {giftingGem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-border-primary rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="font-russo text-xl text-white mb-4">Gift Gems</h3>
            <div className="mb-4">
              <label className="font-roboto text-text-secondary text-sm block mb-2">
                Recipient Email:
              </label>
              <input
                type="email"
                value={recipientEmail}
                onChange={(e) => setRecipientEmail(e.target.value)}
                className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                placeholder="Enter email address"
              />
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setGiftingGem(null)}
                className="flex-1 py-2 px-4 bg-gray-600 text-white rounded-lg font-rajdhani font-bold hover:bg-gray-700 transition-colors"
              >
                CANCEL
              </button>
              <button
                onClick={() => handleGiftGem(giftingGem)}
                disabled={!recipientEmail.trim()}
                className="flex-1 py-2 px-4 bg-accent-primary text-white rounded-lg font-rajdhani font-bold hover:bg-accent-secondary transition-colors disabled:bg-gray-600 disabled:cursor-not-allowed"
              >
                SEND GIFT
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;