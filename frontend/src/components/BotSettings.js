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
            <div className="bg-blue-900 bg-opacity-20 border border-blue-500 border-opacity-30 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-400">{queueStats.totalActiveRegularBets || 0}</div>
              <div className="text-sm text-text-secondary">Активные ставки обычных ботов</div>
              <div className="text-xs text-blue-300 mt-1">из {settings.globalMaxActiveBets} максимум</div>
            </div>
            <div className="bg-green-900 bg-opacity-20 border border-green-500 border-opacity-30 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-400">{queueStats.totalQueuedBets || 0}</div>
              <div className="text-sm text-text-secondary">Ставки в очереди</div>
              <div className="text-xs text-green-300 mt-1">ожидают активации</div>
            </div>
            <div className="bg-purple-900 bg-opacity-20 border border-purple-500 border-opacity-30 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-400">{queueStats.totalRegularBots || 0}</div>
              <div className="text-sm text-text-secondary">Обычные боты</div>
              <div className="text-xs text-purple-300 mt-1">всего активных</div>
            </div>
            <div className="bg-orange-900 bg-opacity-20 border border-orange-500 border-opacity-30 rounded-lg p-4">
              <div className="text-2xl font-bold text-orange-400">{queueStats.totalHumanBots || 0}</div>
              <div className="text-sm text-text-secondary">Human боты</div>
              <div className="text-xs text-orange-300 mt-1">всего активных</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BotSettings;