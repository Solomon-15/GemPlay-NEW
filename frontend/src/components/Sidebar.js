import React, { useState, useEffect } from 'react';
import NotificationBell from './NotificationBell';
import axios from 'axios';

const Sidebar = ({ currentView, setCurrentView, user, isCollapsed, setIsCollapsed, onOpenAdminPanel, onLogout }) => {
  const [totalBalance, setTotalBalance] = useState(0);
  const API = process.env.REACT_APP_BACKEND_URL;

  // Функция для получения общего баланса (Total)
  const fetchTotalBalance = async () => {
    try {
      if (!user) return;
      
      const token = localStorage.getItem('token');
      
      // Получаем баланс
      const balanceResponse = await axios.get(`${API}/api/economy/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const balance = balanceResponse.data;
      
      // Вычисляем Total = virtual_balance + frozen_balance + total_gem_value
      const total = (balance.virtual_balance || 0) + (balance.frozen_balance || 0) + (balance.total_gem_value || 0);
      setTotalBalance(total);
      
    } catch (error) {
      console.error('Error fetching total balance:', error);
      setTotalBalance(0);
    }
  };

  // Загружаем Total при монтировании и изменении пользователя
  useEffect(() => {
    if (user) {
      fetchTotalBalance();
    }
  }, [user]);

  // Обновляем Total каждые 10 секунд
  useEffect(() => {
    if (!user) return;
    
    const interval = setInterval(fetchTotalBalance, 10000);
    return () => clearInterval(interval);
  }, [user]);

  const menuItems = [
    {
      id: 'lobby',
      label: 'Lobby',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
      color: 'text-gray-400'
    },
    {
      id: 'my-bets',
      label: 'My Bets',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
        </svg>
      ),
      color: 'text-gray-400'
    },
    {
      id: 'shop',
      label: 'Shop',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l-1 12H6L5 9z" />
        </svg>
      ),
      color: 'text-gray-400'
    },
    {
      id: 'inventory',
      label: 'Inventory',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      ),
      color: 'text-gray-400'
    },
    {
      id: 'leaderboard',
      label: 'Leaderboard',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'text-gray-400'
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
      color: 'text-gray-400'
    },
    {
      id: 'history',
      label: 'History',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'text-gray-400'
    },
    {
      id: 'admin-panel',
      label: 'Админ панель',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      color: 'text-purple-400',
      adminOnly: true
    }
  ];

  return (
    <div className={`bg-surface-sidebar border-r border-border-primary transition-all duration-300 flex flex-col h-full ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Header */}
      <div className={`p-4 border-b border-border-primary ${isCollapsed ? 'px-2' : ''}`}>
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
          {!isCollapsed && (
            <div className="flex items-center space-x-3">
              {/* Green Gem Logo */}
              <div className="w-10 h-10 flex items-center justify-center">
                <img 
                  src="/gems/gem-green.svg" 
                  alt="GemPlay" 
                  className="w-8 h-8 object-contain"
                />
              </div>
              <span className="font-russo text-2xl text-accent-primary">GemPLAY</span>
            </div>
          )}
          
          {isCollapsed && (
            <div className="flex items-center justify-center mb-2">
              <img 
                src="/gems/gem-green.svg" 
                alt="GemPlay" 
                className="w-8 h-8 object-contain"
              />
            </div>
          )}
          
          {!isCollapsed && (
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 hover:bg-surface-card rounded-lg transition-colors"
            >
              <svg 
                className="w-5 h-5 text-gray-400 transition-transform duration-300" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}
        </div>
        
        {/* Notifications Bell */}
        <div className={`${isCollapsed ? 'flex justify-center mt-2' : 'mt-3 flex justify-center'}`}>
          <NotificationBell isCollapsed={isCollapsed} />
        </div>

        {/* Collapse button when collapsed */}
        {isCollapsed && (
          <div className="flex justify-center mt-2">
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-2 hover:bg-surface-card rounded-lg transition-colors"
            >
              <svg 
                className="w-5 h-5 text-gray-400 transition-transform duration-300 rotate-180" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Menu Items */}
      <nav className="flex-1 py-4">
        <ul className={`space-y-1 ${isCollapsed ? 'px-1' : 'px-2'}`}>
          {menuItems.map((item) => {
            // Показать элементы только для админов, если это админ-элемент
            if (item.adminOnly && (!user || (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN'))) {
              return null;
            }
            
            return (
              <li key={item.id}>
                <button
                  onClick={() => {
                    if (item.id === 'admin-panel') {
                      onOpenAdminPanel();
                    } else {
                      setCurrentView(item.id);
                    }
                  }}
                  className={`w-full flex items-center transition-all duration-300 group relative overflow-hidden ${
                    isCollapsed 
                      ? 'justify-center p-2 mx-1 rounded-lg' 
                      : 'px-3 py-3 rounded-lg'
                  } ${
                    currentView === item.id 
                      ? 'bg-accent-primary bg-opacity-20 text-accent-primary'
                      : `hover:bg-surface-card ${item.color} hover:text-white`
                  }`}
                  title={isCollapsed ? item.label : ''}
                >
                  {/* Цветная рамка для активного состояния */}
                  {currentView === item.id && (
                    <div className={`absolute inset-0 border border-accent-primary bg-accent-primary/10 border-opacity-40 rounded-lg ${
                      isCollapsed ? 'border-opacity-50' : 'border-l-4 border-accent-primary border-opacity-100 border-t-0 border-r-0 border-b-0 bg-accent-primary/15'
                    }`}></div>
                  )}
                  
                  <div className={`relative z-10 transition-all duration-300 ${
                    currentView === item.id 
                      ? 'text-accent-primary' 
                      : `${item.color} group-hover:text-white`
                  } ${
                    isCollapsed 
                      ? 'flex items-center justify-center group-hover:scale-110 group-hover:translate-x-1' 
                      : ''
                  }`}>
                    {item.icon}
                  </div>
                  {!isCollapsed && (
                    <span className="ml-3 font-rajdhani font-semibold tracking-wide relative z-10">
                      {item.label}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User Info */}
      {!isCollapsed && user && (
        <div className="p-4 border-t border-border-primary">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-r from-green-600 to-green-700 rounded-full flex items-center justify-center">
              <span className="font-russo text-white text-sm">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-rajdhani font-semibold text-white truncate">
                {user.username}
              </p>
              <p className="font-roboto text-sm text-green-400">
                ${user.virtual_balance?.toFixed(2) || '0.00'}
              </p>
            </div>
          </div>
          
          {/* Logout Button */}
          <button
            onClick={onLogout}
            className="w-full flex items-center justify-center px-3 py-2 bg-red-600 hover:bg-red-700 text-white font-rajdhani font-bold rounded-lg transition-all duration-300 group"
          >
            <svg className="w-5 h-5 mr-2 group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            LOGOUT
          </button>
        </div>
      )}

      {/* Collapsed User Avatar */}
      {isCollapsed && user && (
        <div className="p-2 border-t border-border-primary">
          <div className="flex flex-col items-center space-y-2">
            <div className="w-8 h-8 bg-gradient-to-r from-green-600 to-green-700 rounded-full flex items-center justify-center">
              <span className="font-russo text-white text-xs">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            
            {/* Collapsed Logout Button */}
            <button
              onClick={onLogout}
              className="w-8 h-8 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-all duration-300 group flex items-center justify-center"
              title="Logout"
            >
              <svg className="w-4 h-4 group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      )}

    </div>
  );
};

export default Sidebar;