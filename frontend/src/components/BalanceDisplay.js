import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { formatCurrencyWithSymbol, calculateGemValue } from '../utils/economy';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BalanceDisplay = ({ user, onUpdateBalance }) => {
  const [balance, setBalance] = useState(null);
  const [gems, setGems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      fetchBalanceData();
    }
  }, [user]);

  const fetchBalanceData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // Fetch balance and gems data
      const [balanceResponse, gemsResponse] = await Promise.all([
        axios.get(`${API}/economy/balance`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/gems/inventory`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      setBalance(balanceResponse.data);
      setGems(gemsResponse.data);
      
      if (onUpdateBalance) {
        onUpdateBalance(balanceResponse.data);
      }
    } catch (error) {
      console.error('Error fetching balance data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!user || loading) {
    return (
      <div className="flex items-center space-x-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-600 rounded w-20 mb-1"></div>
          <div className="h-3 bg-gray-700 rounded w-16"></div>
        </div>
      </div>
    );
  }

  if (!balance) {
    return null;
  }

  const virtualBalance = balance.virtual_balance || 0;
  const frozenBalance = balance.frozen_balance || 0;
  const availableBalance = virtualBalance - frozenBalance;
  const totalGemsValue = calculateGemValue(gems, false);
  const availableGemsValue = calculateGemValue(gems, true);
  const totalWorth = virtualBalance + totalGemsValue;

  return (
    <div className="flex items-center space-x-6">
      {/* Virtual Balance */}
      <div className="text-right">
        <div className="flex items-center space-x-2">
          <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
          </svg>
          <span className="font-rajdhani text-sm text-text-secondary">Balance</span>
        </div>
        <div className="font-rajdhani text-lg font-bold text-green-400">
          {formatCurrencyWithSymbol(availableBalance)}
        </div>
        {frozenBalance > 0 && (
          <div className="font-roboto text-xs text-warning">
            {formatCurrencyWithSymbol(frozenBalance)} frozen
          </div>
        )}
      </div>

      {/* Gems Value */}
      <div className="text-right">
        <div className="flex items-center space-x-2">
          <svg className="w-4 h-4 text-purple-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6,2L2,8L12,22L22,8L18,2H6M6.5,3H17.5L20.5,8L12,19L3.5,8L6.5,3Z" />
          </svg>
          <span className="font-rajdhani text-sm text-text-secondary">Gems</span>
        </div>
        <div className="font-rajdhani text-lg font-bold text-purple-400">
          {formatCurrencyWithSymbol(availableGemsValue, false)} / {formatCurrencyWithSymbol(totalGemsValue, false)}
        </div>
      </div>

      {/* Total Worth */}
      <div className="text-right">
        <div className="flex items-center space-x-2">
          <svg className="w-4 h-4 text-accent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span className="font-rajdhani text-sm text-text-secondary">Total</span>
        </div>
        <div className="font-rajdhani text-lg font-bold text-accent-primary">
          {formatCurrencyWithSymbol(totalWorth)}
        </div>
      </div>

      {/* Refresh Button */}
      <button
        onClick={fetchBalanceData}
        disabled={loading}
        className="p-2 text-text-secondary hover:text-white transition-colors duration-200"
        title="Refresh balance"
      >
        <svg 
          className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
          />
        </svg>
      </button>
    </div>
  );
};

export default BalanceDisplay;