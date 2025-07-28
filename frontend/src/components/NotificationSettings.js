import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationContext';

const NotificationSettings = () => {
  const { 
    notificationSettings, 
    updateNotificationSettings, 
    loading 
  } = useNotifications();
  
  const [settings, setSettings] = useState({
    bet_accepted: true,
    match_results: true,
    commission_freeze: true,
    gem_gifts: true,
    system_messages: true,
    admin_notifications: true
  });
  
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  // Load settings when component mounts or settings change
  useEffect(() => {
    if (notificationSettings) {
      setSettings(notificationSettings);
    }
  }, [notificationSettings]);

  const handleSettingChange = async (key, value) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    
    setSaving(true);
    setSaveStatus('');
    
    try {
      const success = await updateNotificationSettings(newSettings);
      if (success) {
        setSaveStatus('Настройки сохранены');
        setTimeout(() => setSaveStatus(''), 3000);
      } else {
        setSaveStatus('Ошибка сохранения');
        setTimeout(() => setSaveStatus(''), 3000);
      }
    } catch (error) {
      setSaveStatus('Ошибка сохранения');
      setTimeout(() => setSaveStatus(''), 3000);
    } finally {
      setSaving(false);
    }
  };

  const settingsConfig = [
    { 
      key: 'bet_accepted', 
      label: 'Принятие ставок', 
      emoji: '🎯',
      description: 'Уведомления когда кто-то принимает вашу ставку'
    },
    { 
      key: 'match_results', 
      label: 'Результаты матчей', 
      emoji: '🏆',
      description: 'Уведомления о победах, поражениях и ничьих'
    },
    { 
      key: 'commission_freeze', 
      label: 'Заморозка комиссии', 
      emoji: '❄️',
      description: 'Уведомления о заморозке и разморозке комиссии'
    },
    { 
      key: 'gem_gifts', 
      label: 'Подарки гемов', 
      emoji: '💎',
      description: 'Уведомления о получении подарков гемов'
    },
    { 
      key: 'system_messages', 
      label: 'Системные сообщения', 
      emoji: '📢',
      description: 'Обновления системы, техработы, важные новости'
    },
    { 
      key: 'admin_notifications', 
      label: 'Админ-уведомления', 
      emoji: '🛡️',
      description: 'Административные уведомления и модерация'
    }
  ];

  if (loading) {
    return (
      <div className="bg-surface-card p-6 rounded-lg">
        <div className="flex items-center space-x-2 mb-4">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-accent-primary"></div>
          <h3 className="text-white text-lg font-rajdhani font-bold">Загрузка настроек уведомлений...</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-white text-xl font-rajdhani font-bold">🔔 Настройки уведомлений</h3>
        {saveStatus && (
          <div className={`text-sm px-3 py-1 rounded ${
            saveStatus.includes('Ошибка') 
              ? 'bg-red-600 bg-opacity-20 text-red-400' 
              : 'bg-green-600 bg-opacity-20 text-green-400'
          }`}>
            {saveStatus}
          </div>
        )}
      </div>
      
      <div className="space-y-4">
        {settingsConfig.map(({ key, label, emoji, description }) => (
          <div key={key} className="flex items-start justify-between p-4 bg-surface-sidebar bg-opacity-50 rounded-lg border border-gray-700">
            <div className="flex items-start space-x-3 flex-1">
              <span className="text-2xl mt-1">{emoji}</span>
              <div className="flex-1">
                <h4 className="text-white font-roboto font-medium">{label}</h4>
                <p className="text-text-secondary text-sm mt-1">{description}</p>
              </div>
            </div>
            
            <div className="flex items-center ml-4">
              {saving && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent-primary mr-2"></div>
              )}
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings[key] || false}
                  onChange={(e) => handleSettingChange(key, e.target.checked)}
                  disabled={saving}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent-primary peer-focus:ring-opacity-25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-primary disabled:opacity-50"></div>
              </label>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-surface-sidebar bg-opacity-30 rounded-lg border border-gray-700">
        <div className="flex items-start space-x-3">
          <span className="text-lg">💡</span>
          <div>
            <h5 className="text-white font-roboto font-medium mb-1">Про уведомления</h5>
            <p className="text-text-secondary text-sm">
              Уведомления помогают не пропустить важные события в игре. 
              Вы можете отключить любой тип уведомлений, если они вам не нужны.
              Изменения сохраняются автоматически.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings;