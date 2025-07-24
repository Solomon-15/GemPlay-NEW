import React, { createContext, useContext, useState, useCallback } from 'react';

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  // Support for both formats: addNotification({type, message}) and addNotification(message, type)
  const addNotification = useCallback((messageOrNotification, type = null) => {
    const notification = typeof messageOrNotification === 'string' 
      ? { message: messageOrNotification, type: type || 'info' }
      : messageOrNotification;
      
    const id = Date.now() + Math.random();
    const fullNotification = {
      id,
      type: notification.type || 'info',
      message: notification.message || '',
      duration: notification.duration || 5000,
      isRussian: notification.isRussian || false,
      ...notification
    };
    
    setNotifications(prev => [...prev, fullNotification]);
    
    // Auto-remove after duration
    setTimeout(() => {
      removeNotification(id);
    }, fullNotification.duration);
    
    return id;
  }, [removeNotification]);

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Helper functions for different notification types
  const showSuccess = useCallback((message, options = {}) => {
    return addNotification({ type: 'success', message, ...options });
  }, [addNotification]);

  const showError = useCallback((message, options = {}) => {
    return addNotification({ type: 'error', message, ...options });
  }, [addNotification]);

  const showWarning = useCallback((message, options = {}) => {
    return addNotification({ type: 'warning', message, ...options });
  }, [addNotification]);

  const showInfo = useCallback((message, options = {}) => {
    return addNotification({ type: 'info', message, ...options });
  }, [addNotification]);

  // Localized notification helpers
  const showSuccessRU = useCallback((message, options = {}) => {
    return addNotification({ type: 'success', message, isRussian: true, ...options });
  }, [addNotification]);

  const showErrorRU = useCallback((message, options = {}) => {
    return addNotification({ type: 'error', message, isRussian: true, ...options });
  }, [addNotification]);

  const showWarningRU = useCallback((message, options = {}) => {
    return addNotification({ type: 'warning', message, isRussian: true, ...options });
  }, [addNotification]);

  const showInfoRU = useCallback((message, options = {}) => {
    return addNotification({ type: 'info', message, isRussian: true, ...options });
  }, [addNotification]);

  const value = {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showSuccessRU,
    showErrorRU,
    showWarningRU,
    showInfoRU,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export default NotificationProvider;