import React, { useState } from 'react';

const Sidebar = ({ currentView, setCurrentView, user, isCollapsed, setIsCollapsed }) => {
  const menuItems = [
    {
      id: 'lobby',
      label: 'Lobby',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
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
      id: 'history',
      label: 'History',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'text-gray-400'
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
          <button className={`p-2 hover:bg-surface-card rounded-lg transition-colors relative ${
            isCollapsed ? 'w-full flex justify-center' : ''
          }`}>
            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            {/* Notification dot */}
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
          </button>
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
          {menuItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => setCurrentView(item.id)}
                className={`w-full flex items-center transition-all duration-300 group relative overflow-hidden ${
                  isCollapsed 
                    ? 'justify-center p-2 mx-1 rounded-lg' 
                    : 'px-3 py-3 rounded-lg'
                } ${
                  currentView === item.id 
                    ? isCollapsed
                      ? 'bg-accent-primary/5 text-accent-primary' 
                      : 'bg-accent-primary/5 text-accent-primary'
                    : 'hover:bg-surface-card text-gray-400 hover:text-white'
                }`}
                title={isCollapsed ? item.label : ''}
              >
                {/* Very thin green frame for active state */}
                {currentView === item.id && (
                  <div className={`absolute inset-0 border border-accent-primary border-opacity-40 rounded-lg bg-accent-primary/3 ${
                    isCollapsed ? 'border-opacity-50' : 'border-l-2 border-accent-primary border-opacity-100 border-t-0 border-r-0 border-b-0 bg-accent-primary/8'
                  }`}></div>
                )}
                
                <div className={`relative z-10 transition-all duration-300 ${
                  currentView === item.id ? 'text-accent-primary' : 'text-gray-400 group-hover:text-white'
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
          ))}
        </ul>
      </nav>

      {/* User Info */}
      {!isCollapsed && user && (
        <div className="p-4 border-t border-border-primary">
          <div className="flex items-center space-x-3">
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
        </div>
      )}

      {/* Collapsed User Avatar */}
      {isCollapsed && user && (
        <div className="p-2 border-t border-border-primary flex justify-center">
          <div className="w-8 h-8 bg-gradient-to-r from-green-600 to-green-700 rounded-full flex items-center justify-center">
            <span className="font-russo text-white text-xs">
              {user.username.charAt(0).toUpperCase()}
            </span>
          </div>
        </div>
      )}

      {/* Admin Monitoring Section */}
      {user && (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') && (
        <div className={`border-t border-accent-primary border-opacity-30 ${isCollapsed ? 'p-1' : 'p-2'}`}>
          <button
            onClick={() => setCurrentView('monitoring')}
            className={`w-full flex items-center transition-all duration-200 relative ${
              isCollapsed 
                ? 'justify-center p-2 mx-1 rounded-lg' 
                : 'px-3 py-2 rounded-lg'
            } ${
              currentView === 'monitoring' 
                ? isCollapsed
                  ? 'bg-red-500/10 text-red-400 relative' 
                  : 'bg-red-500/10 border-l-2 border-red-500 text-red-400'
                : 'hover:bg-surface-card text-red-400 hover:text-red-300'
            }`}
            title={isCollapsed ? 'Monitoring' : ''}
          >
            {/* Red frame for collapsed active state */}
            {currentView === 'monitoring' && isCollapsed && (
              <div className="absolute inset-0 border border-red-500/60 rounded-lg bg-red-500/5"></div>
            )}
            
            <svg className="w-6 h-6 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            {!isCollapsed && (
              <span className="ml-3 font-rajdhani font-semibold tracking-wide">
                МОНИТОРИНГ
              </span>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default Sidebar;