import { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

/**
 * Custom hook for managing notifications
 */
export const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`${API}/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setNotifications(response.data);
      setUnreadCount(response.data.filter(n => !n.read).length);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/notifications/${notificationId}/mark-read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Update local state
      setNotifications(prev => 
        prev.map(n => 
          n.id === notificationId ? { ...n, read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/notifications/mark-all-read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Update local state
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  // Get notification icon and color
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'GIFT_RECEIVED':
        return { icon: '🎁', color: 'text-green-400' };
      case 'GAME_WON':
        return { icon: '🏆', color: 'text-yellow-400' };
      case 'GAME_LOST':
        return { icon: '😞', color: 'text-red-400' };
      case 'BALANCE_LOW':
        return { icon: '💰', color: 'text-orange-400' };
      default:
        return { icon: 'ℹ️', color: 'text-blue-400' };
    }
  };

  // Format time ago
  const timeAgo = (dateString) => {
    const now = new Date();
    const notificationDate = new Date(dateString);
    const diffInMinutes = Math.floor((now - notificationDate) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  // Auto-fetch notifications every 30 seconds
  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  return {
    notifications,
    unreadCount,
    loading,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    getNotificationIcon,
    timeAgo
  };
};

/**
 * Custom hook for dropdown positioning
 */
export const useDropdownPosition = (triggerRef) => {
  const [position, setPosition] = useState({ right: 0, top: '100%' });

  const calculatePosition = () => {
    if (!triggerRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    const dropdownWidth = 320;
    const dropdownMaxHeight = 400;
    
    let newPosition = {
      right: 0,
      top: '100%',
      left: 'auto',
      bottom: 'auto',
      maxHeight: `${dropdownMaxHeight}px`
    };

    // Check if dropdown would go off right edge of screen
    if (triggerRect.right - dropdownWidth < 0) {
      newPosition.left = 0;
      newPosition.right = 'auto';
    }

    // Check if dropdown would go off bottom of screen
    const spaceBelow = viewportHeight - triggerRect.bottom - 8;
    const spaceAbove = triggerRect.top - 8;
    
    if (spaceBelow < dropdownMaxHeight && spaceAbove > spaceBelow) {
      newPosition.bottom = '100%';
      newPosition.top = 'auto';
      newPosition.maxHeight = `${Math.min(spaceAbove, dropdownMaxHeight)}px`;
    } else {
      newPosition.maxHeight = `${Math.min(spaceBelow, dropdownMaxHeight)}px`;
    }

    setPosition(newPosition);
  };

  return { position, calculatePosition };
};