import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  // Legacy toast notifications state
  const [toastNotifications, setToastNotifications] = useState([]);
  
  // New persistent notifications state
  const [persistentNotifications, setPersistentNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize notification settings
  const [notificationSettings, setNotificationSettings] = useState({
    bet_accepted: true,
    match_results: true,
    commission_freeze: true,
    gem_gifts: true,
    system_messages: true,
    admin_notifications: true
  });

  // Fetch persistent notifications from API
  const fetchNotifications = useCallback(async (page = 1, limit = 20) => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      if (!token) {
        return;
      }

      const response = await axios.get(`${API}/notifications`, {
        headers: { 'Authorization': `Bearer ${token}` },
        params: { page, limit }
      });

      if (response.data.success) {
        setPersistentNotifications(response.data.notifications || []);
        setUnreadCount(response.data.pagination?.unread_count || 0);
      }
    } catch (err) {
      console.error('Error fetching notifications:', err);
      setError('Ошибка загрузки уведомлений');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load notification settings
  const fetchNotificationSettings = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`${API}/notifications/settings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.data.success) {
        setNotificationSettings(response.data.settings);
      }
    } catch (err) {
      console.error('Error fetching notification settings:', err);
    }
  }, []);

  // Update notification settings
  const updateNotificationSettings = useCallback(async (newSettings) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return false;

      const response = await axios.put(`${API}/notifications/settings`, newSettings, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.data.success) {
        setNotificationSettings(newSettings);
        return true;
      }
      return false;
    } catch (err) {
      console.error('Error updating notification settings:', err);
      return false;
    }
  }, []);

  // Mark notification as read
  const markAsRead = useCallback(async (notificationId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return false;

      await axios.put(`${API}/notifications/${notificationId}/read`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      // Update local state
      setPersistentNotifications(prev => 
        prev.map(n => 
          n.id === notificationId 
            ? { ...n, is_read: true, read_at: new Date().toISOString() }
            : n
        )
      );
      
      setUnreadCount(prev => Math.max(0, prev - 1));
      return true;
    } catch (err) {
      console.error('Error marking notification as read:', err);
      return false;
    }
  }, []);

  // Mark all notifications as read
  const markAllAsRead = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return false;

      await axios.put(`${API}/notifications/mark-all-read`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      // Update local state
      setPersistentNotifications(prev => 
        prev.map(n => ({ ...n, is_read: true, read_at: new Date().toISOString() }))
      );
      
      setUnreadCount(0);
      return true;
    } catch (err) {
      console.error('Error marking all notifications as read:', err);
      return false;
    }
  }, []);

  // Delete notification
  const deleteNotification = useCallback(async (notificationId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return false;

      await axios.delete(`${API}/notifications/${notificationId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      // Update local state
      setPersistentNotifications(prev => 
        prev.filter(n => n.id !== notificationId)
      );
      
      return true;
    } catch (err) {
      console.error('Error deleting notification:', err);
      return false;
    }
  }, []);

  // Legacy toast notification functions (backward compatibility)
  const removeToastNotification = useCallback((id) => {
    setToastNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

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
    
    setToastNotifications(prev => [...prev, fullNotification]);
    
    // Auto-remove after duration
    setTimeout(() => {
      removeToastNotification(id);
    }, fullNotification.duration);
    
    return id;
  }, [removeToastNotification]);

  const clearAllNotifications = useCallback(() => {
    setToastNotifications([]);
  }, []);

  // Helper functions for different notification types (legacy support)
  const addSuccessNotification = useCallback((message, duration = 5000) => {
    return addNotification({ message, type: 'success', duration });
  }, [addNotification]);

  const addErrorNotification = useCallback((message, duration = 7000) => {
    return addNotification({ message, type: 'error', duration });
  }, [addNotification]);

  const addWarningNotification = useCallback((message, duration = 6000) => {
    return addNotification({ message, type: 'warning', duration });
  }, [addNotification]);

  const addInfoNotification = useCallback((message, duration = 5000) => {
    return addNotification({ message, type: 'info', duration });
  }, [addNotification]);

  // Initialize notifications on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchNotifications();
      fetchNotificationSettings();
    }
  }, [fetchNotifications, fetchNotificationSettings]);

  // Auto-refresh notifications every 30 seconds
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const interval = setInterval(() => {
      fetchNotifications();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const value = {
    // Legacy toast notifications (backward compatibility)
    notifications: toastNotifications,
    addNotification,
    removeNotification: removeToastNotification,
    clearAllNotifications,
    addSuccessNotification,
    addErrorNotification,
    addWarningNotification,
    addInfoNotification,

    // New persistent notifications system
    persistentNotifications,
    unreadCount,
    loading,
    error,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,

    // Notification settings
    notificationSettings,
    updateNotificationSettings,
    fetchNotificationSettings
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
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