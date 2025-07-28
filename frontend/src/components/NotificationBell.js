import React, { useState, useEffect, useRef } from 'react';
import { useNotifications } from './NotificationContext';

const NotificationBell = ({ isCollapsed }) => {
  const [isOpen, setIsOpen] = useState(false);
  const bellRef = useRef(null);
  const dropdownRef = useRef(null);

  // Use the integrated notification system
  const {
    persistentNotifications,
    unreadCount,
    loading,
    fetchNotifications,
    markAsRead,
    markAllAsRead
  } = useNotifications();

  // Handle bell click
  const handleBellClick = () => {
    if (!isOpen) {
      fetchNotifications();
    }
    setIsOpen(!isOpen);
  };

  // Handle click outside
  const handleClickOutside = (event) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target) && 
        bellRef.current && !bellRef.current.contains(event.target)) {
      setIsOpen(false);
    }
  };

  // Handle notification click
  const handleNotificationClick = async (notification) => {
    // Mark as read if not already read
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }
    
    // Navigate to action URL if exists
    if (notification.payload?.action_url) {
      window.location.href = notification.payload.action_url;
    }
    
    setIsOpen(false);
  };

  // Format time ago helper
  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'только что';
    if (diffInMinutes < 60) return `${diffInMinutes} мин назад`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} ч назад`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} д назад`;
  };

  // Get priority color
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'error': return 'border-l-red-500';
      case 'warning': return 'border-l-yellow-500';
      default: return 'border-l-accent-primary';
    }
  };

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  return (
    <div className="relative">
      {/* Notification Bell Button */}
      <button 
        ref={bellRef}
        onClick={handleBellClick}
        className={`p-2 hover:bg-surface-card rounded-lg transition-colors relative ${
          isCollapsed ? 'w-full flex justify-center' : ''
        }`}
      >
        <svg className="w-6 h-6 text-gray-400 hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        
        {/* Notification count badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[1.25rem] h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center px-1">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notifications Dropdown */}
      {isOpen && (
        <div 
          ref={dropdownRef}
          className="absolute right-0 mt-2 w-80 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg shadow-lg z-50"
        >
          {/* Header */}
          <div className="p-3 border-b border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-white font-rajdhani font-bold text-lg">Уведомления</h3>
              <div className="flex items-center space-x-2">
                {loading && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent-primary"></div>
                )}
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-xs text-accent-primary hover:underline"
                  >
                    Все прочитано
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {persistentNotifications.length === 0 ? (
              <div className="p-4 text-center">
                <div className="text-gray-400 text-sm">📭</div>
                <div className="text-gray-400 text-sm mt-2">Нет уведомлений</div>
              </div>
            ) : (
              persistentNotifications.slice(0, 10).map(notification => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  className={`p-3 border-b border-gray-700 last:border-b-0 cursor-pointer hover:bg-surface-sidebar transition-colors duration-200 border-l-4 ${getPriorityColor(notification.priority)} ${
                    !notification.is_read ? 'bg-accent-primary bg-opacity-5' : ''
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <span className="text-lg flex-shrink-0 mt-0.5">{notification.emoji}</span>
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm ${!notification.is_read ? 'font-bold text-white' : 'text-gray-300'}`}>
                        {notification.title}
                      </div>
                      <div className="text-xs text-gray-400 mt-1 line-clamp-2">
                        {notification.message}
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <div className="text-xs text-gray-500">
                          {formatTimeAgo(notification.created_at)}
                        </div>
                        {!notification.is_read && (
                          <div className="w-2 h-2 bg-accent-primary rounded-full flex-shrink-0"></div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          
          {/* Footer */}
          <div className="p-3 border-t border-gray-700">
            <button 
              onClick={() => {
                window.location.href = '/notifications';
                setIsOpen(false);
              }}
              className="text-accent-primary text-sm hover:underline"
            >
              Все уведомления →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;