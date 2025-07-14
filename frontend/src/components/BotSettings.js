import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BotSettings = ({ user }) => {
  const [settings, setSettings] = useState({
    globalMaxActiveBets: 50,
    globalMaxHumanBots: 30,
    paginationSize: 10,
    autoActivateFromQueue: true,
    priorityType: 'order' // 'order' or 'manual'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [queueStats, setQueueStats] = useState({
    totalActiveRegularBets: 0,
    totalQueuedBets: 0,
    totalRegularBots: 0,
    totalHumanBots: 0
  });
  const { showSuccessRU, showErrorRU } = useNotifications();

  useEffect(() => {
    fetchBotSettings();
    fetchQueueStats();
  }, []);

  const fetchBotSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bot-settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setSettings(response.data.settings);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching bot settings:', error);
      showErrorRU('Ошибка загрузки настроек ботов');
      setLoading(false);
    }
  };

  const fetchQueueStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bot-queue-stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setQueueStats(response.data.stats);
      }
    } catch (error) {
      console.error('Error fetching queue stats:', error);
    }
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(`${API}/admin/bot-settings`, settings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        showSuccessRU('Настройки ботов успешно сохранены');
        fetchQueueStats(); // Обновляем статистику
      }
    } catch (error) {
      console.error('Error saving bot settings:', error);
      showErrorRU('Ошибка сохранения настроек ботов');
    } finally {
      setSaving(false);
    }
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto mb-4"></div>
          <p className="font-rajdhani text-text-secondary">Загрузка настроек ботов...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="font-russo text-2xl text-white mb-6">Настройки ботов</h2>
        
        {/* Статистика очереди */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">📊 Статистика очереди</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Активных ставок обычных ботов</div>
              <div className="text-2xl font-bold text-blue-400">{queueStats.totalActiveRegularBets}</div>
              <div className="text-xs text-blue-300 mt-1">из {settings.globalMaxActiveBets} максимум</div>
            </div>
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Ставок в очереди</div>
              <div className="text-2xl font-bold text-orange-400">{queueStats.totalQueuedBets}</div>
              <div className="text-xs text-orange-300 mt-1">ожидают активации</div>
            </div>
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Обычных ботов</div>
              <div className="text-2xl font-bold text-green-400">{queueStats.totalRegularBots}</div>
              <div className="text-xs text-green-300 mt-1">активных</div>
            </div>
            <div className="bg-surface-sidebar rounded-lg p-4">
              <div className="text-text-secondary text-sm">Human ботов</div>
              <div className="text-2xl font-bold text-purple-400">{queueStats.totalHumanBots}</div>
              <div className="text-xs text-purple-300 mt-1">активных</div>
            </div>
          </div>
        </div>

        {/* Глобальные настройки */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">🌐 Глобальные настройки</h3>
          
          <div className="space-y-6">
            {/* Лимит активных ставок обычных ботов */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Максимальное количество активных ставок обычных ботов
                </label>
                <input
                  type="number"
                  min="1"
                  max="200"
                  value={settings.globalMaxActiveBets}
                  onChange={(e) => handleSettingChange('globalMaxActiveBets', parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                />
                <p className="text-xs text-text-secondary mt-1">
                  Общий лимит активных ставок всех обычных ботов в блоке "Available Bots"
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Максимальное количество активных ставок Human ботов
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={settings.globalMaxHumanBots}
                  onChange={(e) => handleSettingChange('globalMaxHumanBots', parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                />
                <p className="text-xs text-text-secondary mt-1">
                  Общий лимит активных ставок всех Human ботов
                </p>
              </div>
            </div>

            {/* Настройки пагинации */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Размер пагинации в "Available Bots"
                </label>
                <select
                  value={settings.paginationSize}
                  onChange={(e) => handleSettingChange('paginationSize', parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                >
                  <option value={5}>5 ставок на страницу</option>
                  <option value={10}>10 ставок на страницу</option>
                  <option value={15}>15 ставок на страницу</option>
                  <option value={20}>20 ставок на страницу</option>
                  <option value={25}>25 ставок на страницу</option>
                </select>
                <p className="text-xs text-text-secondary mt-1">
                  Количество ставок на одной странице
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Автоматическая активация из очереди
                </label>
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={settings.autoActivateFromQueue}
                    onChange={(e) => handleSettingChange('autoActivateFromQueue', e.target.checked)}
                    className="w-4 h-4 text-accent-primary bg-surface-sidebar border border-border-primary rounded focus:ring-accent-primary"
                  />
                  <span className="text-white">Включить автоматическую активацию</span>
                </div>
                <p className="text-xs text-text-secondary mt-1">
                  Автоматически активировать ставки из очереди при освобождении слотов
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Система приоритетов */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">⚡ Система приоритетов</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Тип приоритета активации из очереди
              </label>
              <select
                value={settings.priorityType}
                onChange={(e) => handleSettingChange('priorityType', e.target.value)}
                className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
              >
                <option value="order">По порядку в списке ботов</option>
                <option value="manual">Ручное управление приоритетом</option>
              </select>
              <p className="text-xs text-text-secondary mt-1">
                Определяет порядок активации ставок из очереди
              </p>
            </div>

            {settings.priorityType === 'order' && (
              <div className="bg-blue-900 bg-opacity-20 border border-blue-500 border-opacity-30 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4 className="font-rajdhani text-sm font-bold text-blue-400">Режим "По порядку"</h4>
                </div>
                <p className="text-xs text-text-secondary">
                  Приоритет определяется порядком ботов в списке. Первый в списке имеет высший приоритет.
                </p>
              </div>
            )}

            {settings.priorityType === 'manual' && (
              <div className="bg-orange-900 bg-opacity-20 border border-orange-500 border-opacity-30 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <h4 className="font-rajdhani text-sm font-bold text-orange-400">Режим "Ручное управление"</h4>
                </div>
                <p className="text-xs text-text-secondary">
                  Приоритет настраивается вручную с помощью кнопок "Вверх/Вниз" в списке ботов.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Кнопки действий */}
        <div className="flex justify-end space-x-4">
          <button
            onClick={fetchBotSettings}
            className="px-6 py-3 font-rajdhani font-bold text-text-secondary border border-border-primary rounded-lg hover:text-white hover:border-accent-primary transition-colors duration-200"
          >
            Сбросить изменения
          </button>
          
          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className={`px-6 py-3 font-rajdhani font-bold rounded-lg transition-all duration-200 ${
              saving 
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                : 'bg-accent-primary hover:bg-blue-600 text-white'
            }`}
          >
            {saving ? (
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>Сохранение...</span>
              </div>
            ) : (
              'Сохранить настройки'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BotSettings;