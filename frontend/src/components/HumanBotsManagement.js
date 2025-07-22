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

  const handleCreateBot = async () => {
    if (createFormData.win_percentage + createFormData.loss_percentage + createFormData.draw_percentage !== 100) {
      alert('Сумма процентов должна равняться 100%');
      return;
    }

    try {
      const response = await executeOperation('/admin/human-bots', 'POST', createFormData);
      if (response.success !== false) {
        setShowCreateForm(false);
        setCreateFormData({
          name: '',
          character: 'BALANCED',
          min_bet: 1,
          max_bet: 100,
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
      console.error('Ошибка создания Human-бота:', error);
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
        <div className="header-actions">
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
      </div>

      {/* Statistics */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Общее количество</h3>
          <div className="stat-value">{stats.total_bots || 0}</div>
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

      {/* Human Bots Table */}
      {loading && <div className="loading">Загрузка...</div>}
      {error && <div className="error">Ошибка: {error}</div>}

      <div className="table-container">
        <table className="bots-table">
          <thead>
            <tr>
              <th>Имя</th>
              <th>Характер</th>
              <th>Статус</th>
              <th>Диапазон ставок</th>
              <th>Процент побед</th>
              <th>Статистика</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {humanBots.length > 0 ? humanBots.map(bot => (
              <tr key={bot.id}>
                <td>{bot.name}</td>
                <td>
                  <span className={`character-badge character-${bot.character.toLowerCase()}`}>
                    {getCharacterLabel(bot.character)}
                  </span>
                </td>
                <td>
                  <span 
                    className={`status-indicator status-${getStatusColor(bot.is_active)}`}
                  >
                    {bot.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </td>
                <td>{formatCurrency(bot.min_bet)} - {formatCurrency(bot.max_bet)}</td>
                <td>{formatPercentage(bot.win_rate)}</td>
                <td>
                  <div className="stats-cell">
                    <div>Игр: {bot.total_games_played}</div>
                    <div>Выиграл: {bot.total_games_won}</div>
                    <div>Заработал: {formatCurrency(bot.total_amount_won)}</div>
                  </div>
                </td>
                <td>
                  <div className="action-buttons">
                    <button
                      className={`btn-sm ${bot.is_active ? 'btn-warning' : 'btn-success'}`}
                      onClick={() => handleToggleStatus(bot.id)}
                    >
                      {bot.is_active ? '⏸️' : '▶️'}
                    </button>
                    <button
                      className="btn-sm btn-danger"
                      onClick={() => handleDeleteBot(bot.id, bot.name)}
                    >
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan="7" className="no-data">Нет Human-ботов</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button 
            disabled={currentPage === 1} 
            onClick={() => setCurrentPage(currentPage - 1)}
          >
            Предыдущая
          </button>
          <span>Страница {currentPage} из {totalPages}</span>
          <button 
            disabled={currentPage === totalPages} 
            onClick={() => setCurrentPage(currentPage + 1)}
          >
            Следующая
          </button>
        </div>
      )}

      {/* Create Bot Form */}
      {showCreateForm && (
        <div className="modal-overlay">
          <div className="modal-content large-modal">
            <h3>Создать Human-бота</h3>
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
                <button type="submit" className="btn-primary">Создать</button>
                <button 
                  type="button" 
                  className="btn-secondary"
                  onClick={() => setShowCreateForm(false)}
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