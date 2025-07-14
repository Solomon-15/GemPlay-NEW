import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RegularBotsManagement = () => {
  const [stats, setStats] = useState({
    active_bots: 0,
    bets_24h: 0,
    wins_24h: 0,
    win_percentage: 0,
    total_bet_value: 0,
    errors: 0,
    most_active: []
  });
  const [botsList, setBotsList] = useState([]);
  const [botSettings, setBotSettings] = useState({
    max_active_bets_regular: 50,
    max_active_bets_human: 30
  });
  const [activeBetsStats, setActiveBetsStats] = useState({
    regular_bots: { current: 0, max: 50, available: 50, percentage: 0 },
    human_bots: { current: 0, max: 30, available: 30, percentage: 0 }
  });
  const [allBotsEnabled, setAllBotsEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [startingBots, setStartingBots] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isGlobalSettingsOpen, setIsGlobalSettingsOpen] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);

  // Form states for creating bot
  const [botForm, setBotForm] = useState({
    name: '',
    pause_timer: 5,
    recreate_interval: 30,
    cycle_games: 12,
    cycle_total_amount: 500,
    win_percentage: 60,
    min_bet_amount: 1,
    max_bet_amount: 100,
    can_accept_bets: false,
    can_play_with_bots: false
  });

  const { showSuccessRU, showErrorRU } = useNotifications();

  useEffect(() => {
    fetchStats();
    fetchBotsList();
    fetchBotSettings();
    fetchActiveBetsStats();
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/regular/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки статистики обычных ботов:', error);
      setLoading(false);
    }
  };

  const fetchBotsList = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/regular/list`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBotsList(response.data.bots || []);
    } catch (error) {
      console.error('Ошибка загрузки списка ботов:', error);
    }
  };

  const fetchBotSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBotSettings({
        max_active_bets_regular: response.data.max_active_bets_regular,
        max_active_bets_human: response.data.max_active_bets_human
      });
    } catch (error) {
      console.error('Ошибка загрузки настроек ботов:', error);
    }
  };

  const fetchActiveBetsStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/stats/active-bets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setActiveBetsStats(response.data);
    } catch (error) {
      console.error('Ошибка загрузки статистики активных ставок:', error);
    }
  };

  const startRegularBots = async () => {
    setStartingBots(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/bots/start-regular`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showSuccessRU(response.data.message);
      await fetchStats(); // Refresh stats
    } catch (error) {
      console.error('Ошибка запуска ботов:', error);
      showErrorRU('Ошибка при запуске ботов');
    } finally {
      setStartingBots(false);
    }
  };

  const toggleAllBots = async () => {
    try {
      const token = localStorage.getItem('token');
      const newState = !allBotsEnabled;
      
      await axios.post(`${API}/admin/bots/toggle-all`, 
        { enabled: newState },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setAllBotsEnabled(newState);
      await fetchStats(); // Refresh stats
    } catch (error) {
      console.error('Ошибка переключения ботов:', error);
    }
  };

  const createIndividualBot = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/bots/create-individual`, botForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showSuccessRU(response.data.message);
      setIsCreateModalOpen(false);
      setBotForm({
        name: '',
        pause_timer: 5,
        recreate_interval: 30,
        cycle_games: 12,
        cycle_total_amount: 500,
        win_percentage: 60,
        min_bet_amount: 1,
        max_bet_amount: 100,
        can_accept_bets: false,
        can_play_with_bots: false
      });
      await fetchStats();
      await fetchBotsList();
    } catch (error) {
      console.error('Ошибка создания бота:', error);
      showErrorRU('Ошибка при создании бота');
    }
  };

  const toggleBotStatus = async (botId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/bots/${botId}/toggle`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showSuccessRU(response.data.message);
      await fetchStats();
      await fetchBotsList();
    } catch (error) {
      console.error('Ошибка переключения статуса бота:', error);
      showErrorRU('Ошибка при изменении статуса бота');
    }
  };

  const handleSettingsModal = (bot) => {
    setSelectedBot(bot);
    setIsSettingsModalOpen(true);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  return (
    <div className="space-y-6">
      {/* Кнопки управления */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-rajdhani font-bold text-white">Обычные Боты</h2>
        <div className="flex space-x-3">
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-6 py-3 rounded-lg font-rajdhani font-bold text-white bg-green-600 hover:bg-green-700 transition-colors"
          >
            Создать Бота
          </button>
          <button
            onClick={startRegularBots}
            disabled={startingBots}
            className={`px-6 py-3 rounded-lg font-rajdhani font-bold text-white transition-colors ${
              startingBots 
                ? 'bg-gray-600 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {startingBots ? 'Запуск...' : 'Запустить ботов'}
          </button>
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
      </div>

      {/* Информационные блоки */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7 gap-4">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
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
                      Bot-{bot.id.substring(0, 6)}: {bot.games}
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
          <h3 className="text-lg font-rajdhani font-bold text-white">Список обычных ботов</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-sidebar">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Имя
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Статус
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Активные ставки
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Поб/Пр/Нч
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Win Rate
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Цикл
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Сумма за цикл
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Мин/Макс ставка
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Регистрация
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-primary">
              {botsList.length === 0 ? (
                <tr>
                  <td colSpan="10" className="px-4 py-8 text-center text-text-secondary">
                    Нет ботов для отображения
                  </td>
                </tr>
              ) : (
                botsList.map((bot) => (
                  <tr key={bot.id} className="hover:bg-surface-sidebar hover:bg-opacity-50">
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-white font-rajdhani font-bold">
                        {bot.name || `Bot #${bot.id.substring(0, 3)}`}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full font-rajdhani font-bold ${
                        bot.is_active 
                          ? 'bg-green-600 text-white' 
                          : 'bg-red-600 text-white'
                      }`}>
                        {bot.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-white font-roboto">
                        {bot.active_bets || 0}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-white font-roboto text-sm">
                        {bot.games_stats.wins}/{bot.games_stats.losses}/{bot.games_stats.draws}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-accent-primary font-rajdhani font-bold">
                        {bot.win_rate}%
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-white font-roboto">
                        {bot.cycle_games}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-accent-primary font-rajdhani font-bold">
                        ${bot.cycle_total_amount}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-white font-roboto text-sm">
                        ${bot.min_bet} / ${bot.max_bet}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="text-white font-roboto text-sm">
                        {formatDate(bot.created_at)}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleSettingsModal(bot)}
                          className="p-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                          title="Настройки"
                        >
                          ⚙
                        </button>
                        <button
                          onClick={() => toggleBotStatus(bot.id)}
                          className={`p-1 text-white rounded ${
                            bot.is_active 
                              ? 'bg-red-600 hover:bg-red-700' 
                              : 'bg-green-600 hover:bg-green-700'
                          }`}
                          title={bot.is_active ? "Отключить" : "Включить"}
                        >
                          {bot.is_active ? '🛑' : '✅'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Модальное окно создания бота */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-white">Создать обычного бота</h3>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              {/* Имя бота */}
              <div>
                <label className="block text-text-secondary text-sm mb-1">Имя бота:</label>
                <input
                  type="text"
                  value={botForm.name}
                  onChange={(e) => setBotForm({...botForm, name: e.target.value})}
                  placeholder="Bot #001"
                  className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                />
              </div>

              {/* Таймеры */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-text-secondary text-sm mb-1">Таймер паузы (мин):</label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={botForm.pause_timer}
                    onChange={(e) => setBotForm({...botForm, pause_timer: parseInt(e.target.value) || 5})}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-text-secondary text-sm mb-1">Интервал пересоздания (сек):</label>
                  <input
                    type="number"
                    min="1"
                    value={botForm.recreate_interval}
                    onChange={(e) => setBotForm({...botForm, recreate_interval: parseInt(e.target.value) || 30})}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                  />
                </div>
              </div>

              {/* Настройки цикла */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Настройки цикла</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Игр в цикле:</label>
                    <input
                      type="number"
                      min="1"
                      value={botForm.cycle_games}
                      onChange={(e) => setBotForm({...botForm, cycle_games: parseInt(e.target.value) || 12})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Сумма за цикл ($):</label>
                    <input
                      type="number"
                      min="1"
                      value={botForm.cycle_total_amount}
                      onChange={(e) => setBotForm({...botForm, cycle_total_amount: parseFloat(e.target.value) || 500})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">% выигрыша:</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={botForm.win_percentage}
                      onChange={(e) => setBotForm({...botForm, win_percentage: parseFloat(e.target.value) || 60})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                </div>
              </div>

              {/* Диапазон ставок */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Диапазон ставок</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Мин. ставка ($):</label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={botForm.min_bet_amount}
                      onChange={(e) => setBotForm({...botForm, min_bet_amount: parseFloat(e.target.value) || 1})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Макс. ставка ($):</label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={botForm.max_bet_amount}
                      onChange={(e) => setBotForm({...botForm, max_bet_amount: parseFloat(e.target.value) || 100})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                </div>
              </div>

              {/* Дополнительные настройки */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Поведение</h4>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={botForm.can_accept_bets}
                      onChange={(e) => setBotForm({...botForm, can_accept_bets: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="text-text-secondary text-sm">Может принимать чужие ставки</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={botForm.can_play_with_bots}
                      onChange={(e) => setBotForm({...botForm, can_play_with_bots: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="text-text-secondary text-sm">Может играть с другими ботами</span>
                  </label>
                </div>
              </div>

              {/* Кнопки */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={createIndividualBot}
                  className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary font-rajdhani font-bold"
                >
                  Создать бота
                </button>
                <button
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно настроек бота */}
      {isSettingsModalOpen && selectedBot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-white">Настройки бота: {selectedBot.name}</h3>
              <button
                onClick={() => setIsSettingsModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-text-secondary text-sm mb-1">Статус:</label>
                  <div className={`px-3 py-2 rounded-lg ${selectedBot.is_active ? 'bg-green-600' : 'bg-red-600'}`}>
                    <span className="text-white font-rajdhani font-bold">{selectedBot.status}</span>
                  </div>
                </div>
                <div>
                  <label className="block text-text-secondary text-sm mb-1">Win Rate:</label>
                  <div className="px-3 py-2 bg-surface-sidebar rounded-lg">
                    <span className="text-accent-primary font-rajdhani font-bold">{selectedBot.win_rate}%</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-text-secondary text-sm mb-1">Таймер паузы:</label>
                  <div className="px-3 py-2 bg-surface-sidebar rounded-lg">
                    <span className="text-white">{selectedBot.pause_timer} мин</span>
                  </div>
                </div>
                <div>
                  <label className="block text-text-secondary text-sm mb-1">Интервал пересоздания:</label>
                  <div className="px-3 py-2 bg-surface-sidebar rounded-lg">
                    <span className="text-white">{selectedBot.recreate_timer} сек</span>
                  </div>
                </div>
                <div>
                  <label className="block text-text-secondary text-sm mb-1">Игр в цикле:</label>
                  <div className="px-3 py-2 bg-surface-sidebar rounded-lg">
                    <span className="text-white">{selectedBot.cycle_games}</span>
                  </div>
                </div>
              </div>

              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Статистика игр</h4>
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-green-400 text-xl font-rajdhani font-bold">{selectedBot.games_stats.wins}</div>
                    <div className="text-text-secondary text-xs">Побед</div>
                  </div>
                  <div className="text-center">
                    <div className="text-red-400 text-xl font-rajdhani font-bold">{selectedBot.games_stats.losses}</div>
                    <div className="text-text-secondary text-xs">Поражений</div>
                  </div>
                  <div className="text-center">
                    <div className="text-yellow-400 text-xl font-rajdhani font-bold">{selectedBot.games_stats.draws}</div>
                    <div className="text-text-secondary text-xs">Ничьих</div>
                  </div>
                  <div className="text-center">
                    <div className="text-accent-primary text-xl font-rajdhani font-bold">{selectedBot.games_stats.total}</div>
                    <div className="text-text-secondary text-xs">Всего</div>
                  </div>
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => toggleBotStatus(selectedBot.id)}
                  className={`px-6 py-3 text-white rounded-lg font-rajdhani font-bold ${
                    selectedBot.is_active 
                      ? 'bg-red-600 hover:bg-red-700' 
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {selectedBot.is_active ? 'Отключить бота' : 'Включить бота'}
                </button>
                <button
                  onClick={() => setIsSettingsModalOpen(false)}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RegularBotsManagement;