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

  const { position, calculatePosition } = useDropdownPosition(bellRef);

  // Handle bell click
  const handleBellClick = () => {
    if (!isOpen) {
      calculatePosition();
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

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      window.addEventListener('resize', calculatePosition);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        window.removeEventListener('resize', calculatePosition);
      };
    }
  }, [isOpen, calculatePosition]);

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
        <>
          {/* Enhanced Backdrop */}
          <div 
            className="fixed inset-0 z-[9998]" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown Panel */}
          <div 
            ref={dropdownRef}
            className="fixed z-[9999] w-80 bg-surface-card border border-border-primary rounded-lg shadow-2xl overflow-hidden"
            style={{
              ...position,
              right: position.right !== 'auto' ? `${bellRef.current?.getBoundingClientRect().right - (bellRef.current?.getBoundingClientRect().width || 0) - 320 + (bellRef.current?.getBoundingClientRect().width || 0)}px` : position.right,
              left: position.left !== 'auto' ? `${bellRef.current?.getBoundingClientRect().left}px` : position.left,
              top: position.top !== 'auto' ? `${(bellRef.current?.getBoundingClientRect().bottom || 0) + 8}px` : position.top,
              bottom: position.bottom !== 'auto' ? `${window.innerHeight - (bellRef.current?.getBoundingClientRect().top || 0) + 8}px` : position.bottom,
              maxHeight: position.maxHeight,
              minWidth: '320px',
              maxWidth: '320px'
            }}
          >
            {/* Header */}
            <div className="px-4 py-3 border-b border-border-primary flex items-center justify-between bg-surface-card">
              <h3 className="font-rajdhani font-bold text-white">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-xs text-accent-primary hover:text-accent-secondary transition-colors"
                >
                  Mark all read
                </button>
              )}
            </div>

            {/* Notifications List */}
            <div className="overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800" 
                 style={{ 
                   maxHeight: 'calc(100% - 120px)',
                   minHeight: '200px'
                 }}>
              {notifications.length === 0 ? (
                <div className="px-4 py-8 text-center text-text-secondary">
                  <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  <div className="text-sm">No notifications yet</div>
                  <div className="text-xs mt-1">You'll see notifications here when something happens</div>
                </div>
              ) : (
                <div className="space-y-0">
                  {notifications.map((notification) => {
                    const { icon, color } = getNotificationIcon(notification.type);
                    
                    return (
                      <div
                        key={notification.id}
                        onClick={() => {
                          if (!notification.read) {
                            markAsRead(notification.id);
                          }
                        }}
                        className={`px-4 py-3 border-b border-border-primary last:border-b-0 hover:bg-surface-sidebar cursor-pointer transition-colors ${
                          !notification.read ? 'bg-accent-primary bg-opacity-5' : ''
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          {/* Icon */}
                          <div className={`text-lg ${color} flex-shrink-0 mt-0.5`}>
                            {icon}
                          </div>
                          
                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <h4 className={`text-sm font-medium ${
                                !notification.read ? 'text-white' : 'text-text-secondary'
                              }`}>
                                {notification.title}
                              </h4>
                              {!notification.read && (
                                <div className="w-2 h-2 bg-accent-primary rounded-full flex-shrink-0"></div>
                              )}
                            </div>
                            
                            <p className={`text-xs ${
                              !notification.read ? 'text-text-secondary' : 'text-gray-500'
                            } leading-relaxed mb-1`}>
                              {notification.message}
                            </p>
                            
                            <div className="text-xs text-gray-500">
                              {timeAgo(notification.created_at)}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Footer */}
            {notifications.length > 0 && (
              <div className="px-4 py-2 border-t border-border-primary bg-surface-sidebar">
                <button 
                  onClick={() => setIsOpen(false)}
                  className="w-full text-xs text-text-secondary hover:text-white transition-colors text-center"
                >
                  Close notifications
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default NotificationBell;