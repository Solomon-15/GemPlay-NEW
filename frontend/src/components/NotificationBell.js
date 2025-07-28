import React, { useState, useEffect, useRef, useCallback } from 'react';
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

  // Enhanced positioning calculation for perfect alignment
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0 });

  // Calculate precise dropdown position
  const calculateDropdownPosition = useCallback(() => {
    if (bellRef.current) {
      const bellRect = bellRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      
      // Position dropdown so its left-top corner touches the bell
      const position = {
        // Top edge of dropdown should align with bottom edge of bell
        top: bellRect.bottom + 2, // 2px gap for perfect visual connection
        // Left edge of dropdown should align with left edge of bell
        left: bellRect.left,
        maxHeight: viewportHeight - bellRect.bottom - 20, // Leave margin from bottom
        maxWidth: Math.min(320, viewportWidth - bellRect.left - 20) // Don't exceed viewport
      };
      
      setDropdownPosition(position);
    }
  }, []);

  // Update position when bell is clicked or window resizes  
  useEffect(() => {
    if (isOpen) {
      calculateDropdownPosition();
      
      const handleResize = () => {
        if (isOpen) {
          calculateDropdownPosition();
        }
      };
      
      const handleScroll = () => {
        if (isOpen) {
          calculateDropdownPosition();
        }
      };
      
      window.addEventListener('resize', handleResize);
      window.addEventListener('scroll', handleScroll, true);
      
      return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('scroll', handleScroll, true);
      };
    }
  }, [isOpen, calculateDropdownPosition]);

  // Handle bell click with position calculation
  const handleBellClick = () => {
    if (!isOpen) {
      fetchNotifications();
      // Calculate position before opening
      setTimeout(calculateDropdownPosition, 0);
    }
    setIsOpen(!isOpen);
  };

  // Handle click outside with improved logic
  const handleClickOutside = (event) => {
    if (isOpen && 
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target) && 
        bellRef.current && 
        !bellRef.current.contains(event.target)) {
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

  // Enhanced responsive positioning
  const getDropdownClasses = () => {
    const baseClasses = `
      absolute z-50 bg-surface-card border border-accent-primary border-opacity-30 
      rounded-lg shadow-xl transform transition-all duration-200 ease-out
    `;
    
    // Responsive width and positioning
    const responsiveClasses = `
      w-80 max-w-[calc(100vw-2rem)]
      sm:w-72 sm:max-w-[calc(100vw-2rem)]
      xs:w-64 xs:max-w-[calc(100vw-1rem)]
      right-0 top-full mt-2
    `;
    
    const stateClasses = isOpen 
      ? 'opacity-100 scale-100 translate-y-0' 
      : 'opacity-0 scale-95 -translate-y-2 pointer-events-none';
    
    return `${baseClasses} ${responsiveClasses} ${stateClasses}`;
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
      {/* Bell Button - Stylized Design */}
      <button
        ref={bellRef}
        onClick={handleBellClick}
        className={`
          relative flex items-center justify-center p-3 text-text-secondary hover:text-white 
          transition-all duration-200 rounded-lg hover:bg-surface-sidebar group
          ${isCollapsed ? 'w-10 h-10' : 'w-10 h-10'}
        `}
        aria-label="Notifications"
      >
        {/* Stylized Bell Icon */}
        <div className="relative">
          <svg 
            className="w-6 h-6 transform group-hover:scale-110 transition-transform duration-200" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
            strokeWidth={1.5}
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" 
            />
          </svg>
          
          {/* Notification Dot - only show when there are unread notifications */}
          {unreadCount > 0 && (
            <div className="absolute -top-1 -right-1 flex items-center justify-center">
              <div className="absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75 animate-ping"></div>
              <div className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></div>
            </div>
          )}
        </div>
        
        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[1.25rem] h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center px-1 border-2 border-surface-primary">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notifications Dropdown - Enhanced Responsive Design */}
      {isOpen && (
        <>
          {/* Mobile backdrop */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-25 z-40 sm:hidden"
            onClick={() => setIsOpen(false)}
          />
          
          <div 
            ref={dropdownRef}
            className={getDropdownClasses()}
            style={{
              maxHeight: 'min(24rem, calc(100vh - 120px))'
            }}
          >
            {/* Header */}
            <div className="sticky top-0 p-3 border-b border-gray-700 bg-surface-card rounded-t-lg z-10">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-rajdhani font-bold text-lg">Уведомления</h3>
                <div className="flex items-center space-x-3">
                  {loading && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent-primary"></div>
                  )}
                  {unreadCount > 0 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        markAllAsRead();
                      }}
                      className="text-xs text-accent-primary hover:text-accent-primary-dark transition-colors whitespace-nowrap"
                    >
                      Все прочитано
                    </button>
                  )}
                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-gray-400 hover:text-white transition-colors sm:hidden p-1"
                    aria-label="Закрыть"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Notifications List - Enhanced Scrolling */}
            <div className="overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
              {persistentNotifications.length === 0 ? (
                <div className="p-8 text-center">
                  <div className="text-4xl mb-3 opacity-50">📭</div>
                  <div className="text-gray-400 text-sm">Нет уведомлений</div>
                  <div className="text-gray-500 text-xs mt-1">Здесь будут отображаться ваши уведомления</div>
                </div>
              ) : (
                <div className="divide-y divide-gray-700">
                  {persistentNotifications.slice(0, 10).map(notification => (
                    <div
                      key={notification.id}
                      onClick={() => handleNotificationClick(notification)}
                      className={`p-3 cursor-pointer hover:bg-surface-sidebar transition-colors duration-200 border-l-4 ${getPriorityColor(notification.priority)} ${
                        !notification.is_read ? 'bg-accent-primary bg-opacity-5' : ''
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <span className="text-lg flex-shrink-0 mt-0.5 select-none">{notification.emoji}</span>
                        <div className="flex-1 min-w-0">
                          <div className={`text-sm leading-tight break-words ${!notification.is_read ? 'font-bold text-white' : 'text-gray-300'}`}>
                            {notification.title}
                          </div>
                          <div className="text-xs text-gray-400 mt-1 line-clamp-2 leading-tight break-words">
                            {notification.message}
                          </div>
                          <div className="flex items-center justify-between mt-2">
                            <div className="text-xs text-gray-500 flex-shrink-0">
                              {formatTimeAgo(notification.created_at)}
                            </div>
                            {!notification.is_read && (
                              <div className="w-2 h-2 bg-accent-primary rounded-full flex-shrink-0 ml-2"></div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Footer - Sticky */}
            <div className="sticky bottom-0 p-3 border-t border-gray-700 bg-surface-card rounded-b-lg">
              <button 
                onClick={() => {
                  window.location.href = '/notifications';
                  setIsOpen(false);
                }}
                className="text-accent-primary text-sm hover:text-accent-primary-dark transition-colors font-medium"
              >
                Все уведомления →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationBell;