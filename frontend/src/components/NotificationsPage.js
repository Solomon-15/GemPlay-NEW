import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationContext';
import MatchResultNotification from './MatchResultNotification';
import { formatDateTimeDDMMYYYYHHMMSS } from '../utils/timeUtils';

const NotificationsPage = ({ user }) => {
  const {
    persistentNotifications,
    unreadCount,
    loading,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification
  } = useNotifications();

  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState('all'); // all, unread, read
  const [typeFilter, setTypeFilter] = useState('all');

  useEffect(() => {
    fetchNotifications(page, 20);
  }, [page, fetchNotifications]);

  const handleNotificationClick = async (notification, event) => {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'error': return 'border-l-red-500 bg-red-500 bg-opacity-5';
      case 'warning': return 'border-l-yellow-500 bg-yellow-500 bg-opacity-5';
      default: return 'border-l-accent-primary bg-accent-primary bg-opacity-5';
    }
  };

  const getTypeLabel = (type) => {
    const typeLabels = {
      bet_accepted: 'Bet Accepted',
      match_result: 'Match Result',
      commission_freeze: 'Commission Freeze',
      gem_gift: 'Gem Gift',
      system_message: 'System Message',
      admin_notification: 'Admin Notification'
    };
    return typeLabels[type] || type;
  };

  // Filter notifications based on selected filters
  const filteredNotifications = persistentNotifications.filter(notification => {
    if (filter === 'unread' &amp;&amp; notification.is_read) return false;
    if (filter === 'read' &amp;&amp; !notification.is_read) return false;
    if (typeFilter !== 'all' &amp;&amp; notification.type !== typeFilter) return false;
    return true;
  });

  const renderNotification = (notification) =&gt; {
    if (notification.type === 'match_result') {
      return <MatchResultNotification notification={notification} user={user} />;
    }
    return (
      <div className="p-3">
        <div className="text-white font-rajdhani font-bold text-base">{notification.title || 'Notification'}</div>
        <p className="text-sm text-gray-300 mt-1">{notification.message}</p>
        <div className="text-xs text-gray-500 mt-1">{formatDateTimeDDMMYYYYHHMMSS(notification.created_at, user?.timezone_offset)}</div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-surface-primary">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-rajdhani font-bold text-white mb-2">
                🔔 Notifications
              </h1>
              <p className="text-text-secondary">
                {unreadCount &gt; 0 ? `You have ${unreadCount} unread notifications` : 'All notifications are read'}
              </p>
            </div>
            
            {unreadCount &gt; 0 &amp;&amp; (
              <button
                onClick={markAllAsRead}
                className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-dark transition-colors"
              >
                Mark all as read
              </button>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* Read status filter */}
            <div className="flex items-center space-x-2">
              <label className="text-sm text-text-secondary">Status:</label>
              <select
                value={filter}
                onChange={(e) =&gt; setFilter(e.target.value)}
                className="px-3 py-1 bg-surface-sidebar border border-border-primary rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary"
              >
                <option value="all">All</option>
                <option value="unread">Unread</option>
                <option value="read">Read</option>
              </select>
            </div>

            {/* Type filter */}
            <div className="flex items-center space-x-2">
              <label className="text-sm text-text-secondary">Type:</label>
              <select
                value={typeFilter}
                onChange={(e) =&gt; setTypeFilter(e.target.value)}
                className="px-3 py-1 bg-surface-sidebar border border-border-primary rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary"
              >
                <option value="all">All types</option>
                <option value="bet_accepted">Bet Accepted</option>
                <option value="match_result">Match Results</option>
                <option value="commission_freeze">Commission Freeze</option>
                <option value="gem_gift">Gem Gifts</option>
                <option value="system_message">System Messages</option>
                <option value="admin_notification">Admin Notifications</option>
              </select>
            </div>
          </div>
        </div>

        {/* Notifications List */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary mx-auto"></div>
              <p className="text-text-secondary mt-2">Loading notifications...</p>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📭</div>
              <h3 className="text-lg font-rajdhani font-bold text-white mb-2">
                No notifications
              </h3>
              <p className="text-text-secondary">
                {filter === 'all' 
                  ? 'You have no notifications yet'
                  : filter === 'unread'
                  ? 'All notifications are read'
                  : 'No read notifications'
                }
              </p>
            </div>
          ) : (
            filteredNotifications.map(notification =&gt; (
              <div
                key={notification.id}
                className={`bg-surface-card border border-gray-700 rounded-lg p-0 cursor-pointer hover:bg-surface-sidebar transition-colors border-l-4 ${getPriorityColor(notification.priority)} ${
                  !notification.is_read ? 'ring-1 ring-accent-primary ring-opacity-30' : ''
                }`}
                onClick={(event) =&gt; handleNotificationClick(notification, event)}
              >
                {renderNotification(notification)}
                <div className="flex items-center justify-between px-3 pb-3">
                  <span className="text-xs text-gray-500">
                    {formatDateTimeDDMMYYYYHHMMSS(notification.created_at, user?.timezone_offset)}
                  </span>
                  <div className="flex items-center space-x-2">
                    {notification.payload?.action_url &amp;&amp; (
                      <span className="text-xs text-accent-primary">
                        Click to navigate →
                      </span>
                    )}
                    <button
                      onClick={(e) =&gt; {
                        e.stopPropagation();
                        deleteNotification(notification.id);
                      }}
                      className="text-gray-500 hover:text-red-400 transition-colors"
                      title="Delete notification"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Load More Button (if needed) */}
        {filteredNotifications.length &gt;= 20 &amp;&amp; (
          <div className="text-center mt-8">
            <button
              onClick={() =&gt; setPage(prev =&gt; prev + 1)}
              disabled={loading}
              className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary-dark disabled:opacity-50 transition-colors"
            >
              {loading ? 'Loading...' : 'Load more'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsPage;