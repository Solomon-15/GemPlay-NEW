import React, { useState, useEffect } from 'react';
import { useBotsManagement } from '../hooks/useBotsManagement';
import { useConfirmation } from '../hooks/useConfirmation';
import { useInput } from '../hooks/useInput';
import InputModal from './InputModal';
import ConfirmationModal from './ConfirmationModal';

const HumanBotsManagement = () => {
  const { loading, error, executeOperation } = useBotsManagement();
  const { confirmationState, showConfirmation, handleConfirmation } = useConfirmation();
  const { inputModalState, showInputModal, handleInputModal } = useInput();
  const [humanBots, setHumanBots] = useState([]);
  const [stats, setStats] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    character: '',
    is_active: null
  });

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
    showConfirmation(
      `Вы уверены, что хотите удалить Human-бота "${botName}"?`,
      async () => {
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
    );
  };

  const handleToggleAll = async (activate) => {
    showConfirmation(
      `Вы уверены, что хотите ${activate ? 'активировать' : 'деактивировать'} всех Human-ботов?`,
      async () => {
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
    );
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
      <ConfirmationModal {...confirmationState} onClose={handleConfirmation} />
      <InputModal {...inputModalState} onClose={handleInputModal} />
    </div>
  );
};

export default HumanBotsManagement;tate, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import { useBotsManagement } from '../hooks/useBotsManagement';

const HumanBotsManagement = () => {
  const { botsApi } = useApi();
  const { bulkOperations } = useBotsManagement();
  const [stats, setStats] = useState({
    active_bots: 0,
    bets_24h: 0,
    wins_24h: 0,
    win_percentage: 0,
    total_bet_value: 0,
    errors: 0,
    most_active: []
  });
  const [allBotsEnabled, setAllBotsEnabled] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await botsApi.getStats();
      setStats(response || {});
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки статистики Human ботов:', error);
      setLoading(false);
    }
  };

  const toggleAllBots = async () => {
    try {
      const newState = !allBotsEnabled;
      
      await bulkOperations.toggleAllBots(newState);
      
      setAllBotsEnabled(newState);
      await fetchStats(); // Refresh stats
    } catch (error) {
      console.error('Ошибка переключения ботов:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Кнопка управления всеми ботами */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-rajdhani font-bold text-white">Human Боты</h2>
        <button
          onClick={toggleAllBots}
          className={`px-6 py-3 rounded-lg font-rajdhani font-bold text-white transition-colors ${
            allBotsEnabled 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-green-600 hover:bg-green-700'
          }`}
        >
          {allBotsEnabled ? 'Отключить всех ботов' : 'Включить всех ботов'}
        </button>
      </div>

      {/* Информационные блоки */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7 gap-4">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Активных ботов</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.active_bots}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Ставок за 24ч</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.bets_24h}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Побед за 24ч</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.wins_24h}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-purple-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">% побед</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.win_percentage}%</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-orange-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Сумма ставок</p>
              <p className="text-white text-lg font-rajdhani font-bold">${stats.total_bet_value.toFixed(2)}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${stats.errors > 0 ? 'bg-red-600' : 'bg-gray-600'}`}>
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Ошибки/Сбои</p>
              <p className={`text-lg font-rajdhani font-bold ${stats.errors > 0 ? 'text-red-400' : 'text-white'}`}>
                {stats.errors}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-indigo-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Топ активных</p>
              <div className="text-white text-sm">
                {stats.most_active.length > 0 ? (
                  stats.most_active.slice(0, 3).map((bot, index) => (
                    <div key={bot.id} className="text-xs">
                      {bot.name || `Bot-${bot.id.substring(0, 6)}`}: {bot.games}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-text-secondary">Нет данных</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Таблица ботов */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border-primary">
          <h3 className="text-lg font-rajdhani font-bold text-white">Список Human ботов</h3>
          <p className="text-text-secondary text-sm">Пока оставлено пустым, добавлю позже</p>
        </div>
        <div className="p-8 text-center">
          <div className="text-text-secondary">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="font-rajdhani">Таблица будет добавлена позже</p>
            <p className="text-sm">Раздел находится в разработке</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HumanBotsManagement;