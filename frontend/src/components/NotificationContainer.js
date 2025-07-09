import React from 'react';
import Notification from './Notification';
import { useNotifications } from './NotificationContext';

const NotificationContainer = () => {
  const { notifications, removeNotification } = useNotifications();

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          id={notification.id}
          type={notification.type}
          message={notification.message}
          duration={notification.duration}
          isRussian={notification.isRussian}
          onClose={removeNotification}
        />
      ))}
    </div>
  );
};

export default NotificationContainer;