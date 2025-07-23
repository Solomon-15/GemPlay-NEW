import React, { useState, useEffect } from 'react';
import axios from 'axios';
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
    logging_level: 'INFO'
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
        max_active_bets_human: humanBotSettings.max_active_bets_human
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
                  className="btn-primary"
                  onClick={() => setShowCreateForm(true)}
                >
                  + Создать бота
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => setShowBulkCreateForm(true)}
                >
                  📦 Массовое создание
                </button>
                <button
                  className="btn-success"
                  onClick={() => handleToggleAll(true)}
                >
                  ✅ Активировать всех
                </button>
                <button
                  className="btn-warning"
                  onClick={() => handleToggleAll(false)}
                >
                  ⏸️ Деактивировать всех
                </button>
              </div>

              {/* Statistics */}
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Количество ботов</h3>
                  <div className="stat-value">{stats.total_bots || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Количество ставок</h3>
                  <div className="stat-value">{stats.total_bets || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Активные</h3>
                  <div className="stat-value">{stats.active_bots || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Игр за 24ч</h3>
                  <div className="stat-value">{stats.total_games_24h || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Доход за 24ч</h3>
                  <div className="stat-value">{formatCurrency(stats.total_revenue_24h || 0)}</div>
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
                            className="flex-1 max-w-xs px-4 py-2 bg-surface-primary border border-border-primary rounded-lg text-white font-roboto"
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
          <div className="modal-content large-modal">
            <h3>{editingBot ? 'Редактировать Human-бота' : 'Создать Human-бота'}</h3>
            <form onSubmit={(e) => { e.preventDefault(); handleCreateBot(); }}>
              <div className="form-row">
                <div className="form-group">
                  <label>Имя бота *</label>
                  <input
                    type="text"
                    value={createFormData.name}
                    onChange={(e) => setCreateFormData({...createFormData, name: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Характер *</label>
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

              <div className="form-row">
                <div className="form-group">
                  <label>Мин. ставка ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    value={createFormData.min_bet}
                    onChange={(e) => setCreateFormData({...createFormData, min_bet: parseFloat(e.target.value)})}
                  />
                </div>
                <div className="form-group">
                  <label>Макс. ставка ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    value={createFormData.max_bet}
                    onChange={(e) => setCreateFormData({...createFormData, max_bet: parseFloat(e.target.value)})}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Лимит ставок</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={createFormData.bet_limit}
                    onChange={(e) => setCreateFormData({...createFormData, bet_limit: parseInt(e.target.value)})}
                  />
                  <small className="form-help">Максимальное количество одновременных ставок (1-100)</small>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>% Побед</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={createFormData.win_percentage}
                    onChange={(e) => setCreateFormData({...createFormData, win_percentage: parseFloat(e.target.value)})}
                  />
                </div>
                <div className="form-group">
                  <label>% Поражений</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={createFormData.loss_percentage}
                    onChange={(e) => setCreateFormData({...createFormData, loss_percentage: parseFloat(e.target.value)})}
                  />
                </div>
                <div className="form-group">
                  <label>% Ничьих</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={createFormData.draw_percentage}
                    onChange={(e) => setCreateFormData({...createFormData, draw_percentage: parseFloat(e.target.value)})}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Мин. задержка (сек)</label>
                  <input
                    type="number"
                    min="1"
                    max="300"
                    value={createFormData.min_delay}
                    onChange={(e) => setCreateFormData({...createFormData, min_delay: parseInt(e.target.value)})}
                  />
                </div>
                <div className="form-group">
                  <label>Макс. задержка (сек)</label>
                  <input
                    type="number"
                    min="1"
                    max="300"
                    value={createFormData.max_delay}
                    onChange={(e) => setCreateFormData({...createFormData, max_delay: parseInt(e.target.value)})}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={createFormData.use_commit_reveal}
                      onChange={(e) => setCreateFormData({...createFormData, use_commit_reveal: e.target.checked})}
                    />
                    Использовать Commit-Reveal
                  </label>
                </div>
                <div className="form-group">
                  <label>Уровень логирования</label>
                  <select
                    value={createFormData.logging_level}
                    onChange={(e) => setCreateFormData({...createFormData, logging_level: e.target.value})}
                  >
                    <option value="INFO">INFO</option>
                    <option value="DEBUG">DEBUG</option>
                  </select>
                </div>
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary">{editingBot ? 'Сохранить' : 'Создать'}</button>
                <button 
                  type="button" 
                  className="btn-secondary"
                  onClick={() => {
                    setShowCreateForm(false);
                    setEditingBot(null);
                  }}
                >
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
          <div className="modal-content large-modal">
            <h3>Массовое создание Human-ботов</h3>
            <form onSubmit={(e) => { e.preventDefault(); handleBulkCreate(); }}>
              <div className="form-row">
                <div className="form-group">
                  <label>Количество ботов</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={bulkCreateData.count}
                    onChange={(e) => setBulkCreateData({...bulkCreateData, count: parseInt(e.target.value)})}
                  />
                </div>
                <div className="form-group">
                  <label>Характер для всех</label>
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

              <div className="form-row">
                <div className="form-group">
                  <label>Диапазон мин. ставок ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="От"
                    value={bulkCreateData.min_bet_range[0]}
                    onChange={(e) => setBulkCreateData({
                      ...bulkCreateData, 
                      min_bet_range: [parseFloat(e.target.value), bulkCreateData.min_bet_range[1]]
                    })}
                  />
                  <input
                    type="number"
                    step="0.01"
                    placeholder="До"
                    value={bulkCreateData.min_bet_range[1]}
                    onChange={(e) => setBulkCreateData({
                      ...bulkCreateData, 
                      min_bet_range: [bulkCreateData.min_bet_range[0], parseFloat(e.target.value)]
                    })}
                  />
                </div>
                <div className="form-group">
                  <label>Диапазон макс. ставок ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="От"
                    value={bulkCreateData.max_bet_range[0]}
                    onChange={(e) => setBulkCreateData({
                      ...bulkCreateData, 
                      max_bet_range: [parseFloat(e.target.value), bulkCreateData.max_bet_range[1]]
                    })}
                  />
                  <input
                    type="number"
                    step="0.01"
                    placeholder="До"
                    value={bulkCreateData.max_bet_range[1]}
                    onChange={(e) => setBulkCreateData({
                      ...bulkCreateData, 
                      max_bet_range: [bulkCreateData.max_bet_range[0], parseFloat(e.target.value)]
                    })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Диапазон лимитов ставок</label>
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
                  <small className="form-help">Диапазон максимального количества одновременных ставок (1-100)</small>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>% Побед</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={bulkCreateData.win_percentage}
                    onChange={(e) => setBulkCreateData({...bulkCreateData, win_percentage: parseFloat(e.target.value)})}
                  />
                </div>
                <div className="form-group">
                  <label>% Поражений</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={bulkCreateData.loss_percentage}
                    onChange={(e) => setBulkCreateData({...bulkCreateData, loss_percentage: parseFloat(e.target.value)})}
                  />
                </div>
                <div className="form-group">
                  <label>% Ничьих</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={bulkCreateData.draw_percentage}
                    onChange={(e) => setBulkCreateData({...bulkCreateData, draw_percentage: parseFloat(e.target.value)})}
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary">Создать {bulkCreateData.count} ботов</button>
                <button 
                  type="button" 
                  className="btn-secondary"
                  onClick={() => setShowBulkCreateForm(false)}
                >
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