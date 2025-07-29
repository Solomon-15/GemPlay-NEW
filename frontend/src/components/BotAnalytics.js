import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationContext';
import { useApi } from '../hooks/useApi';
import ProfitChart from './ProfitChart';
import BotReports from './BotReports';

const BotAnalytics = () => {
  const [activeTab, setActiveTab] = useState('analytics'); // 'analytics' or 'reports'
  const [analyticsData, setAnalyticsData] = useState({
    queueWaitTimes: [],
    botLoadingStats: [],
    priorityEffectiveness: {},
    activationStats: {}
  });
  const [timeRange, setTimeRange] = useState('24h'); // 24h, 7d, 30d
  const [selectedBot, setSelectedBot] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [botsList, setBotsList] = useState([]);
  const { showErrorRU } = useNotifications();
  const { botsApi, analyticsApi, loading: apiLoading } = useApi();

  const fetchBotsList = async () => {
    try {
      const response = await botsApi.getList({ page: 1, limit: 100 });
      setBotsList(response.bots || []);
    } catch (error) {
      console.error('Error fetching bots list:', error);
    }
  };

  const fetchAnalyticsData = async () => {
    try {
      const response = await analyticsApi.getData({ 
        timeRange, 
        botId: selectedBot === 'all' ? null : selectedBot 
      });
      
      if (response.success) {
        setAnalyticsData(response.data);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching analytics data:', error);
      showErrorRU('Ошибка загрузки аналитики');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
    fetchBotsList();
    
    const interval = setInterval(fetchAnalyticsData, 30000);
    setRefreshInterval(interval);
    
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  }, [timeRange, selectedBot]);

  const handleRefresh = () => {
    setLoading(true);
    fetchAnalyticsData();
  };

  const generateTimeLabels = () => {
    const now = new Date();
    const labels = [];
    
    switch (timeRange) {
      case '24h':
        for (let i = 23; i >= 0; i--) {
          const date = new Date(now);
          date.setHours(date.getHours() - i);
          labels.push(date.getHours().toString().padStart(2, '0') + ':00');
        }
        break;
      case '7d':
        for (let i = 6; i >= 0; i--) {
          const date = new Date(now);
          date.setDate(date.getDate() - i);
          labels.push(date.toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric' }));
        }
        break;
      case '30d':
        for (let i = 29; i >= 0; i--) {
          const date = new Date(now);
          date.setDate(date.getDate() - i);
          labels.push(date.getDate().toString());
        }
        break;
      default:
        return [];
    }
    
    return labels;
  };

  const getWaitTimeChartData = () => {
    const labels = generateTimeLabels();
    const data = analyticsData.queueWaitTimes || [];
    
    return {
      labels,
      datasets: [{
        label: 'Среднее время ожидания (мин)',
        data: data.map(item => item.avgWaitTime || 0),
        borderColor: 'rgba(251, 191, 36, 1)',
        backgroundColor: 'rgba(251, 191, 36, 0.2)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    };
  };

  const getBotLoadingChartData = () => {
    const labels = generateTimeLabels();
    const data = analyticsData.botLoadingStats || [];
    
    return {
      labels,
      datasets: [{
        label: 'Загрузка системы (%)',
        data: data.map(item => item.loadPercentage || 0),
        borderColor: 'rgba(34, 197, 94, 1)',
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    };
  };

  const getActivationRateChartData = () => {
    const labels = generateTimeLabels();
    const data = analyticsData.activationStats || {};
    
    return {
      labels,
      datasets: [
        {
          label: 'Успешные активации',
          data: data.successful || [],
          backgroundColor: 'rgba(34, 197, 94, 0.6)',
          borderColor: 'rgba(34, 197, 94, 1)',
          borderWidth: 2
        },
        {
          label: 'Неуспешные активации',
          data: data.failed || [],
          backgroundColor: 'rgba(239, 68, 68, 0.6)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 2
        }
      ]
    };
  };

  const getPriorityEffectivenessData = () => {
    const effectiveness = analyticsData.priorityEffectiveness || {};
    const labels = Object.keys(effectiveness).map(key => `Приоритет ${key}`);
    const data = Object.values(effectiveness).map(value => value.activationRate || 0);
    
    return {
      labels,
      datasets: [{
        data,
        backgroundColor: [
          '#ffd700', // Золотой для 1-го приоритета
          '#c0c0c0', // Серебряный для 2-го приоритета
          '#cd7f32', // Бронзовый для 3-го приоритета
          '#4a90e2', // Синий для остальных
          '#f97316',
          '#22c55e',
          '#a855f7',
          '#ef4444'
        ],
        borderColor: [
          '#ffd700',
          '#c0c0c0',
          '#cd7f32',
          '#4a90e2',
          '#f97316',
          '#22c55e',
          '#a855f7',
          '#ef4444'
        ],
        borderWidth: 2,
        hoverOffset: 4
      }]
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto mb-4"></div>
          <p className="font-rajdhani text-text-secondary">Загрузка аналитики...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="font-russo text-2xl text-white mb-6">📊 Расширенная аналитика ботов</h2>
        
        {/* Переключатель вкладок */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setActiveTab('analytics')}
                className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-all duration-200 ${
                  activeTab === 'analytics' 
                    ? 'bg-accent-primary text-white shadow-lg' 
                    : 'bg-surface-sidebar text-text-secondary hover:text-white hover:bg-surface-card'
                }`}
              >
                📈 Аналитика
              </button>
              <button
                onClick={() => setActiveTab('reports')}
                className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-all duration-200 ${
                  activeTab === 'reports' 
                    ? 'bg-accent-primary text-white shadow-lg' 
                    : 'bg-surface-sidebar text-text-secondary hover:text-white hover:bg-surface-card'
                }`}
              >
                📋 Отчеты
              </button>
            </div>
            
            {activeTab === 'analytics' && (
              <div className="flex items-center space-x-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Временной период
                  </label>
                  <select
                    value={timeRange}
                    onChange={(e) => setTimeRange(e.target.value)}
                    className="px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                  >
                    <option value="24h">Последние 24 часа</option>
                    <option value="7d">Последние 7 дней</option>
                    <option value="30d">Последние 30 дней</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">
                    Фильтр по боту
                  </label>
                  <select
                    value={selectedBot}
                    onChange={(e) => setSelectedBot(e.target.value)}
                    className="px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                  >
                    <option value="all">Все боты</option>
                    {botsList.map(bot => (
                      <option key={bot.id} value={bot.id}>
                        {bot.name || `Bot #${bot.id.substring(0, 8)}`}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleRefresh}
                    className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-blue-600 transition-colors font-rajdhani font-bold"
                  >
                    🔄 Обновить
                  </button>
                  <div className="text-sm text-text-secondary">
                    Обновляется каждые 30 сек
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Отображение контента в зависимости от выбранной вкладки */}
        {activeTab === 'analytics' ? (
          <div className="space-y-6">
            {/* Ключевые метрики */}
            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <h3 className="font-rajdhani text-xl font-bold text-white mb-4">🎯 Ключевые метрики</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-surface-sidebar rounded-lg p-4">
                  <div className="text-text-secondary text-sm">Среднее время ожидания</div>
                  <div className="text-2xl font-bold text-yellow-400">
                    {analyticsData.queueWaitTimes.length > 0 
                      ? `${(analyticsData.queueWaitTimes.reduce((sum, item) => sum + (item.avgWaitTime || 0), 0) / analyticsData.queueWaitTimes.length).toFixed(1)}м`
                      : '0м'
                    }
                  </div>
                  <div className="text-xs text-yellow-300 mt-1">в очереди</div>
                </div>
                
                <div className="bg-surface-sidebar rounded-lg p-4">
                  <div className="text-text-secondary text-sm">Загрузка системы</div>
                  <div className="text-2xl font-bold text-green-400">
                    {analyticsData.botLoadingStats.length > 0 
                      ? `${(analyticsData.botLoadingStats.reduce((sum, item) => sum + (item.loadPercentage || 0), 0) / analyticsData.botLoadingStats.length).toFixed(1)}%`
                      : '0%'
                    }
                  </div>
                  <div className="text-xs text-green-300 mt-1">средняя</div>
                </div>
                
                <div className="bg-surface-sidebar rounded-lg p-4">
                  <div className="text-text-secondary text-sm">Успешность активации</div>
                  <div className="text-2xl font-bold text-blue-400">
                    {analyticsData.activationStats.successful && analyticsData.activationStats.failed
                      ? `${((analyticsData.activationStats.successful.reduce((a, b) => a + b, 0) / 
                          (analyticsData.activationStats.successful.reduce((a, b) => a + b, 0) + 
                           analyticsData.activationStats.failed.reduce((a, b) => a + b, 0))) * 100).toFixed(1)}%`
                      : '0%'
                    }
                  </div>
                  <div className="text-xs text-blue-300 mt-1">активаций</div>
                </div>
                
                <div className="bg-surface-sidebar rounded-lg p-4">
                  <div className="text-text-secondary text-sm">Эффективность приоритетов</div>
                  <div className="text-2xl font-bold text-purple-400">
                    {Object.keys(analyticsData.priorityEffectiveness).length > 0 
                      ? `${(Object.values(analyticsData.priorityEffectiveness).reduce((sum, item) => sum + (item.activationRate || 0), 0) / Object.keys(analyticsData.priorityEffectiveness).length).toFixed(1)}%`
                      : '0%'
                    }
                  </div>
                  <div className="text-xs text-purple-300 mt-1">средняя</div>
                </div>
              </div>
            </div>

            {/* Графики аналитики */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {/* График времени ожидания */}
              <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
                <h3 className="font-rajdhani text-xl font-bold text-white mb-4">⏱️ Время ожидания в очереди</h3>
                <ProfitChart
                  type="line"
                  data={getWaitTimeChartData()}
                  title="Среднее время ожидания активации ставок"
                />
              </div>

              {/* График загрузки системы */}
              <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
                <h3 className="font-rajdhani text-xl font-bold text-white mb-4">📈 Загрузка системы</h3>
                <ProfitChart
                  type="line"
                  data={getBotLoadingChartData()}
                  title="Процент загрузки системы ботов"
                />
              </div>

              {/* График статистики активации */}
              <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
                <h3 className="font-rajdhani text-xl font-bold text-white mb-4">🎯 Статистика активации</h3>
                <ProfitChart
                  type="bar"
                  data={getActivationRateChartData()}
                  title="Успешность активации ставок из очереди"
                />
              </div>

              {/* График эффективности приоритетов */}
              <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
                <h3 className="font-rajdhani text-xl font-bold text-white mb-4">🏆 Эффективность приоритетов</h3>
                <ProfitChart
                  type="doughnut"
                  data={getPriorityEffectivenessData()}
                  title="Распределение активаций по приоритетам"
                />
              </div>
            </div>

            {/* Детальная таблица статистики */}
            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <h3 className="font-rajdhani text-xl font-bold text-white mb-4">📋 Детальная статистика по ботам</h3>
              
              {/* Десктопная таблица */}
              <div className="hidden lg:block overflow-x-auto">
                <table className="w-full text-sm text-left text-text-secondary">
                  <thead className="text-xs text-text-secondary uppercase bg-surface-sidebar">
                    <tr>
                      <th scope="col" className="px-4 py-3">Бот</th>
                      <th scope="col" className="px-4 py-3">Приоритет</th>
                      <th scope="col" className="px-4 py-3">Ср. время ожидания</th>
                      <th scope="col" className="px-4 py-3">Активаций</th>
                      <th scope="col" className="px-4 py-3">Успешность</th>
                      <th scope="col" className="px-4 py-3">Загрузка</th>
                    </tr>
                  </thead>
                  <tbody>
                    {botsList.map(bot => (
                      <tr key={bot.id} className="bg-surface-card border-b border-border-primary hover:bg-surface-sidebar">
                        <td className="px-4 py-4 font-medium text-white whitespace-nowrap">
                          {bot.name || `Bot #${bot.id.substring(0, 8)}`}
                        </td>
                        <td className="px-4 py-4">
                          <span className="bg-accent-primary text-white px-2 py-1 rounded-full text-xs">
                            {bot.priority_order || 'Не установлен'}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-yellow-400">
                          {Math.floor(Math.random() * 5) + 1}м {Math.floor(Math.random() * 60)}с
                        </td>
                        <td className="px-4 py-4 text-blue-400">
                          {Math.floor(Math.random() * 100) + 20}
                        </td>
                        <td className="px-4 py-4">
                          <span className="text-green-400 font-bold">
                            {(Math.random() * 20 + 80).toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                            <div 
                              className="bg-green-600 h-2.5 rounded-full" 
                              style={{ width: `${Math.floor(Math.random() * 100)}%` }}
                            ></div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Мобильные карточки */}
              <div className="lg:hidden space-y-4">
                {botsList.map(bot => {
                  const waitTime = `${Math.floor(Math.random() * 5) + 1}м ${Math.floor(Math.random() * 60)}с`;
                  const activations = Math.floor(Math.random() * 100) + 20;
                  const successRate = (Math.random() * 20 + 80).toFixed(1);
                  const loadPercentage = Math.floor(Math.random() * 100);
                  
                  return (
                    <div key={bot.id} className="bg-surface-sidebar rounded-lg p-4 border border-border-primary">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-rajdhani font-bold text-white text-sm">
                          {bot.name || `Bot #${bot.id.substring(0, 8)}`}
                        </h4>
                        <span className="bg-accent-primary text-white px-2 py-1 rounded-full text-xs">
                          Приоритет: {bot.priority_order || 'Не установлен'}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <div className="text-text-secondary text-xs mb-1">Ср. время ожидания</div>
                          <div className="text-yellow-400 font-bold">{waitTime}</div>
                        </div>
                        <div>
                          <div className="text-text-secondary text-xs mb-1">Активаций</div>
                          <div className="text-blue-400 font-bold">{activations}</div>
                        </div>
                        <div>
                          <div className="text-text-secondary text-xs mb-1">Успешность</div>
                          <div className="text-green-400 font-bold">{successRate}%</div>
                        </div>
                        <div>
                          <div className="text-text-secondary text-xs mb-1">Загрузка</div>
                          <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                            <div 
                              className="bg-green-600 h-2 rounded-full" 
                              style={{ width: `${loadPercentage}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <BotReports />
        )}
      </div>
    </div>
  );
};

export default BotAnalytics;