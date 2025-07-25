import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import useConfirmation from '../hooks/useConfirmation';
import useInput from '../hooks/useInput';
import InputModal from './InputModal';
import ConfirmationModal from './ConfirmationModal';
import HumanBotsList from './HumanBotsList';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HumanBotsManagement = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { addNotification } = useNotifications();
  const { confirm, confirmationModal } = useConfirmation();
  const { prompt, inputModal } = useInput();
  const [humanBots, setHumanBots] = useState([]);
  const [stats, setStats] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    character: '',
    is_active: null
  });

  // Состояние для табов
  const [activeTab, setActiveTab] = useState('bots'); // 'bots' или 'settings'

  // Состояние для настроек Human-ботов
  const [humanBotSettings, setHumanBotSettings] = useState({
    max_active_bets_human: 100,
    auto_play_enabled: false,
    min_delay_seconds: 1,
    max_delay_seconds: 3600,
    play_with_players_enabled: false,
    max_concurrent_games: 3,
    current_usage: {
      total_individual_limits: 0,
      max_limit: 100,
      available: 100,
      usage_percentage: 0
    }
  });
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);

  // Helper function to execute API operations
  const executeOperation = async (endpoint, method = 'GET', data = null) => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      const config = {
        method,
        url: `${API}${endpoint}`,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      };
      
      if (data) {
        if (method === 'GET') {
          config.params = data;
        } else {
          config.data = data;
        }
      }
      
      const response = await axios(config);
      return response.data;
    } catch (err) {
      let errorMessage = 'Ошибка API запроса';
      
      // Handle different error response formats
      if (err.response?.data) {
        const errorData = err.response.data;
        
        // Handle FastAPI validation errors (array format)
        if (Array.isArray(errorData) && errorData.length > 0) {
          errorMessage = errorData.map(e => e.msg || e.message || 'Validation error').join(', ');
        }
        // Handle standard error with detail
        else if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : 'Validation error';
        }
        // Handle error message
        else if (errorData.message) {
          errorMessage = errorData.message;
        }
        // Handle error as string
        else if (typeof errorData === 'string') {
          errorMessage = errorData;
        }
      }
      // Fallback to error message
      else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const characters = [
    { value: 'STABLE', label: 'Стабильный', description: 'Ровные небольшие ставки' },
    { value: 'AGGRESSIVE', label: 'Агрессивный', description: 'Крупные ставки, высокий риск' },
    { value: 'CAUTIOUS', label: 'Осторожный', description: 'Мелкие ставки, низкая волатильность' },
    { value: 'BALANCED', label: 'Балансированный', description: 'Средние ставки и стратегия' },
    { value: 'IMPULSIVE', label: 'Импульсивный', description: 'Случайные всплески активности' },
    { value: 'ANALYST', label: 'Аналитик', description: 'Адаптивная стратегия' },
    { value: 'MIMIC', label: 'Мимик', description: 'Копирует поведение оппонентов' }
  ];

  const [createFormData, setCreateFormData] = useState({
    name: '',
    character: 'BALANCED',
    min_bet: 1,
    max_bet: 100,
    bet_limit: 12,
    win_percentage: 40,
    loss_percentage: 40,
    draw_percentage: 20,
    min_delay: 30,
    max_delay: 120,
    use_commit_reveal: true,
    logging_level: 'INFO',
    can_play_with_other_bots: true,
    can_play_with_players: true
  });

  const [bulkCreateData, setBulkCreateData] = useState({
    count: 10,
    character: 'BALANCED',
    min_bet_range: [1, 50],
    max_bet_range: [50, 200],
    bet_limit_range: [12, 12],
    win_percentage: 40,
    loss_percentage: 40,
    draw_percentage: 20,
    delay_range: [30, 120],
    use_commit_reveal: true,
    logging_level: 'INFO'
  });

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showBulkCreateForm, setShowBulkCreateForm] = useState(false);
  const [editingBot, setEditingBot] = useState(null);

  useEffect(() => {
    fetchHumanBots();
    fetchStats();
  }, [currentPage, filters]);

  const fetchHumanBots = async () => {
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '10'
      });
      
      if (filters.character) params.append('character', filters.character);
      if (filters.is_active !== null) params.append('is_active', filters.is_active.toString());

      const response = await executeOperation('/admin/human-bots?' + params.toString(), 'GET');
      if (response.success !== false) {
        setHumanBots(response.bots || []);
        setTotalPages(response.total_pages || 1);
      }
    } catch (error) {
      console.error('Ошибка получения Human-ботов:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await executeOperation('/admin/human-bots/stats', 'GET');
      if (response.success !== false) {
        setStats(response);
      }
    } catch (error) {
      console.error('Ошибка получения статистики:', error);
    }
  };

  const fetchHumanBotSettings = async () => {
    try {
      setSettingsLoading(true);
      const response = await executeOperation('/admin/human-bots/settings', 'GET');
      if (response.success !== false) {
        setHumanBotSettings(response.settings);
      }
    } catch (error) {
      console.error('Ошибка получения настроек Human-ботов:', error);
    } finally {
      setSettingsLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setSettingsSaving(true);
      const response = await executeOperation('/admin/human-bots/update-settings', 'POST', {
        max_active_bets_human: humanBotSettings.max_active_bets_human,
        auto_play_enabled: humanBotSettings.auto_play_enabled || false,
        min_delay_seconds: humanBotSettings.min_delay_seconds || 1,
        max_delay_seconds: humanBotSettings.max_delay_seconds || 3600,
        play_with_players_enabled: humanBotSettings.play_with_players_enabled || false,
        max_concurrent_games: humanBotSettings.max_concurrent_games || 3
      });
      
      if (response.success !== false) {
        alert(response.message || 'Настройки сохранены успешно');
        // Обновить настройки после сохранения
        await fetchHumanBotSettings();
        // Обновить список ботов если были изменения
        if (response.adjusted_bots_count > 0) {
          await fetchHumanBots();
        }
      }
    } catch (error) {
      console.error('Ошибка сохранения настроек:', error);
    } finally {
      setSettingsSaving(false);
    }
  };

  // Обновленный useEffect для загрузки настроек при переключении на вкладку настроек
  useEffect(() => {
    if (activeTab === 'settings') {
      fetchHumanBotSettings();
    }
  }, [activeTab]);

  const handleCreateBot = async () => {
    if (createFormData.win_percentage + createFormData.loss_percentage + createFormData.draw_percentage !== 100) {
      alert('Сумма процентов должна равняться 100%');
      return;
    }

    try {
      let response;
      if (editingBot) {
        // Edit existing bot
        response = await executeOperation(`/admin/human-bots/${editingBot.id}`, 'PUT', createFormData);
      } else {
        // Create new bot
        response = await executeOperation('/admin/human-bots', 'POST', createFormData);
      }
      
      if (response.success !== false) {
        const action = editingBot ? 'отредактирован' : 'создан';
        const botName = createFormData.name || 'Human-бот';
        addNotification(`Human-бот "${botName}" успешно ${action}`, 'success');
        
        setShowCreateForm(false);
        setEditingBot(null);
        setCreateFormData({
          name: '',
          character: 'BALANCED',
          min_bet: 1,
          max_bet: 100,
          bet_limit: 12,
          win_percentage: 40,
          loss_percentage: 40,
          draw_percentage: 20,
          min_delay: 30,
          max_delay: 120,
          use_commit_reveal: true,
          logging_level: 'INFO'
        });
        fetchHumanBots();
        fetchStats();
      }
    } catch (error) {
      console.error('Ошибка создания/редактирования Human-бота:', error);
    }
  };

  const handleBulkCreate = async () => {
    if (bulkCreateData.win_percentage + bulkCreateData.loss_percentage + bulkCreateData.draw_percentage !== 100) {
      alert('Сумма процентов должна равняться 100%');
      return;
    }

    try {
      const response = await executeOperation('/admin/human-bots/bulk-create', 'POST', bulkCreateData);
      if (response.success !== false) {
        addNotification(`Массовое создание завершено: создано ${bulkCreateData.count} Human-ботов`, 'success');
        setShowBulkCreateForm(false);
        fetchHumanBots();
        fetchStats();
        alert(`Создано ${response.created_count} ботов${response.failed_count > 0 ? `, не удалось создать: ${response.failed_count}` : ''}`);
      }
    } catch (error) {
      console.error('Ошибка массового создания Human-ботов:', error);
    }
  };

  const handleToggleStatus = async (botId) => {
    try {
      const response = await executeOperation(`/admin/human-bots/${botId}/toggle-status`, 'POST');
      if (response.success !== false) {
        const bot = humanBots.find(b => b.id === botId);
        const botName = bot?.name || 'Human-бот';
        const action = bot?.is_active ? 'деактивирован' : 'активирован';
        addNotification(`Human-бот "${botName}" успешно ${action}`, 'success');
        fetchHumanBots();
        fetchStats();
      }
    } catch (error) {
      console.error('Ошибка переключения статуса:', error);
    }
  };

  const handleDeleteBot = async (botId, botName) => {
    confirm({
      title: "Удаление Human-бота",
      message: `Вы уверены, что хотите удалить Human-бота "${botName}"?`,
      type: "danger",
      onConfirm: async () => {
        try {
          const response = await executeOperation(`/admin/human-bots/${botId}`, 'DELETE');
          if (response.success !== false) {
            fetchHumanBots();
            fetchStats();
          }
        } catch (error) {
          console.error('Ошибка удаления Human-бота:', error);
        }
      }
    });
  };

  const handleToggleAll = async (activate) => {
    const confirmed = await confirm({
      title: `${activate ? 'Активация' : 'Деактивация'} всех Human-ботов`,
      message: `Вы уверены, что хотите ${activate ? 'активировать' : 'деактивировать'} всех Human-ботов?`,
      type: activate ? "success" : "warning"
    });
    
    if (confirmed) {
      try {
        const response = await executeOperation('/admin/human-bots/toggle-all', 'POST', { activate });
        if (response.success !== false) {
          const action = activate ? 'активированы' : 'деактивированы';
          const count = response.affected_count || 0;
          addNotification(`Массовая операция завершена: ${count} Human-ботов ${action}`, 'success');
          fetchHumanBots();
          fetchStats();
          alert(`${activate ? 'Активировано' : 'Деактивировано'} ${response.affected_count} ботов`);
        }
      } catch (error) {
        console.error('Ошибка массового переключения статуса:', error);
      }
    }
  };

  const getCharacterLabel = (character) => {
    const found = characters.find(c => c.value === character);
    return found ? found.label : character;
  };

  const getStatusColor = (isActive) => {
    return isActive ? 'green' : 'red';
  };

  const formatCurrency = (amount) => {
    return `$${amount.toFixed(2)}`;
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  return (
    <div className="human-bots-management">
      <div className="bots-header">
        <h2>Управление Human-ботами</h2>
      </div>

      {/* Табы */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="flex border-b border-border-primary">
          <button
            onClick={() => setActiveTab('bots')}
            className={`flex-1 px-6 py-4 text-center font-rajdhani font-bold transition-colors ${
              activeTab === 'bots'
                ? 'bg-accent-primary text-white border-b-2 border-accent-primary'
                : 'text-text-secondary hover:text-white hover:bg-surface-sidebar'
            }`}
          >
            📋 Список ботов
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`flex-1 px-6 py-4 text-center font-rajdhani font-bold transition-colors ${
              activeTab === 'settings'
                ? 'bg-accent-primary text-white border-b-2 border-accent-primary'
                : 'text-text-secondary hover:text-white hover:bg-surface-sidebar'
            }`}
          >
            ⚙️ Настройки
          </button>
        </div>

        {/* Содержимое табов */}
        <div className="p-6">
          {activeTab === 'bots' && (
            <div className="space-y-6">
              {/* Действия для ботов */}
              <div className="flex flex-wrap gap-3 mb-6">
                <button
                  className="styled-btn btn-primary"
                  onClick={() => setShowCreateForm(true)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Создать бота
                </button>
                <button
                  className="styled-btn btn-secondary"
                  onClick={() => setShowBulkCreateForm(true)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  Массовое создание
                </button>
                <button
                  className="styled-btn btn-success"
                  onClick={() => handleToggleAll(true)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Активировать всех
                </button>
                <button
                  className="styled-btn btn-warning"
                  onClick={() => handleToggleAll(false)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Деактивировать всех
                </button>
              </div>

              {/* Statistics */}
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Количество ботов</h3>
                  <div className="stat-value">{stats.total_bots || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Ожидающие</h3>
                  <div className="stat-value">{stats.total_bets || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Активные</h3>
                  <div className="stat-value">{stats.active_games || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="flex justify-between items-center">
                    <h3>Всего Игр</h3>
                    <button
                      onClick={() => handleResetTotalGames()}
                      className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                      title="Сбросить счетчик всего игр"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
                  <div className="stat-value">{stats.total_games_played || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="flex justify-between items-center">
                    <h3>Доход за Период</h3>
                    <button
                      onClick={() => handleResetPeriodRevenue()}
                      className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                      title="Сбросить доход за период"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
                  <div className="stat-value">{formatCurrency(stats.period_revenue || 0)}</div>
                </div>
              </div>

              {/* Filters */}
              <div className="filters-section">
                <div className="filter-group">
                  <label>Характер:</label>
                  <select 
                    value={filters.character} 
                    onChange={(e) => setFilters({...filters, character: e.target.value})}
                  >
                    <option value="">Все</option>
                    {characters.map(char => (
                      <option key={char.value} value={char.value}>
                        {char.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="filter-group">
                  <label>Статус:</label>
                  <select 
                    value={filters.is_active || ''} 
                    onChange={(e) => setFilters({...filters, is_active: e.target.value === '' ? null : e.target.value === 'true'})}
                  >
                    <option value="">Все</option>
                    <option value="true">Активные</option>
                    <option value="false">Неактивные</option>
                  </select>
                </div>
              </div>

              {/* Human Bots List */}
              <HumanBotsList 
                onEditBot={(bot) => {
                  setEditingBot(bot);
                  setCreateFormData({
                    name: bot.name || '',
                    character: bot.character || 'BALANCED',
                    min_bet: bot.min_bet || 1,
                    max_bet: bot.max_bet || 100,
                    bet_limit: bot.bet_limit || 12,
                    win_percentage: bot.win_percentage || 40,
                    loss_percentage: bot.loss_percentage || 40,
                    draw_percentage: bot.draw_percentage || 20,
                    min_delay: bot.min_delay || 30,
                    max_delay: bot.max_delay || 120,
                    use_commit_reveal: bot.use_commit_reveal !== undefined ? bot.use_commit_reveal : true,
                    logging_level: bot.logging_level || 'INFO'
                  });
                  setShowCreateForm(true);
                }}
                onCreateBot={() => setShowCreateForm(true)}
              />
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              {/* Настройки лимитов Human-ботов */}
              <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-green-600 rounded-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="font-rajdhani text-xl font-bold text-white">
                        Глобальные настройки Human-ботов
                      </h3>
                      <p className="text-text-secondary font-roboto">
                        Управление общими лимитами для всех Human-ботов
                      </p>
                    </div>
                  </div>
                </div>

                {settingsLoading ? (
                  <div className="text-center py-8">
                    <div className="text-accent-primary text-2xl mb-2">⏳</div>
                    <p className="text-text-secondary">Загрузка настроек...</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Текущее использование */}
                    <div className="bg-surface-sidebar rounded-lg p-4">
                      <h4 className="font-rajdhani font-bold text-white mb-3">Текущее использование</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="text-accent-primary font-bold text-lg">
                            {humanBotSettings.current_usage?.total_individual_limits || 0}
                          </div>
                          <div className="text-text-secondary text-sm">Использовано</div>
                        </div>
                        <div className="text-center">
                          <div className="text-white font-bold text-lg">
                            {humanBotSettings.current_usage?.max_limit || 100}
                          </div>
                          <div className="text-text-secondary text-sm">Максимум</div>
                        </div>
                        <div className="text-center">
                          <div className="text-green-400 font-bold text-lg">
                            {humanBotSettings.current_usage?.available || 0}
                          </div>
                          <div className="text-text-secondary text-sm">Доступно</div>
                        </div>
                        <div className="text-center">
                          <div className="text-orange-400 font-bold text-lg">
                            {humanBotSettings.current_usage?.usage_percentage || 0}%
                          </div>
                          <div className="text-text-secondary text-sm">Использование</div>
                        </div>
                      </div>

                      {/* Прогресс бар */}
                      <div className="mt-4">
                        <div className="bg-surface-primary rounded-full h-3 overflow-hidden">
                          <div 
                            className="bg-accent-primary h-full transition-all duration-300"
                            style={{ 
                              width: `${Math.min(humanBotSettings.current_usage?.usage_percentage || 0, 100)}%` 
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Настройки автоигры между Human-ботами */}
                    <div className="bg-surface-sidebar rounded-lg p-4">
                      <h4 className="font-rajdhani font-bold text-white mb-3">🎮 Автоигра между Human-ботами</h4>
                      <div className="space-y-4">
                        {/* Глобальный переключатель */}
                        <div className="flex items-center justify-between">
                          <div>
                            <label className="font-rajdhani font-bold text-white">
                              Включить автоигру между Human-ботами
                            </label>
                            <p className="text-text-secondary text-sm">
                              Позволяет Human-ботам автоматически присоединяться к ставкам других Human-ботов и игроков
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={humanBotSettings.auto_play_enabled || false}
                              onChange={(e) => setHumanBotSettings({
                                ...humanBotSettings,
                                auto_play_enabled: e.target.checked
                              })}
                              className="sr-only peer"
                              disabled={settingsSaving}
                            />
                            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent-primary peer-focus:ring-opacity-25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-primary"></div>
                          </label>
                        </div>

                        {/* Настройка диапазона задержки */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block font-rajdhani font-bold text-white mb-2">
                              Минимальная задержка (секунды)
                            </label>
                            <input
                              type="number"
                              min="1"
                              max="3600"
                              value={humanBotSettings.min_delay_seconds || 1}
                              onChange={(e) => setHumanBotSettings({
                                ...humanBotSettings,
                                min_delay_seconds: parseInt(e.target.value) || 1
                              })}
                              className="w-full px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                              disabled={settingsSaving}
                            />
                          </div>
                          <div>
                            <label className="block font-rajdhani font-bold text-white mb-2">
                              Максимальная задержка (секунды)
                            </label>
                            <input
                              type="number"
                              min="1"
                              max="3600"
                              value={humanBotSettings.max_delay_seconds || 3600}
                              onChange={(e) => setHumanBotSettings({
                                ...humanBotSettings,
                                max_delay_seconds: parseInt(e.target.value) || 3600
                              })}
                              className="w-full px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                              disabled={settingsSaving}
                            />
                          </div>
                        </div>
                        
                        {/* Новое поле для максимального количества одновременных игр */}
                        <div>
                          <label className="block font-rajdhani font-bold text-white mb-2">
                            Макс. одновременных игр
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="50"
                            value={humanBotSettings.max_concurrent_games || 3}
                            onChange={(e) => setHumanBotSettings({
                              ...humanBotSettings,
                              max_concurrent_games: parseInt(e.target.value) || 3
                            })}
                            className="w-full px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                            disabled={settingsSaving}
                          />
                          <p className="text-text-secondary text-xs mt-1">
                            Максимальное количество игр, в которых Human-бот может участвовать одновременно
                          </p>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                          <div className="flex-1 text-text-secondary text-sm">
                            💡 Human-боты будут присоединяться к доступным ставкам с случайной задержкой от {humanBotSettings.min_delay_seconds || 1} до {humanBotSettings.max_delay_seconds || 3600} секунд ({Math.round((humanBotSettings.max_delay_seconds || 3600) / 60)} минут)
                          </div>
                          <button
                            onClick={handleSaveSettings}
                            disabled={settingsSaving}
                            className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-opacity-80 transition-colors disabled:opacity-50"
                          >
                            {settingsSaving ? 'Сохранение...' : 'Сохранить'}
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Новый переключатель для игры с игроками */}
                    <div className="bg-surface-sidebar rounded-lg p-4">
                      <h4 className="font-rajdhani font-bold text-white mb-3">👥 Игра с живыми игроками</h4>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <label className="font-rajdhani font-bold text-white">
                              Включить игру с Игроками
                            </label>
                            <p className="text-text-secondary text-sm">
                              Позволяет Human-ботам играть с живыми игроками
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={humanBotSettings.play_with_players_enabled || false}
                              onChange={(e) => setHumanBotSettings({
                                ...humanBotSettings,
                                play_with_players_enabled: e.target.checked
                              })}
                              className="sr-only peer"
                              disabled={settingsSaving}
                            />
                            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent-primary peer-focus:ring-opacity-25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-primary"></div>
                          </label>
                        </div>
                      </div>
                    </div>

                    {/* Настройка максимального лимита */}
                    <div className="space-y-4">
                      <div>
                        <label className="block font-rajdhani font-bold text-white mb-2">
                          Максимум активных ставок для всех Human-ботов
                        </label>
                        <div className="flex items-center space-x-4">
                          <input
                            type="number"
                            min="1"
                            max="1000"
                            value={humanBotSettings.max_active_bets_human || 100}
                            onChange={(e) => setHumanBotSettings({
                              ...humanBotSettings,
                              max_active_bets_human: parseInt(e.target.value) || 100
                            })}
                            className="flex-1 max-w-xs px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                            disabled={settingsSaving}
                          />
                          <button
                            onClick={handleSaveSettings}
                            disabled={settingsSaving}
                            className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-opacity-80 transition-colors disabled:opacity-50"
                          >
                            {settingsSaving ? 'Сохранение...' : 'Сохранить'}
                          </button>
                        </div>
                        <p className="text-text-secondary text-sm mt-2">
                          💡 При уменьшении лимита индивидуальные лимиты ботов будут автоматически скорректированы пропорционально
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Bot Form */}
      {showCreateForm && (
        <div className="modal-overlay">
          <div className="modal-content large-modal styled-modal">
            <div className="modal-header">
              <div className="modal-title">
                <svg className="modal-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <h3>{editingBot ? 'Редактировать Human-бота' : 'Создать Human-бота'}</h3>
              </div>
              <button 
                type="button" 
                className="modal-close"
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingBot(null);
                }}
              >
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <form onSubmit={(e) => { e.preventDefault(); handleCreateBot(); }}>
              {/* Основная информация */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4>Основная информация</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                      Имя бота *
                    </label>
                    <input
                      type="text"
                      value={createFormData.name}
                      onChange={(e) => setCreateFormData({...createFormData, name: e.target.value})}
                      placeholder="Введите имя бота"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      Характер *
                    </label>
                    <select
                      value={createFormData.character}
                      onChange={(e) => setCreateFormData({...createFormData, character: e.target.value})}
                    >
                      {characters.map(char => (
                        <option key={char.value} value={char.value} title={char.description}>
                          {char.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Настройки ставок */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                  <h4>Настройки ставок</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      Мин. ставка (гемы)
                    </label>
                    <input
                      type="number"
                      step="1"
                      min="1"
                      value={createFormData.min_bet}
                      onChange={(e) => setCreateFormData({...createFormData, min_bet: parseInt(e.target.value) || 1})}
                      placeholder="1"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Макс. ставка (гемы)
                    </label>
                    <input
                      type="number"
                      step="1"
                      min="1"
                      value={createFormData.max_bet}
                      onChange={(e) => setCreateFormData({...createFormData, max_bet: parseInt(e.target.value) || 1})}
                      placeholder="100"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      Лимит ставок
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={createFormData.bet_limit}
                      onChange={(e) => setCreateFormData({...createFormData, bet_limit: parseInt(e.target.value)})}
                      placeholder="12"
                    />
                    <small className="form-help">Макс. количество одновременных ставок (1-100)</small>
                  </div>
                </div>
              </div>

              {/* Настройки результатов */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h4>Настройки результатов</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      % Побед
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={createFormData.win_percentage}
                      onChange={(e) => setCreateFormData({...createFormData, win_percentage: parseFloat(e.target.value)})}
                      placeholder="40"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      % Поражений
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={createFormData.loss_percentage}
                      onChange={(e) => setCreateFormData({...createFormData, loss_percentage: parseFloat(e.target.value)})}
                      placeholder="40"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L12 12m6.364 6.364L12 12m0 0L5.636 5.636M12 12l6.364-6.364M12 12l-6.364 6.364" />
                      </svg>
                      % Ничьих
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={createFormData.draw_percentage}
                      onChange={(e) => setCreateFormData({...createFormData, draw_percentage: parseFloat(e.target.value)})}
                      placeholder="20"
                    />
                  </div>
                </div>
                <div className="form-help-block">
                  <svg className="help-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Сумма всех процентов должна равняться 100%
                </div>
              </div>

              {/* Настройки времени */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4>Настройки времени</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      Мин. задержка (сек)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="300"
                      value={createFormData.min_delay}
                      onChange={(e) => setCreateFormData({...createFormData, min_delay: parseInt(e.target.value)})}
                      placeholder="30"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Макс. задержка (сек)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="300"
                      value={createFormData.max_delay}
                      onChange={(e) => setCreateFormData({...createFormData, max_delay: parseInt(e.target.value)})}
                      placeholder="120"
                    />
                  </div>
                </div>
              </div>

              {/* Дополнительные настройки */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  </svg>
                  <h4>Дополнительные настройки</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Уровень логирования
                    </label>
                    <select
                      value={createFormData.logging_level}
                      onChange={(e) => setCreateFormData({...createFormData, logging_level: e.target.value})}
                    >
                      <option value="INFO">INFO</option>
                      <option value="DEBUG">DEBUG</option>
                    </select>
                  </div>
                </div>
                
                <div className="checkbox-group">
                  <div className="checkbox-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={createFormData.use_commit_reveal}
                        onChange={(e) => setCreateFormData({...createFormData, use_commit_reveal: e.target.checked})}
                      />
                      <svg className="checkbox-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      Использовать Commit-Reveal
                    </label>
                  </div>
                  <div className="checkbox-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={createFormData.can_play_with_other_bots || false}
                        onChange={(e) => setCreateFormData({...createFormData, can_play_with_other_bots: e.target.checked})}
                      />
                      <svg className="checkbox-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      Играть с другими Human-ботами
                    </label>
                    <small className="form-help">Разрешить боту автоматически играть с другими Human-ботами</small>
                  </div>
                  <div className="checkbox-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={createFormData.can_play_with_players || false}
                        onChange={(e) => setCreateFormData({...createFormData, can_play_with_players: e.target.checked})}
                      />
                      <svg className="checkbox-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                      </svg>
                      Играть с живыми игроками
                    </label>
                    <small className="form-help">Разрешить боту автоматически играть с живыми игроками</small>
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                <button type="submit" className="styled-btn btn-primary">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {editingBot ? 'Сохранить изменения' : 'Создать бота'}
                </button>
                <button 
                  type="button" 
                  className="styled-btn btn-secondary"
                  onClick={() => {
                    setShowCreateForm(false);
                    setEditingBot(null);
                  }}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Create Form */}
      {showBulkCreateForm && (
        <div className="modal-overlay">
          <div className="modal-content large-modal styled-modal">
            <div className="modal-header">
              <div className="modal-title">
                <svg className="modal-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <h3>Массовое создание Human-ботов</h3>
              </div>
              <button 
                type="button" 
                className="modal-close"
                onClick={() => setShowBulkCreateForm(false)}
              >
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <form onSubmit={(e) => { e.preventDefault(); handleBulkCreate(); }}>
              {/* Общие настройки */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h4>Общие настройки</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                      </svg>
                      Количество ботов
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={bulkCreateData.count}
                      onChange={(e) => setBulkCreateData({...bulkCreateData, count: parseInt(e.target.value)})}
                      placeholder="10"
                    />
                    <small className="form-help">Максимум 50 ботов за раз</small>
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      Характер для всех
                    </label>
                    <select
                      value={bulkCreateData.character}
                      onChange={(e) => setBulkCreateData({...bulkCreateData, character: e.target.value})}
                    >
                      {characters.map(char => (
                        <option key={char.value} value={char.value} title={char.description}>
                          {char.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Диапазоны ставок */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                  <h4>Диапазоны ставок</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      Диапазон мин. ставок (гемы)
                    </label>
                    <div className="range-inputs">
                      <input
                        type="number"
                        step="1"
                        placeholder="От"
                        value={bulkCreateData.min_bet_range[0]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          min_bet_range: [parseInt(e.target.value) || 1, bulkCreateData.min_bet_range[1]]
                        })}
                      />
                      <span className="range-separator">—</span>
                      <input
                        type="number"
                        step="1"
                        placeholder="До"
                        value={bulkCreateData.min_bet_range[1]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          min_bet_range: [bulkCreateData.min_bet_range[0], parseInt(e.target.value) || 1]
                        })}
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Диапазон макс. ставок (гемы)
                    </label>
                    <div className="range-inputs">
                      <input
                        type="number"
                        step="1"
                        placeholder="От"
                        value={bulkCreateData.max_bet_range[0]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          max_bet_range: [parseInt(e.target.value) || 1, bulkCreateData.max_bet_range[1]]
                        })}
                      />
                      <span className="range-separator">—</span>
                      <input
                        type="number"
                        step="1"
                        placeholder="До"
                        value={bulkCreateData.max_bet_range[1]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          max_bet_range: [bulkCreateData.max_bet_range[0], parseInt(e.target.value) || 1]
                        })}
                      />
                    </div>
                  </div>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      Диапазон лимитов ставок
                    </label>
                    <div className="range-inputs">
                      <input
                        type="number"
                        min="1"
                        max="100"
                        placeholder="От"
                        value={bulkCreateData.bet_limit_range[0]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          bet_limit_range: [parseInt(e.target.value), bulkCreateData.bet_limit_range[1]]
                        })}
                      />
                      <span className="range-separator">—</span>
                      <input
                        type="number"
                        min="1"
                        max="100"
                        placeholder="До"
                        value={bulkCreateData.bet_limit_range[1]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          bet_limit_range: [bulkCreateData.bet_limit_range[0], parseInt(e.target.value)]
                        })}
                      />
                    </div>
                    <small className="form-help">Диапазон максимального количества одновременных ставок (1-100)</small>
                  </div>
                </div>
              </div>

              {/* Настройки результатов */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h4>Настройки результатов для всех ботов</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      % Побед
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={bulkCreateData.win_percentage}
                      onChange={(e) => setBulkCreateData({...bulkCreateData, win_percentage: parseFloat(e.target.value)})}
                      placeholder="40"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      % Поражений
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={bulkCreateData.loss_percentage}
                      onChange={(e) => setBulkCreateData({...bulkCreateData, loss_percentage: parseFloat(e.target.value)})}
                      placeholder="40"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L12 12m6.364 6.364L12 12m0 0L5.636 5.636M12 12l6.364-6.364M12 12l-6.364 6.364" />
                      </svg>
                      % Ничьих
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={bulkCreateData.draw_percentage}
                      onChange={(e) => setBulkCreateData({...bulkCreateData, draw_percentage: parseFloat(e.target.value)})}
                      placeholder="20"
                    />
                  </div>
                </div>
                <div className="form-help-block">
                  <svg className="help-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Сумма всех процентов должна равняться 100%
                </div>
              </div>

              {/* Предпросмотр */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  <h4>Предпросмотр</h4>
                </div>
                
                <div className="bulk-preview">
                  <div className="preview-card">
                    <div className="preview-header">
                      <svg className="preview-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      <span>Будет создано {bulkCreateData.count} ботов</span>
                    </div>
                    <div className="preview-details">
                      <p><strong>Характер:</strong> {characters.find(c => c.value === bulkCreateData.character)?.label}</p>
                      <p><strong>Мин. ставки:</strong> {bulkCreateData.min_bet_range[0]} - {bulkCreateData.min_bet_range[1]} гемов</p>
                      <p><strong>Макс. ставки:</strong> {bulkCreateData.max_bet_range[0]} - {bulkCreateData.max_bet_range[1]} гемов</p>
                      <p><strong>Лимиты:</strong> {bulkCreateData.bet_limit_range[0]} - {bulkCreateData.bet_limit_range[1]} ставок</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                <button type="submit" className="styled-btn btn-primary">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  Создать {bulkCreateData.count} ботов
                </button>
                <button 
                  type="button" 
                  className="styled-btn btn-secondary"
                  onClick={() => setShowBulkCreateForm(false)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modals */}
      <ConfirmationModal {...confirmationModal} />
      <InputModal {...inputModal} />
    </div>
  );
};

export default HumanBotsManagement;