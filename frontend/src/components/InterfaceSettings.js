import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const InterfaceSettings = () => {
  const [settings, setSettings] = useState({
    live_players: {
      my_bets: 10,
      available_bets: 10,
      ongoing_battles: 10
    },
    bot_players: {
      available_bots: 10,
      ongoing_bot_battles: 10
    },
    display_limits: {
      live_players: {
        max_my_bets: 50,
        max_available_bets: 50,
        max_ongoing_battles: 50
      },
      bot_players: {
        max_available_bots: 100,
        max_ongoing_bot_battles: 100
      }
    }
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { showSuccessRU, showErrorRU } = useNotifications();

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/interface-settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSettings(response.data);
    } catch (error) {
      console.error('Error fetching interface settings:', error);
      // Используем дефолтные значения если не удалось загрузить
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/interface-settings`, settings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      showSuccessRU('Настройки интерфейса успешно сохранены');
    } catch (error) {
      console.error('Error saving interface settings:', error);
      showErrorRU('Ошибка при сохранении настроек интерфейса');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (section, field, value) => {
    const numValue = parseInt(value);
    
    // Определяем лимиты в зависимости от типа поля
    let minVal, maxVal;
    if (field.startsWith('max_')) {
      minVal = 10;
      maxVal = 500;
    } else {
      minVal = 5;
      maxVal = 100;
    }
    
    if (numValue < minVal || numValue > maxVal) return;

    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: numValue
      }
    }));
  };

  const handleDisplayLimitChange = (section, field, value) => {
    const numValue = parseInt(value);
    if (numValue < 10 || numValue > 500) return;

    setSettings(prev => ({
      ...prev,
      display_limits: {
        ...prev.display_limits,
        [section]: {
          ...prev.display_limits[section],
          [field]: numValue
        }
      }
    }));
  };

  const handleReset = () => {
    setSettings({
      live_players: {
        my_bets: 10,
        available_bets: 10,
        ongoing_battles: 10
      },
      bot_players: {
        available_bots: 10,
        ongoing_bot_battles: 10
      }
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-white text-lg font-roboto">Загрузка настроек...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <h2 className="text-2xl font-russo text-accent-primary mb-2">Настройка интерфейса</h2>
        <p className="text-text-secondary font-roboto">
          Настройте количество элементов на странице для различных разделов интерфейса
        </p>
      </div>

      {/* Live Players Settings */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <h3 className="text-xl font-rajdhani font-bold text-white mb-4 flex items-center">
          <svg className="w-5 h-5 mr-2 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
          </svg>
          Live Players
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-rajdhani font-medium text-text-secondary mb-2">
              My Bets
            </label>
            <input
              type="number"
              min="5"
              max="100"
              value={settings.live_players.my_bets}
              onChange={(e) => handleChange('live_players', 'my_bets', e.target.value)}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
            />
            <p className="text-xs text-text-secondary mt-1">От 5 до 100 элементов</p>
          </div>
          
          <div>
            <label className="block text-sm font-rajdhani font-medium text-text-secondary mb-2">
              Available Bets
            </label>
            <input
              type="number"
              min="5"
              max="100"
              value={settings.live_players.available_bets}
              onChange={(e) => handleChange('live_players', 'available_bets', e.target.value)}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
            />
            <p className="text-xs text-text-secondary mt-1">От 5 до 100 элементов</p>
          </div>
          
          <div>
            <label className="block text-sm font-rajdhani font-medium text-text-secondary mb-2">
              Ongoing Battles
            </label>
            <input
              type="number"
              min="5"
              max="100"
              value={settings.live_players.ongoing_battles}
              onChange={(e) => handleChange('live_players', 'ongoing_battles', e.target.value)}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
            />
            <p className="text-xs text-text-secondary mt-1">От 5 до 100 элементов</p>
          </div>
        </div>
      </div>

      {/* Bot Players Settings */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <h3 className="text-xl font-rajdhani font-bold text-white mb-4 flex items-center">
          <svg className="w-5 h-5 mr-2 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3.5a1.5 1.5 0 1 1 3 0M12 3.5v2M7.5 7.5h9a3 3 0 0 1 3 3v6a3 3 0 0 1-3 3h-9a3 3 0 0 1-3-3v-6a3 3 0 0 1 3-3ZM9 12a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm6 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3ZM8.25 18h7.5M12 1.5v2" />
          </svg>
          Bot Players
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-rajdhani font-medium text-text-secondary mb-2">
              Available Bots
            </label>
            <input
              type="number"
              min="5"
              max="100"
              value={settings.bot_players.available_bots}
              onChange={(e) => handleChange('bot_players', 'available_bots', e.target.value)}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
            />
            <p className="text-xs text-text-secondary mt-1">От 5 до 100 элементов</p>
          </div>
          
          <div>
            <label className="block text-sm font-rajdhani font-medium text-text-secondary mb-2">
              Ongoing Bot Battles
            </label>
            <input
              type="number"
              min="5"
              max="100"
              value={settings.bot_players.ongoing_bot_battles}
              onChange={(e) => handleChange('bot_players', 'ongoing_bot_battles', e.target.value)}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
            />
            <p className="text-xs text-text-secondary mt-1">От 5 до 100 элементов</p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="text-text-secondary font-roboto">
            <p className="text-sm">Настройки будут применены ко всем пользователям</p>
            <p className="text-xs mt-1">Изменения вступят в силу после перезагрузки страницы</p>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-text-secondary hover:text-white hover:border-accent-primary transition-colors font-rajdhani font-medium"
            >
              Сброс
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-accent-primary hover:bg-accent-secondary text-white rounded-lg font-rajdhani font-medium transition-colors disabled:opacity-50"
            >
              {saving ? 'Сохранение...' : 'Сохранить'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterfaceSettings;