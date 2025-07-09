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
      color: 'text-accent-primary'
    },
    {
      id: 'my-bets',
      label: 'My Bets',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
      ),
      color: 'text-blue-400'
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
      color: 'text-purple-400'
    },
    {
      id: 'shop',
      label: 'Shop',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l-1 12H6L5 9z" />
        </svg>
      ),
      color: 'text-yellow-400'
    },
    {
      id: 'inventory',
      label: 'Inventory',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      ),
      color: 'text-green-400'
    },
    {
      id: 'leaderboard',
      label: 'Leaderboard',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'text-orange-400'
    },
    {
      id: 'history',
      label: 'History',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'text-red-400'
    }
  ];

  return (
    <div className={`bg-surface-sidebar border-r border-border-primary transition-all duration-300 flex flex-col h-full ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Header */}
      <div className="p-4 border-b border-border-primary">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center space-x-2">
              {/* Gem Logo */}
              <div className="w-8 h-8 flex items-center justify-center">
                <svg className="w-6 h-6 text-accent-primary" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6,2L2,8L12,22L22,8L18,2H6M6.5,3H17.5L20.5,8L12,19L3.5,8L6.5,3Z" />
                </svg>
              </div>
              <span className="font-russo text-xl text-accent-primary">GemPLAY</span>
            </div>
          )}
          
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 hover:bg-surface-card rounded-lg transition-colors"
          >
            <svg 
              className={`w-5 h-5 text-text-secondary transition-transform duration-300 ${
                isCollapsed ? 'rotate-180' : ''
              }`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
        
        {/* Notifications Bell */}
        {!isCollapsed && (
          <div className="mt-3 flex justify-center">
            <button className="p-2 hover:bg-surface-card rounded-lg transition-colors relative">
              <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {/* Notification dot */}
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
            </button>
          </div>
        )}
      </div>

      {/* Menu Items */}
      <nav className="flex-1 py-4">
        <ul className="space-y-1 px-2">
          {menuItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => setCurrentView(item.id)}
                className={`w-full flex items-center px-3 py-3 rounded-lg transition-all duration-200 group ${
                  currentView === item.id 
                    ? 'bg-accent-primary/20 border-l-4 border-accent-primary text-accent-primary' 
                    : 'hover:bg-surface-card text-text-secondary hover:text-white'
                }`}
                title={isCollapsed ? item.label : ''}
              >
                <div className={`${item.color} ${currentView === item.id ? 'text-accent-primary' : ''}`}>
                  {item.icon}
                </div>
                {!isCollapsed && (
                  <span className="ml-3 font-rajdhani font-semibold tracking-wide">
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
            <div className="w-10 h-10 bg-gradient-accent rounded-full flex items-center justify-center">
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

      {/* Admin Monitoring Section */}
      {!isCollapsed && user && (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') && (
        <div className="p-2 border-t border-border-primary">
          <button
            onClick={() => setCurrentView('monitoring')}
            className={`w-full flex items-center px-3 py-2 rounded-lg transition-all duration-200 ${
              currentView === 'monitoring' 
                ? 'bg-red-600/20 border-l-4 border-red-500 text-red-400' 
                : 'hover:bg-surface-card text-red-400 hover:text-red-300'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span className="ml-3 font-rajdhani font-semibold tracking-wide">
              МОНИТОРИНГ
            </span>
          </button>
        </div>
      )}
    </div>
  );
};

export default Sidebar;