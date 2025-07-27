import React, { useState, useEffect } from 'react';
import axios from 'axios';
import NotificationBell from './NotificationBell';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';

const MobileHeader = ({ currentView, setCurrentView, user, onOpenAdminPanel, onLogout, totalBalance }) => {
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [portfolioBalance, setPortfolioBalance] = useState(null);
  const [gems, setGems] = useState([]);
  const [loading, setLoading] = useState(true);

  const API = process.env.REACT_APP_BACKEND_URL;

  const fetchBalance = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/economy/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPortfolioBalance(response.data);
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
    if (!portfolioBalance) return null;
    
    const virtualBalance = portfolioBalance.virtual_balance;
    const frozenBalance = portfolioBalance.frozen_balance;
    const totalGemsCount = gems.reduce((sum, gem) => sum + gem.quantity, 0);
    const frozenGemsCount = gems.reduce((sum, gem) => sum + gem.frozen_quantity, 0);
    const availableGemValue = portfolioBalance.available_gem_value;
    const frozenGemValue = portfolioBalance.total_gem_value - portfolioBalance.available_gem_value;
    const totalValue = virtualBalance + frozenBalance + portfolioBalance.total_gem_value;

    return {
      balance: {
        total: virtualBalance + frozenBalance,
        frozen: frozenBalance,
        available: virtualBalance
      },
      gems: {
        totalCount: totalGemsCount,
        totalValue: portfolioBalance.total_gem_value,
        frozenCount: frozenGemsCount,
        frozenValue: frozenGemValue,
        availableValue: availableGemValue
      },
      total: {
        value: totalValue
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
  
  const profileMenuItems = [
    {
      id: 'profile',
      label: 'Profile',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
    },
    {
      id: 'history',
      label: 'History',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      id: 'admin-panel',
      label: 'Admin',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      adminOnly: true,
    },
  ];

  return (
    <div className="md:hidden bg-surface-sidebar border-b border-border-primary sticky top-0 z-50">
      {/* Balance, Gems, Total tiles row */}
      {portfolioData && !loading && (
        <div className="flex space-x-2 px-4 py-2 border-b border-border-primary">
          {/* Balance Block */}
          <div className="bg-surface-card rounded-lg px-2 py-2 border border-green-500/20 min-w-0 flex-1">
            <div className="text-center">
              <h3 className="font-rajdhani text-xs font-semibold text-white mb-1">Balance</h3>
              <div className="font-rajdhani text-sm font-bold text-green-400 break-words whitespace-nowrap">
                ${formatNumber(portfolioData.balance.total)}
              </div>
              {portfolioData.balance.frozen > 0 && (
                <div className="text-xs text-orange-400">
                  Frozen: ${formatNumber(portfolioData.balance.frozen)}
                </div>
              )}
              <div className="text-xs text-text-secondary">
                ${formatNumber(portfolioData.balance.available)}
              </div>
            </div>
          </div>

          {/* Gems Block */}
          <div className="bg-surface-card rounded-lg px-2 py-2 border border-green-500/20 min-w-0 flex-1">
            <div className="text-center">
              <h3 className="font-rajdhani text-xs font-semibold text-white mb-1">Gems</h3>
              <div className="font-rajdhani text-sm font-bold text-purple-400 break-words whitespace-nowrap">
                {formatNumber(portfolioData.gems.totalCount)}/{formatNumber(portfolioData.gems.totalValue)}
              </div>
              {portfolioData.gems.frozenCount > 0 && (
                <div className="text-xs text-orange-400">
                  Frozen: {formatNumber(portfolioData.gems.frozenCount)}/{formatNumber(portfolioData.gems.frozenValue)}
                </div>
              )}
              <div className="text-xs text-text-secondary">
                ${formatNumber(portfolioData.gems.availableValue)}
              </div>
            </div>
          </div>

          {/* Total Block */}
          <div className="bg-surface-card rounded-lg px-2 py-2 border border-green-500/20 min-w-0 flex-1">
            <div className="text-center">
              <h3 className="font-rajdhani text-xs font-semibold text-white mb-1">Total</h3>
              <div className="font-rajdhani text-sm font-bold text-accent-primary break-words whitespace-nowrap">
                ${formatNumber(portfolioData.total.value)}
              </div>
              <div className="text-xs text-text-secondary">
                ${(() => {
                  const totalFrozen = portfolioData.balance.frozen + portfolioData.gems.frozenValue;
                  const totalAvailable = portfolioData.total.value - totalFrozen;
                  return `${formatNumber(totalAvailable)}`;
                })()}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header content */}
      <div className="flex items-center justify-between px-4 py-3">
        {/* Left side - Notifications Bell and Logo */}
        <div className="flex items-center space-x-3">
          {/* Notifications Bell */}
          <NotificationBell isCollapsed={false} />
          
          <div className="w-17 h-18 flex items-center justify-center">
            <img 
              src="/gems/gem-green.svg" 
              alt="GemPlay" 
              className="w-12 h-12 object-contain"
            />
          </div>
          <span className="font-russo text-3xl text-accent-primary">GemPLAY</span>
        </div>

        {/* Right side - Profile dropdown */}
        <div className="flex items-center space-x-4">
          {/* Profile Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowProfileDropdown(!showProfileDropdown)}
              className="flex items-center space-x-2 px-3 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg hover:border-opacity-50 transition-colors"
            >
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span className="font-rajdhani text-white text-sm">Profile</span>
              <svg 
                className={`w-4 h-4 text-gray-400 transform transition-transform ${showProfileDropdown ? 'rotate-180' : ''}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Dropdown Menu */}
            {showProfileDropdown && (
              <div className="absolute right-0 mt-2 w-48 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg shadow-lg z-50">
                {profileMenuItems.map((item) => {
                  // Show admin items only for admins
                  if (item.adminOnly && (!user || (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN'))) {
                    return null;
                  }

                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        if (item.id === 'admin-panel') {
                          onOpenAdminPanel();
                        } else {
                          setCurrentView(item.id);
                        }
                        setShowProfileDropdown(false);
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 hover:bg-surface-sidebar transition-colors ${
                        currentView === item.id 
                          ? 'bg-accent-primary bg-opacity-20 text-accent-primary'
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      {item.icon}
                      <span className="font-rajdhani font-semibold">{item.label}</span>
                    </button>
                  );
                })}
                
                {/* Divider */}
                <div className="border-t border-border-primary my-1"></div>
                
                {/* User Info */}
                {user && (
                  <div className="px-4 py-3 border-t border-border-primary">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="w-8 h-8 bg-gradient-to-r from-green-600 to-green-700 rounded-full flex items-center justify-center">
                        <img 
                          src={user.gender === 'female' ? '/Women.svg' : '/Men.svg'} 
                          alt="User Avatar" 
                          className="w-11 h-11 object-contain"
                        />
                      </div>
                      <div>
                        <div className="font-rajdhani font-semibold text-white text-sm">{user.username}</div>
                        <div className="text-text-secondary text-xs">
                          Total: ${totalBalance.toFixed(2)}
                        </div>
                      </div>
                    </div>
                    
                    <button
                      onClick={onLogout}
                      className="w-full flex items-center space-x-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      <span className="font-rajdhani font-semibold text-sm">LOGOUT</span>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileHeader;