import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import Pagination from './Pagination';
import usePagination from '../hooks/usePagination';

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
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);
  const [editingBot, setEditingBot] = useState(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deletingBot, setDeletingBot] = useState(null);
  const [deleteReason, setDeleteReason] = useState('');
  const [isActiveBetsModalOpen, setIsActiveBetsModalOpen] = useState(false);
  const [activeBetsBot, setActiveBetsBot] = useState(null);
  const [activeBetsData, setActiveBetsData] = useState(null);
  const [isCycleModalOpen, setIsCycleModalOpen] = useState(false);
  const [cycleBot, setCycleBot] = useState(null);
  const [cycleData, setCycleData] = useState(null);
  const [resettingBotBets, setResettingBotBets] = useState(null);

  // Новые состояния для управления прибылью ботов
  const [isProfitAccumulatorsModalOpen, setIsProfitAccumulatorsModalOpen] = useState(false);
  const [profitAccumulators, setProfitAccumulators] = useState([]);
  const [profitPagination, setProfitPagination] = useState({ current_page: 1, total_pages: 1 });
  const [isForceCompleteModalOpen, setIsForceCompleteModalOpen] = useState(false);
  const [selectedBotForForceComplete, setSelectedBotForForceComplete] = useState(null);

  // Пагинация для списка ботов
  const pagination = usePagination(1, 10);

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

  // Перезагрузка списка ботов при изменении страницы
  useEffect(() => {
    fetchBotsList();
  }, [pagination.currentPage]);

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
      const { page, limit } = pagination.getPaginationParams();
      
      const response = await axios.get(`${API}/admin/bots/regular/list`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { page, limit }
      });
      
      setBotsList(response.data.bots || []);
      pagination.updatePagination(response.data.total_count || 0);
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
      
      if (response.data.limit_reached) {
        showErrorRU(`Лимит активных ставок достигнут: ${response.data.current_active_bets}/${response.data.max_active_bets}`);
      } else {
        showSuccessRU(response.data.message);
      }
      
      await fetchStats();
      await fetchActiveBetsStats();
    } catch (error) {
      console.error('Ошибка запуска ботов:', error);
      showErrorRU('Ошибка при запуске ботов');
    } finally {
      setStartingBots(false);
    }
  };

  const updateBotSettings = async (newSettings) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/bots/settings`, newSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setBotSettings(newSettings);
      setIsGlobalSettingsOpen(false);
      showSuccessRU(response.data.message);
      await fetchActiveBetsStats();
    } catch (error) {
      console.error('Ошибка обновления настроек:', error);
      showErrorRU('Ошибка при обновлении настроек');
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

  const handleEditModal = async (bot) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/${bot.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Set editing bot with all saved parameters
      setEditingBot({
        id: bot.id,
        name: response.data.bot.name || '',
        pause_timer: response.data.bot.pause_timer || 5,
        recreate_timer: response.data.bot.recreate_timer || 30,
        cycle_games: response.data.bot.cycle_games || 12,
        cycle_total_amount: response.data.bot.cycle_total_amount || 500,
        win_percentage: response.data.bot.win_percentage || 60,
        min_bet_amount: response.data.bot.min_bet_amount || 1,
        max_bet_amount: response.data.bot.max_bet_amount || 100,
        can_accept_bets: response.data.bot.can_accept_bets || false,
        can_play_with_bots: response.data.bot.can_play_with_bots || false
      });
      setIsEditModalOpen(true);
    } catch (error) {
      console.error('Ошибка загрузки данных бота:', error);
      showErrorRU('Ошибка при загрузке данных бота');
    }
  };

  const updateIndividualBotSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(`${API}/admin/bots/${editingBot.id}`, editingBot, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showSuccessRU(response.data.message);
      setIsEditModalOpen(false);
      setEditingBot(null);
      await fetchBotsList();
    } catch (error) {
      console.error('Ошибка обновления настроек бота:', error);
      showErrorRU('Ошибка при обновлении настроек бота');
    }
  };

  const recalculateBotBets = async (botId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/bots/${botId}/recalculate-bets`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showSuccessRU(`Пересчитано ${response.data.generated_bets} ставок для бота`);
      await fetchBotsList();
    } catch (error) {
      console.error('Ошибка пересчета ставок:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при пересчете ставок';
      showErrorRU(errorMessage);
    }
  };

  const resetBotBets = async (bot) => {
    try {
      setResettingBotBets(bot.id);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/bots/${bot.id}/reset-bets`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(`${response.data.message}. Обработано: ${response.data.total_processed} ставок`);
      await fetchBotsList(); // Refresh data
    } catch (error) {
      console.error('Error resetting bot bets:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при сбросе ставок бота';
      showErrorRU(errorMessage);
    } finally {
      setResettingBotBets(null);
    }
  };

  const handleDeleteModal = (bot) => {
    setDeletingBot(bot);
    setDeleteReason('');
    setIsDeleteModalOpen(true);
  };

  const deleteBot = async () => {
    if (!deleteReason.trim()) {
      showErrorRU('Укажите причину удаления бота');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.delete(`${API}/admin/bots/${deletingBot.id}/delete`, {
        headers: { Authorization: `Bearer ${token}` },
        data: { reason: deleteReason }
      });
      
      showSuccessRU(response.data.message);
      setIsDeleteModalOpen(false);
      setDeletingBot(null);
      setDeleteReason('');
      await fetchStats();
      await fetchBotsList();
    } catch (error) {
      console.error('Ошибка удаления бота:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при удалении бота';
      showErrorRU(errorMessage);
    }
  };

  const handleActiveBetsModal = async (bot) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/${bot.id}/active-bets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setActiveBetsBot(bot);
      setActiveBetsData(response.data);
      setIsActiveBetsModalOpen(true);
    } catch (error) {
      console.error('Ошибка загрузки активных ставок:', error);
      showErrorRU('Ошибка при загрузке активных ставок');
    }
  };

  const handleCycleModal = async (bot) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/${bot.id}/cycle-history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCycleBot(bot);
      setCycleData(response.data);
      setIsCycleModalOpen(true);
    } catch (error) {
      console.error('Ошибка загрузки истории цикла:', error);
      showErrorRU('Ошибка при загрузке истории цикла');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  // Функции для управления прибылью ботов
  const handleOpenProfitAccumulators = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/profit-accumulators?page=1&limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setProfitAccumulators(response.data.accumulators || []);
      setProfitPagination(response.data.pagination || { current_page: 1, total_pages: 1 });
      setIsProfitAccumulatorsModalOpen(true);
      showSuccessRU('Данные накопителей прибыли загружены');
    } catch (error) {
      console.error('Error fetching profit accumulators:', error);
      showErrorRU('Ошибка при загрузке накопителей прибыли');
    }
  };

  const handleForceCompleteModal = (bot) => {
    setSelectedBotForForceComplete(bot);
    setIsForceCompleteModalOpen(true);
  };

  const handleForceCompleteCycle = async () => {
    if (!selectedBotForForceComplete) return;

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/bots/${selectedBotForForceComplete.id}/force-complete-cycle`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showSuccessRU(`Цикл бота завершён принудительно. Прибыль: $${response.data.profit.toFixed(2)}`);
      setIsForceCompleteModalOpen(false);
      setSelectedBotForForceComplete(null);
      
      // Обновляем данные
      await fetchStats();
      await fetchBotsList();
      await fetchActiveBetsStats();
    } catch (error) {
      console.error('Error force completing cycle:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при принудительном завершении цикла';
      showErrorRU(errorMessage);
    }
  };

  return (
    <div className="space-y-6">
      {/* Кнопки управления */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-rajdhani font-bold text-white">Обычные Боты</h2>
        <div className="flex space-x-3">
          <button
            onClick={() => setIsGlobalSettingsOpen(true)}
            className="px-6 py-3 rounded-lg font-rajdhani font-bold text-white bg-purple-600 hover:bg-purple-700 transition-colors"
          >
            Общие настройки
          </button>
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

      {/* Статистика активных ставок */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
        <h3 className="text-lg font-rajdhani font-bold text-white mb-3">Активные ставки обычных ботов</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-surface-sidebar rounded-lg p-3">
            <div className="text-text-secondary text-sm">Текущие активные ставки</div>
            <div className="text-white text-xl font-rajdhani font-bold">
              {activeBetsStats.regular_bots.current}
            </div>
          </div>
          <div className="bg-surface-sidebar rounded-lg p-3">
            <div className="text-text-secondary text-sm">Максимальный лимит</div>
            <div className="text-accent-primary text-xl font-rajdhani font-bold">
              {activeBetsStats.regular_bots.max}
            </div>
          </div>
          <div className="bg-surface-sidebar rounded-lg p-3">
            <div className="text-text-secondary text-sm">Доступные слоты</div>
            <div className="text-green-400 text-xl font-rajdhani font-bold">
              {activeBetsStats.regular_bots.available}
            </div>
          </div>
          <div className="bg-surface-sidebar rounded-lg p-3">
            <div className="text-text-secondary text-sm">Заполненность</div>
            <div className={`text-xl font-rajdhani font-bold ${
              activeBetsStats.regular_bots.percentage >= 90 ? 'text-red-400' :
              activeBetsStats.regular_bots.percentage >= 70 ? 'text-yellow-400' : 'text-green-400'
            }`}>
              {activeBetsStats.regular_bots.percentage}%
            </div>
          </div>
        </div>
        
        {/* Прогресс-бар */}
        <div className="mt-4">
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                activeBetsStats.regular_bots.percentage >= 90 ? 'bg-red-500' :
                activeBetsStats.regular_bots.percentage >= 70 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(100, activeBetsStats.regular_bots.percentage)}%` }}
            ></div>
          </div>
          <div className="text-text-secondary text-xs mt-1">
            {activeBetsStats.regular_bots.current} из {activeBetsStats.regular_bots.max} активных ставок
          </div>
        </div>
      </div>

      {/* Информационные блоки */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7 gap-4">
        {/* Активные и отключенные боты */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-600 rounded-lg">
              <span className="text-white text-lg">🟢</span>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Активных ботов</p>
              <p className="text-white text-lg font-rajdhani font-bold">
                {botsList.filter(bot => bot.is_active).length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-red-600 rounded-lg">
              <span className="text-white text-lg">🔴</span>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Отключённых ботов</p>
              <p className="text-white text-lg font-rajdhani font-bold">
                {botsList.filter(bot => !bot.is_active).length}
              </p>
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
                  % Выигрыша
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
                  <td colSpan="11" className="px-4 py-8 text-center text-text-secondary">
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
                      <button
                        onClick={() => handleActiveBetsModal(bot)}
                        className="text-blue-400 hover:text-blue-300 underline font-roboto cursor-pointer"
                        title="Показать активные ставки"
                      >
                        {bot.active_bets || 0}
                      </button>
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
                      <div className="text-orange-400 font-rajdhani font-bold">
                        {bot.win_percentage || 60}%
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleCycleModal(bot)}
                        className="text-green-400 hover:text-green-300 underline font-roboto cursor-pointer"
                        title="Показать историю цикла"
                      >
                        {(bot.games_stats.wins + bot.games_stats.losses)}/{bot.cycle_games || 12}
                      </button>
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
                          onClick={() => handleEditModal(bot)}
                          className="p-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                          title="Настройки"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => resetBotBets(bot)}
                          disabled={resettingBotBets === bot.id}
                          className="p-1 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
                          title="Сбросить ставки бота"
                        >
                          {resettingBotBets === bot.id ? (
                            <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                          ) : (
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          )}
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
                          {bot.is_active ? (
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                            </svg>
                          ) : (
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          )}
                        </button>
                        <button
                          onClick={() => handleDeleteModal(bot)}
                          className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                          title="🗑 Удалить"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                        <button
                          onClick={() => recalculateBotBets(bot.id)}
                          className="p-1 bg-purple-600 text-white rounded hover:bg-purple-700"
                          title="🔄 Пересчитать ставки"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
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

      {/* Пагинация для списка ботов */}
      <Pagination
        currentPage={pagination.currentPage}
        totalPages={pagination.totalPages}
        onPageChange={pagination.handlePageChange}
        itemsPerPage={pagination.itemsPerPage}
        totalItems={pagination.totalItems}
        className="mt-6"
      />

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

      {/* Модальное окно редактирования бота */}
      {isEditModalOpen && editingBot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-white">Редактировать бота: {editingBot.name}</h3>
              <button
                onClick={() => setIsEditModalOpen(false)}
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
                  value={editingBot.name}
                  onChange={(e) => setEditingBot({...editingBot, name: e.target.value})}
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
                    value={editingBot.pause_timer}
                    onChange={(e) => setEditingBot({...editingBot, pause_timer: parseInt(e.target.value) || 5})}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-text-secondary text-sm mb-1">Интервал пересоздания (сек):</label>
                  <input
                    type="number"
                    min="1"
                    value={editingBot.recreate_timer}
                    onChange={(e) => setEditingBot({...editingBot, recreate_timer: parseInt(e.target.value) || 30})}
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
                      value={editingBot.cycle_games}
                      onChange={(e) => setEditingBot({...editingBot, cycle_games: parseInt(e.target.value) || 12})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Сумма за цикл ($):</label>
                    <input
                      type="number"
                      min="1"
                      value={editingBot.cycle_total_amount}
                      onChange={(e) => setEditingBot({...editingBot, cycle_total_amount: parseFloat(e.target.value) || 500})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">% выигрыша:</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={editingBot.win_percentage}
                      onChange={(e) => setEditingBot({...editingBot, win_percentage: parseFloat(e.target.value) || 60})}
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
                      value={editingBot.min_bet_amount}
                      onChange={(e) => setEditingBot({...editingBot, min_bet_amount: parseFloat(e.target.value) || 1})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Макс. ставка ($):</label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={editingBot.max_bet_amount}
                      onChange={(e) => setEditingBot({...editingBot, max_bet_amount: parseFloat(e.target.value) || 100})}
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
                      checked={editingBot.can_accept_bets}
                      onChange={(e) => setEditingBot({...editingBot, can_accept_bets: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="text-text-secondary text-sm">Может принимать чужие ставки</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={editingBot.can_play_with_bots}
                      onChange={(e) => setEditingBot({...editingBot, can_play_with_bots: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="text-text-secondary text-sm">Может играть с другими ботами</span>
                  </label>
                </div>
              </div>

              {/* Кнопки */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={updateIndividualBotSettings}
                  className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary font-rajdhani font-bold"
                >
                  Сохранить изменения
                </button>
                <button
                  onClick={() => recalculateBotBets(editingBot.id)}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-rajdhani font-bold"
                >
                  🔄 Пересчитать ставки
                </button>
                <button
                  onClick={() => setIsEditModalOpen(false)}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно общих настроек */}
      {isGlobalSettingsOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-lg w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-white">Общие настройки ботов</h3>
              <button
                onClick={() => setIsGlobalSettingsOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Лимиты активных ставок</h4>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">
                      Максимальное количество активных ставок обычных ботов:
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="1000"
                      value={botSettings.max_active_bets_regular}
                      onChange={(e) => setBotSettings({
                        ...botSettings, 
                        max_active_bets_regular: parseInt(e.target.value) || 0
                      })}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                    <div className="text-text-secondary text-xs mt-1">
                      Текущее значение: {activeBetsStats.regular_bots.current} из {activeBetsStats.regular_bots.max}
                    </div>
                  </div>

                  <div>
                    <label className="block text-text-secondary text-sm mb-1">
                      Максимальное количество активных ставок Human ботов:
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="1000"
                      value={botSettings.max_active_bets_human}
                      onChange={(e) => setBotSettings({
                        ...botSettings, 
                        max_active_bets_human: parseInt(e.target.value) || 0
                      })}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                    <div className="text-text-secondary text-xs mt-1">
                      Текущее значение: {activeBetsStats.human_bots.current} из {activeBetsStats.human_bots.max}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-yellow-900 border border-yellow-600 rounded-lg p-3">
                <div className="text-yellow-200 text-sm">
                  <strong>Важно:</strong> Если лимит достигнут, новые ставки ботами не создаются до тех пор, 
                  пока одна из активных ставок не будет принята, отменена или завершена.
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => updateBotSettings(botSettings)}
                  className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary font-rajdhani font-bold"
                >
                  Сохранить настройки
                </button>
                <button
                  onClick={() => setIsGlobalSettingsOpen(false)}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно активных ставок */}
      {isActiveBetsModalOpen && activeBetsBot && activeBetsData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-blue-500 border-opacity-50 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-blue-400">
                📊 Активные ставки: {activeBetsData.bot_name}
              </h3>
              <button
                onClick={() => setIsActiveBetsModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              {/* Статистика */}
              <div className="bg-surface-sidebar rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-2">Сводка:</h4>
                <div className="text-text-secondary">
                  Всего активных ставок: <span className="text-white font-bold">{activeBetsData.active_bets_count}</span>
                </div>
              </div>

              {/* Список ставок */}
              {activeBetsData.bets.length === 0 ? (
                <div className="text-center py-8 text-text-secondary">
                  Нет активных ставок
                </div>
              ) : (
                <div className="space-y-3">
                  {activeBetsData.bets.map((bet, index) => (
                    <div key={bet.game_id} className="bg-surface-sidebar rounded-lg p-4 border border-border-primary">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                          <div className="text-text-secondary text-sm">Сумма ставки:</div>
                          <div className="text-accent-primary font-rajdhani font-bold text-lg">
                            ${bet.bet_amount}
                          </div>
                          <div className="text-text-secondary text-xs">
                            {Object.entries(bet.bet_gems).map(([gem, qty]) => `${gem}: ${qty}`).join(', ')}
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-text-secondary text-sm">Противник:</div>
                          <div className="text-white">
                            {bet.opponent ? bet.opponent.username : 'Ожидает'}
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-text-secondary text-sm">Статус:</div>
                          <span className={`px-2 py-1 text-xs rounded-full font-rajdhani font-bold ${
                            bet.status === 'Ожидает' 
                              ? 'bg-yellow-600 text-white' 
                              : 'bg-blue-600 text-white'
                          }`}>
                            {bet.status}
                          </span>
                        </div>
                        
                        <div>
                          <div className="text-text-secondary text-sm">Создана:</div>
                          <div className="text-white text-sm">
                            {new Date(bet.created_at).toLocaleString('ru-RU')}
                          </div>
                          {bet.time_until_cancel && (
                            <div className="text-yellow-400 text-xs">
                              ⏰ {bet.time_until_cancel}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Кнопки */}
              <div className="flex justify-end pt-4">
                <button
                  onClick={() => setIsActiveBetsModalOpen(false)}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно истории цикла */}
      {isCycleModalOpen && cycleBot && cycleData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-green-500 border-opacity-50 rounded-lg p-6 max-w-6xl w-full mx-4 max-h-[85vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-green-400">
                📈 История цикла: {cycleData.bot_name}
              </h3>
              <button
                onClick={() => setIsCycleModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-6">
              {/* Статистика цикла */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-surface-sidebar rounded-lg p-4">
                  <h4 className="font-rajdhani font-bold text-white mb-2">Прогресс цикла:</h4>
                  <div className="text-2xl font-rajdhani font-bold text-green-400">
                    {cycleData.cycle_info.progress}
                  </div>
                  <div className="text-text-secondary text-sm">
                    Завершено игр (без ничьих)
                  </div>
                  <div className="mt-2 text-sm">
                    <div className="text-green-400">Побед: {cycleData.cycle_info.current_wins}</div>
                    <div className="text-red-400">Поражений: {cycleData.cycle_info.current_losses}</div>
                    <div className="text-yellow-400">Ничьих: {cycleData.cycle_info.draws}</div>
                  </div>
                </div>

                <div className="bg-surface-sidebar rounded-lg p-4">
                  <h4 className="font-rajdhani font-bold text-white mb-2">Финансы:</h4>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-text-secondary">Поставлено:</span>
                      <span className="text-white ml-2">${cycleData.cycle_stats.total_bet_amount}</span>
                    </div>
                    <div>
                      <span className="text-text-secondary">Выиграно:</span>
                      <span className="text-green-400 ml-2">${cycleData.cycle_stats.total_winnings}</span>
                    </div>
                    <div>
                      <span className="text-text-secondary">Проиграно:</span>
                      <span className="text-red-400 ml-2">${cycleData.cycle_stats.total_losses}</span>
                    </div>
                    <div className="border-t border-border-primary pt-2">
                      <span className="text-text-secondary">Итого:</span>
                      <span className={`ml-2 font-bold ${
                        cycleData.cycle_stats.net_profit >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        ${cycleData.cycle_stats.net_profit}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-surface-sidebar rounded-lg p-4">
                  <h4 className="font-rajdhani font-bold text-white mb-2">Эффективность:</h4>
                  <div className="text-2xl font-rajdhani font-bold text-accent-primary">
                    {cycleData.cycle_stats.win_percentage}%
                  </div>
                  <div className="text-text-secondary text-sm">
                    Процент побед
                  </div>
                </div>
              </div>

              {/* Таблица игр */}
              <div className="bg-surface-sidebar rounded-lg overflow-hidden">
                <div className="p-4 border-b border-border-primary">
                  <h4 className="font-rajdhani font-bold text-white">Лог матчей текущего цикла</h4>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-surface-card">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">№</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Ставка</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Гемы</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Противник</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Результат</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Выигрыш</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Дата</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-primary">
                      {cycleData.games.map((game, index) => (
                        <tr key={game.game_id} className="hover:bg-surface-card hover:bg-opacity-50">
                          <td className="px-4 py-3 text-white">{game.game_number}</td>
                          <td className="px-4 py-3 text-accent-primary font-bold">${game.bet_amount}</td>
                          <td className="px-4 py-3 text-text-secondary text-xs">
                            {Object.entries(game.bet_gems).map(([gem, qty]) => `${gem}: ${qty}`).join(', ')}
                          </td>
                          <td className="px-4 py-3 text-white">{game.opponent}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs rounded-full font-rajdhani font-bold ${
                              game.result === 'Победа' ? 'bg-green-600 text-white' :
                              game.result === 'Поражение' ? 'bg-red-600 text-white' :
                              'bg-yellow-600 text-white'
                            }`}>
                              {game.result}
                            </span>
                          </td>
                          <td className={`px-4 py-3 font-bold ${
                            game.winnings > 0 ? 'text-green-400' :
                            game.winnings < 0 ? 'text-red-400' :
                            'text-gray-400'
                          }`}>
                            {game.winnings > 0 ? '+' : ''}${game.winnings}
                          </td>
                          <td className="px-4 py-3 text-text-secondary text-sm">
                            {new Date(game.completed_at).toLocaleString('ru-RU')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Кнопки */}
              <div className="flex justify-end pt-4">
                <button
                  onClick={() => setIsCycleModalOpen(false)}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно удаления бота */}
      {isDeleteModalOpen && deletingBot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-red-500 border-opacity-50 rounded-lg p-6 max-w-lg w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-red-400">🗑 Удалить бота</h3>
              <button
                onClick={() => setIsDeleteModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              {/* Предупреждение */}
              <div className="bg-red-900 border border-red-600 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-6 h-6 text-red-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <div>
                    <h4 className="text-red-300 font-rajdhani font-bold">Внимание!</h4>
                    <p className="text-red-200 text-sm">
                      Вы собираетесь удалить бота <strong>"{deletingBot.name || `Bot #${deletingBot.id.substring(0, 6)}`}"</strong>
                    </p>
                  </div>
                </div>
              </div>

              {/* Информация о боте */}
              <div className="bg-surface-sidebar rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-2">Информация о боте:</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-text-secondary">Статус:</span>
                    <span className={`ml-2 ${deletingBot.is_active ? 'text-green-400' : 'text-red-400'}`}>
                      {deletingBot.is_active ? 'Активен' : 'Отключен'}
                    </span>
                  </div>
                  <div>
                    <span className="text-text-secondary">Активные ставки:</span>
                    <span className="text-white ml-2">{deletingBot.active_bets || 0}</span>
                  </div>
                  <div>
                    <span className="text-text-secondary">Win Rate:</span>
                    <span className="text-accent-primary ml-2">{deletingBot.win_rate}%</span>
                  </div>
                  <div>
                    <span className="text-text-secondary">Регистрация:</span>
                    <span className="text-white ml-2">{formatDate(deletingBot.created_at)}</span>
                  </div>
                </div>
              </div>

              {/* Поле для причины удаления */}
              <div>
                <label className="block text-text-secondary text-sm mb-2">
                  <span className="text-red-400">*</span> Причина удаления:
                </label>
                <textarea
                  key={`delete-reason-${deletingBot.id}`}
                  value={deleteReason}
                  onChange={(e) => setDeleteReason(e.target.value)}
                  placeholder="Укажите причину удаления бота (например: неисправность, нарушение правил, плановая замена...)"
                  rows={3}
                  className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white resize-none"
                  required
                />
                <div className="text-text-secondary text-xs mt-1">
                  Причина будет записана в логи администратора
                </div>
              </div>

              {/* Предупреждение об активных играх */}
              {deletingBot.active_bets > 0 && (
                <div className="bg-yellow-900 border border-yellow-600 rounded-lg p-3">
                  <div className="text-yellow-200 text-sm">
                    <strong>Важно:</strong> У бота есть {deletingBot.active_bets} активные ставки. 
                    Они будут отменены при удалении.
                  </div>
                </div>
              )}

              {/* Кнопки */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={deleteBot}
                  disabled={!deleteReason.trim()}
                  className={`px-6 py-3 text-white rounded-lg font-rajdhani font-bold transition-colors ${
                    deleteReason.trim()
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-gray-600 cursor-not-allowed'
                  }`}
                >
                  🗑 Удалить бота
                </button>
                <button
                  onClick={() => {
                    setIsDeleteModalOpen(false);
                    setDeletingBot(null);
                    setDeleteReason('');
                  }}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Отмена
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