import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';
import SoundSettings from './SoundSettings';
import { useSound } from '../hooks/useSound';

const HeaderPortfolio = ({ user }) => {
  const [balance, setBalance] = useState(null);
  const [gems, setGems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showSoundSettings, setShowSoundSettings] = useState(false);
  
  const { ui, settings } = useSound();

  const API = process.env.REACT_APP_BACKEND_URL;

  const fetchBalance = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/economy/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBalance(response.data);
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  const fetchGems = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/gems/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGems(response.data || []);
    } catch (error) {
      console.error('Error fetching gems:', error);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([fetchBalance(), fetchGems()]);
    setLoading(false);
  };

  useEffect(() => {
    if (user?.id) {
      fetchData();
      
      // Subscribe to global updates
      const globalRefresh = getGlobalLobbyRefresh();
      const unregister = globalRefresh.registerRefreshCallback(() => {
        fetchData();
      });
      
      return () => {
        unregister();
      };
    }
  }, [user?.id]);

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

  if (loading || !portfolioData) {
    return (
      <div className="flex space-x-3">
        <div className="w-24 h-12 bg-gray-700 rounded animate-pulse"></div>
        <div className="w-24 h-12 bg-gray-700 rounded animate-pulse"></div>
        <div className="w-24 h-12 bg-gray-700 rounded animate-pulse"></div>
      </div>
    );
  }

  return (
    <>
      <div className="flex space-x-1 sm:space-x-2 md:space-x-4 overflow-x-auto">
      {/* Balance Block - Mobile and Desktop */}
      <div className="bg-surface-card rounded-lg px-2 py-2 md:px-3 md:py-2 border border-green-500/20 hover:border-green-500/40 transition-colors duration-200 min-w-0 flex-1 md:flex-shrink-0 shadow-sm">
        <div className="text-center">
          <h3 className="font-rajdhani text-xs md:text-sm font-semibold text-white mb-1 md:block hidden">Balance</h3>
          <div className="font-rajdhani text-xs sm:text-sm md:text-lg font-bold text-green-400 break-words whitespace-nowrap">
            ${formatNumber(portfolioData.balance.total)}
          </div>
          {portfolioData.balance.frozen > 0 && (
            <div className="text-xs text-orange-400 block md:block">
              Frozen: ${formatNumber(portfolioData.balance.frozen)}
            </div>
          )}
          <div className="text-xs text-text-secondary block md:block">
            ${formatNumber(portfolioData.balance.available)}
          </div>
        </div>
      </div>

      {/* Gems Block - Mobile and Desktop */}
      <div className="bg-surface-card rounded-lg px-2 py-2 md:px-3 md:py-2 border border-green-500/20 hover:border-green-500/40 transition-colors duration-200 min-w-0 flex-1 md:flex-shrink-0 shadow-sm">
        <div className="text-center">
          <h3 className="font-rajdhani text-xs md:text-sm font-semibold text-white mb-1 md:block hidden">Gems</h3>
          <div className="font-rajdhani text-xs sm:text-sm md:text-lg font-bold text-purple-400 break-words whitespace-nowrap">
            {formatNumber(portfolioData.gems.totalCount)}/{formatNumber(portfolioData.gems.totalValue)}
          </div>
          {portfolioData.gems.frozenCount > 0 && (
            <div className="text-xs text-orange-400 block md:block">
              Frozen: {formatNumber(portfolioData.gems.frozenCount)}/{formatNumber(portfolioData.gems.frozenValue)}
            </div>
          )}
          <div className="text-xs text-text-secondary block md:block">
            ${formatNumber(portfolioData.gems.availableValue)}
          </div>
        </div>
      </div>

      {/* Total Block - Mobile and Desktop */}
      <div className="bg-surface-card rounded-lg px-2 py-2 md:px-3 md:py-2 border border-green-500/20 hover:border-green-500/40 transition-colors duration-200 min-w-0 flex-1 md:flex-shrink-0 shadow-sm">
        <div className="text-center">
          <h3 className="font-rajdhani text-xs md:text-sm font-semibold text-white mb-1 md:block hidden">Total</h3>
          <div className="font-rajdhani text-xs sm:text-sm md:text-lg font-bold text-accent-primary break-words whitespace-nowrap">
            ${formatNumber(portfolioData.total.value)}
          </div>
          <div className="text-xs text-text-secondary block md:block">
            ${(() => {
              const totalFrozen = portfolioData.balance.frozen + portfolioData.gems.frozenValue;
              const totalAvailable = portfolioData.total.value - totalFrozen;
              
              return `${formatNumber(totalAvailable)}`;
            })()}
          </div>
        </div>
      </div>

      {/* Sound Settings Button - Hidden on mobile */}
      <div className="bg-surface-card rounded-lg px-2 py-2 md:px-3 md:py-2 border border-blue-500/20 hover:border-blue-500/40 transition-colors duration-200 min-w-0 flex-shrink-0 shadow-sm hidden md:block">
        <button
          onClick={() => {
            ui.modalOpen();
            setShowSoundSettings(true);
          }}
          onMouseEnter={() => ui.hover()}
          className="text-center w-full h-full flex flex-col items-center justify-center"
          title="Настройки звука"
        >
          <div className="text-lg mb-1">
            {settings.isEnabled() ? '🔊' : '🔇'}
          </div>
          <div className="text-xs text-text-secondary hidden md:block">
            Sound
          </div>
        </button>
      </div>
      </div>

      {/* Sound Settings Modal */}
      <SoundSettings 
        isOpen={showSoundSettings} 
        onClose={() => {
          ui.modalClose();
          setShowSoundSettings(false);
        }} 
      />
    </>
  );
};

export default HeaderPortfolio;