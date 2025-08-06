import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import { formatAsGems } from '../utils/economy';
import Pagination from './Pagination';
import usePagination from '../hooks/usePagination';
import useConfirmation from '../hooks/useConfirmation';
import useInput from '../hooks/useInput';
import ConfirmationModal from './ConfirmationModal';
import InputModal from './InputModal';
import API, { getApiConfig } from '../utils/api';

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
    max_active_bets_regular: 5000000000,
    max_active_bets_human: 300000000
  });
  const [activeBetsStats, setActiveBetsStats] = useState({
    regular_bots: { current: 0, max: 50, available: 50, percentage: 0 },
    human_bots: { current: 0, max: 30, available: 30, percentage: 0 }
  });
  const [allBotsEnabled, setAllBotsEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);
  const [editingBot, setEditingBot] = useState(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deletingBot, setDeletingBot] = useState(null);
  const [deleteReason, setDeleteReason] = useState('');
  const [isActiveBetsModalOpen, setIsActiveBetsModalOpen] = useState(false);
  const [selectedBotForActiveBets, setSelectedBotForActiveBets] = useState(null);
  const [activeBetsData, setActiveBetsData] = useState(null);
  const [loadingActiveBets, setLoadingActiveBets] = useState(false);
  const [loadingStates, setLoadingStates] = useState({});
  const [isCycleModalOpen, setIsCycleModalOpen] = useState(false);
  const [cycleBot, setCycleBot] = useState(null);
  const [cycleData, setCycleData] = useState(null);
  
  const [editingBotLimits, setEditingBotLimits] = useState({}); // {botId: {limit: value, saving: false}}
  const [botLimitsValidation, setBotLimitsValidation] = useState({});

  const [isProfitAccumulatorsModalOpen, setIsProfitAccumulatorsModalOpen] = useState(false);
  const [profitAccumulators, setProfitAccumulators] = useState([]);
  const [profitPagination, setProfitPagination] = useState({ current_page: 1, total_pages: 1 });
  const [isForceCompleteModalOpen, setIsForceCompleteModalOpen] = useState(false);
  const [selectedBotForForceComplete, setSelectedBotForForceComplete] = useState(null);

  const [isBotProfitModalOpen, setIsBotProfitModalOpen] = useState(false);
  const [selectedBotForProfit, setSelectedBotForProfit] = useState(null);
  const [botProfitAccumulators, setBotProfitAccumulators] = useState([]);
  const [botProfitPagination, setBotProfitPagination] = useState({ current_page: 1, total_pages: 1 });

  const pagination = usePagination(1, 10);

  const [selectedBots, setSelectedBots] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);

  // Form states for creating bot with new extended system
  const [botForm, setBotForm] = useState({
    name: '',
    
    min_bet_amount: 1.0, // 1-10000
    max_bet_amount: 50.0, // 1-10000
    win_percentage: 55.0, // 0-100% (по умолчанию 55%)
    
    cycle_games: 12, // 1-66 (по умолчанию 12)
    pause_between_cycles: 5, // 1-300 секунд (пауза между циклами, по умолчанию 5)
    pause_on_draw: 1, // 1-60 секунд (пауза при ничье, по умолчанию 1)
    
    creation_mode: 'queue-based', // 'always-first', 'queue-based', 'after-all' (по умолчанию queue-based)
    profit_strategy: 'balanced', // 'start-positive', 'balanced', 'start-negative'
    
    cycle_total_amount: 0 // calculated automatically
  });

  // Calculate cycle total amount automatically
  const calculateCycleTotalAmount = () => {
    if (!botForm.min_bet_amount || !botForm.max_bet_amount || !botForm.cycle_games) {
      return 0;
    }
    
    const averageValue = (botForm.min_bet_amount + botForm.max_bet_amount) / 2;
    const totalAmount = Math.round(averageValue * botForm.cycle_games);
    
    return totalAmount;
  };

  // Update cycle total amount when relevant fields change
  useEffect(() => {
    const newAmount = calculateCycleTotalAmount();
    setBotForm(prev => ({ ...prev, cycle_total_amount: newAmount }));
  }, [botForm.min_bet_amount, botForm.max_bet_amount, botForm.cycle_games]);

  const [extendedValidation, setExtendedValidation] = useState({
    isValid: true,
    errors: []
  });

  const [activeTab, setActiveTab] = useState('bots'); // только 'bots'

  const { showSuccessRU, showErrorRU } = useNotifications();
  
  const { confirm, confirmationModal } = useConfirmation();
  
  const { prompt, inputModal } = useInput();

  const handleSelectBot = (botId) => {
    const newSelected = new Set(selectedBots);
    if (newSelected.has(botId)) {
      newSelected.delete(botId);
    } else {
      newSelected.add(botId);
    }
    setSelectedBots(newSelected);
    setShowBulkActions(newSelected.size > 0);
    
    setSelectAll(newSelected.size === botsList.length && botsList.length > 0);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedBots(new Set());
      setShowBulkActions(false);
    } else {
      const allBotIds = new Set(botsList.map(bot => bot.id));
      setSelectedBots(allBotIds);
      setShowBulkActions(true);
    }
    setSelectAll(!selectAll);
  };

  const clearSelection = () => {
    setSelectedBots(new Set());
    setSelectAll(false);
    setShowBulkActions(false);
  };

  const handleBulkToggleStatus = async (activate) => {
    if (selectedBots.size === 0) return;
    
    const action = activate ? 'активировать' : 'деактивировать';
    const actionPast = activate ? 'активированы' : 'деактивированы';
    
    const confirmed = await confirm({
      title: activate ? "Активация ботов" : "Деактивация ботов",
      message: `Вы уверены, что хотите ${action} ${selectedBots.size} ботов?`,
      confirmText: activate ? "Активировать" : "Деактивировать",
      cancelText: "Отмена",
      type: activate ? "success" : "warning"
    });
    
    if (!confirmed) return;
    
    setBulkActionLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const promises = Array.from(selectedBots).map(botId =>
        axios.post(`${API}/admin/bots/${botId}/toggle`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
      );
      
      await Promise.all(promises);
      showSuccessRU(`Успешно ${actionPast} ${selectedBots.size} ботов`);
      await fetchBotsList();
      clearSelection();
    } catch (error) {
      console.error(`Error bulk ${action} bots:`, error);
      showErrorRU(`Ошибка при ${action} ботов`);
    } finally {
      setBulkActionLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedBots.size === 0) return;
    
    const confirmed = await confirm({
      title: "Удаление ботов",
      message: `Вы уверены, что хотите удалить ${selectedBots.size} ботов? Это действие нельзя отменить.`,
      confirmText: "Удалить",
      cancelText: "Отмена",
      type: "danger"
    });
    
    if (!confirmed) return;
    
    setBulkActionLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const promises = Array.from(selectedBots).map(botId =>
        axios.delete(`${API}/admin/bots/${botId}/delete`, {
          headers: { Authorization: `Bearer ${token}` },
          data: { reason: 'Массовое удаление из админ-панели' }
        })
      );
      
      await Promise.all(promises);
      showSuccessRU(`Успешно удалены ${selectedBots.size} ботов`);
      await fetchBotsList();
      clearSelection();
    } catch (error) {
      console.error('Error bulk delete bots:', error);
      showErrorRU('Ошибка при удалении ботов');
    } finally {
      setBulkActionLoading(false);
    }
  };

  const handleBulkAction = async (action) => {
  };

  useEffect(() => {
    fetchStats();
    fetchBotsList();
    fetchActiveBetsStats();
  }, []);

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
      const response = await axios.get(`${API}/admin/bots/regular/list`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          page: pagination.currentPage,
          limit: pagination.itemsPerPage
        }
      });
      
      const botsData = response.data.bots || response.data;
      // Sort by creation date instead of priority_order (removed)
      const sortedBots = botsData.sort((a, b) => {
        return new Date(a.created_at) - new Date(b.created_at);
      });
      setBotsList(sortedBots);
      
      clearSelection();
      
      if (response.data.total_count !== undefined) {
        pagination.updatePagination(response.data.total_count);
      } else {
        pagination.updatePagination(botsData.length);
      }
    } catch (error) {
      console.error('Error fetching bots:', error);
      showErrorRU('Ошибка при загрузке ботов');
    }
  };

  const fetchBotQueueStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/queue-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error fetching bot queue status:', error);
      showErrorRU('Ошибка при загрузке статуса очереди');
      return null;
    }
  };

  const fetchBotWinRateAnalysis = async (botId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/${botId}/win-rate-analysis`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error fetching bot win rate analysis:', error);
      showErrorRU('Ошибка при загрузке анализа win rate');
      return null;
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
    setLoading(true);
    try {
      const response = await axios.post(`${API}/admin/bots/start-regular`, {}, getApiConfig());
      
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
      setLoading(false);
    }
  };



  const toggleAllBots = async () => {
    try {
      const newState = !allBotsEnabled;
      
      await axios.post(`${API}/admin/bots/toggle-all`, 
        { enabled: newState },
        getApiConfig()
      );
      
      setAllBotsEnabled(newState);
      await fetchStats(); // Refresh stats
    } catch (error) {
      console.error('Ошибка переключения ботов:', error);
    }
  };

  const validateExtendedBotForm = (formData) => {
    const errors = [];
    
    if (formData.min_bet_amount < 1 || formData.min_bet_amount > 10000) {
      errors.push('Минимальная ставка должна быть от 1 до 10000');
    }
    
    if (formData.max_bet_amount < 1 || formData.max_bet_amount > 10000) {
      errors.push('Максимальная ставка должна быть от 1 до 10000');
    }
    
    if (formData.min_bet_amount >= formData.max_bet_amount) {
      errors.push('Минимальная ставка должна быть меньше максимальной');
    }
    
    if (formData.win_percentage < 0 || formData.win_percentage > 100) {
      errors.push('Процент побед должен быть от 0 до 100');
    }
    
    if (formData.cycle_games < 1 || formData.cycle_games > 66) {
      errors.push('Количество игр в цикле должно быть от 1 до 66');
    }
    
    if (formData.pause_between_cycles < 1 || formData.pause_between_cycles > 300) {
      errors.push('Пауза между циклами должна быть от 1 до 300 секунд');
    }
    
    if (formData.pause_on_draw < 1 || formData.pause_on_draw > 60) {
      errors.push('Пауза при ничье должна быть от 1 до 60 секунд');
    }
    
    const validModes = ['always-first', 'queue-based', 'after-all'];
    if (!validModes.includes(formData.creation_mode)) {
      errors.push('Неверный режим создания ставок');
    }
    
    const validStrategies = ['start-positive', 'balanced', 'start-negative'];
    if (!validStrategies.includes(formData.profit_strategy)) {
      errors.push('Неверная стратегия прибыли');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  };

  const validateExtendedFormInRealTime = (formData) => {
    const validation = validateExtendedBotForm(formData);
    setExtendedValidation(validation);
    return validation.isValid;
  };

  const handleToggleBotStatus = async (bot) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/bots/${bot.id}/toggle-status`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        showSuccessRU(`Бот ${bot.name} ${bot.is_active ? 'отключен' : 'включен'}`);
        await fetchBotsList();
      }
    } catch (error) {
      console.error('Ошибка переключения статуса бота:', error);
      showErrorRU('Ошибка при изменении статуса бота');
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
      
      if (response.data.success) {
        showSuccessRU(`Цикл бота ${selectedBotForForceComplete.name} принудительно завершен. Прибыль: $${response.data.profit.toFixed(2)}`);
        setIsForceCompleteModalOpen(false);
        setSelectedBotForForceComplete(null);
        await fetchBotsList();
        await fetchStats();
      }
    } catch (error) {
      console.error('Ошибка принудительного завершения цикла:', error);
      showErrorRU('Ошибка при завершении цикла');
    }
  };

  const createExtendedBot = async () => {
    const validation = validateExtendedBotForm(botForm);
    if (!validation.isValid) {
      setExtendedValidation(validation);
      showErrorRU(`Ошибка валидации: ${validation.errors.join(', ')}`);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      
      const botData = {
        name: botForm.name,
        min_bet_amount: botForm.min_bet_amount,
        max_bet_amount: botForm.max_bet_amount,
        win_percentage: botForm.win_percentage,
        cycle_games: botForm.cycle_games,
        pause_between_cycles: botForm.pause_between_cycles,
        pause_on_draw: botForm.pause_on_draw,
        creation_mode: botForm.creation_mode,
        profit_strategy: botForm.profit_strategy
      };
      
      const response = await axios.post(`${API}/admin/bots/create-regular`, botData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showSuccessRU(response.data.message);
      setIsCreateModalOpen(false);
      
      setBotForm({
        name: '',
        min_bet_amount: 1.0,
        max_bet_amount: 50.0,
        win_percentage: 55.0,
        cycle_games: 12,
        pause_between_cycles: 5,
        pause_on_draw: 1,
        creation_mode: 'queue-based',
        profit_strategy: 'balanced',
        cycle_total_amount: 0
      });
      
      await fetchStats();
      await fetchBotsList();
      
    } catch (error) {
      console.error('Ошибка создания бота:', error);
      showErrorRU(error.response?.data?.detail || 'Ошибка при создании бота');
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

  const handleEditModal = async (bot) => {
    try {
      const response = await axios.get(`${API}/admin/bots/${bot.id}`, getApiConfig());
      
      setBotForm({
        name: response.data.bot.name || '',
        min_bet_amount: response.data.bot.min_bet_amount || 1.0,
        max_bet_amount: response.data.bot.max_bet_amount || 50.0,
        win_percentage: response.data.bot.win_percentage || response.data.bot.win_rate * 100 || 55.0,
        cycle_games: response.data.bot.cycle_games || 12,
        pause_between_games: response.data.bot.pause_between_games || 5,
        profit_strategy: response.data.bot.profit_strategy || 'balanced',
        cycle_total_amount: response.data.bot.cycle_total_amount || 0
      });
      
      setEditingBot(response.data.bot);
      setIsCreateModalOpen(true);
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
      const response = await axios.post(`${API}/admin/bots/${botId}/reset-bets`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        showSuccessRU(`Ставки бота сброшены и пересозданы. Отменено ставок: ${response.data.cancelled_bets}`);
        await fetchBotsList();
        await fetchStats();
      }
    } catch (error) {
      console.error('Ошибка сброса ставок:', error);
      showErrorRU('Ошибка при сбросе ставок бота');
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
    setSelectedBotForActiveBets(bot);
    setLoadingActiveBets(true);
    setIsActiveBetsModalOpen(true);
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await axios.get(`${API}/admin/bots/${bot.id}/active-bets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('Active Bets API Response:', response.data);
      
      const data = response.data;
      
      setActiveBetsData({
        bets: data.bets || [],
        totalBets: data.totalBets || 0,
        totalBetAmount: data.totalBetAmount || 0,
        gamesPlayed: data.gamesPlayed || 0,
        botWins: data.botWins || 0,
        playerWins: data.playerWins || 0,
        draws: data.draws || 0,
        remaining_slots: data.remaining_slots || 0,
        current_cycle_played: data.current_cycle_played || 0,
        cycle_games: data.cycle_games || 12,
        actions_taken: data.actions_taken || { cancelled: 0, created: 0 }
      });
      
      if (data.actions_taken?.cancelled > 0) {
        showSuccessRU(`Отменено ${data.actions_taken.cancelled} лишних ставок`);
      }
      if (data.actions_taken?.created > 0) {
        showSuccessRU(`Создано ${data.actions_taken.created} новых ставок`);
      }
      
    } catch (error) {
      console.error('Ошибка загрузки активных ставок:', error);
      showErrorRU('Ошибка при загрузке активных ставок');
      
      setActiveBetsData({
        bets: [],
        totalBets: 0,
        totalBetAmount: 0,
        gamesPlayed: 0,
        botWins: 0,
        playerWins: 0,
        draws: 0,
        remaining_slots: 0,
        current_cycle_played: 0,
        cycle_games: 12,
        actions_taken: { cancelled: 0, created: 0 }
      });
    } finally {
      setLoadingActiveBets(false);
    }
  };

  const handleCycleModal = async (bot) => {
    try {
      const response = await axios.get(`${API}/admin/bots/${bot.id}/cycle-history`, getApiConfig());
      
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

  const handleEditBotLimit = (botId, currentLimit) => {
    setEditingBotLimits(prev => ({
      ...prev,
      [botId]: {
        limit: currentLimit || 12,
        saving: false
      }
    }));
  };

  const handleCancelEditBotLimit = (botId) => {
    setEditingBotLimits(prev => {
      const newState = { ...prev };
      delete newState[botId];
      return newState;
    });
    setBotLimitsValidation(prev => {
      const newState = { ...prev };
      delete newState[botId];
      return newState;
    });
  };

  const handleBotLimitChange = (botId, newLimit) => {
    const limit = parseInt(newLimit);
    
    let error = null;
    if (isNaN(limit) || limit < 1) {
      error = 'Лимит должен быть больше 0';
    } else if (limit > 66) {
      error = 'Лимит не может быть больше 66';
    }
    
    setEditingBotLimits(prev => ({
      ...prev,
      [botId]: {
        ...prev[botId],
        limit: newLimit
      }
    }));
    
    setBotLimitsValidation(prev => ({
      ...prev,
      [botId]: error
    }));
  };

  const handleSaveBotLimit = async (botId) => {
    const editData = editingBotLimits[botId];
    if (!editData || botLimitsValidation[botId]) return;
    
    setEditingBotLimits(prev => ({
      ...prev,
      [botId]: {
        ...prev[botId],
        saving: true
      }
    }));
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(`${API}/admin/bots/${botId}/limit`, {
        maxIndividualBets: parseInt(editData.limit)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        showSuccessRU('Лимит бота успешно обновлен');
        
        setBotsList(prev => prev.map(bot => 
          bot.id === botId 
            ? { ...bot, max_individual_bets: parseInt(editData.limit) }
            : bot
        ));
        
        handleCancelEditBotLimit(botId);
        
        await fetchActiveBetsStats();
      }
    } catch (error) {
      console.error('Error updating bot limit:', error);
      showErrorRU('Ошибка при обновлении лимита бота');
    } finally {
      setEditingBotLimits(prev => ({
        ...prev,
        [botId]: {
          ...prev[botId],
          saving: false
        }
      }));
    }
  };



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

  const handleOpenBotProfitModal = async (bot) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/profit-accumulators?page=1&limit=20&bot_id=${bot.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSelectedBotForProfit(bot);
      setBotProfitAccumulators(response.data.accumulators || []);
      setBotProfitPagination(response.data.pagination || { current_page: 1, total_pages: 1 });
      setIsBotProfitModalOpen(true);
      showSuccessRU(`Загружены накопители прибыли для бота: ${bot.name}`);
    } catch (error) {
      console.error('Error fetching bot profit accumulators:', error);
      showErrorRU('Ошибка при загрузке накопителей прибыли бота');
    }
  };

  // Функции для редактирования процента выигрышей и паузы
  const handleEditWinPercentage = async (bot) => {
    try {
      const currentPercentage = bot.win_percentage || 55;
      const userInput = window.prompt(
        `Введите новый процент выигрышей для бота ${bot.name || `Bot #${bot.id.substring(0, 3)}`}:\n\nТекущий: ${currentPercentage}%\n(Допустимые значения: 0-100)`,
        currentPercentage
      );

      if (userInput === null) return; // Пользователь отменил

      const newPercentage = parseFloat(userInput);
      if (isNaN(newPercentage) || newPercentage < 0 || newPercentage > 100) {
        showErrorRU('Процент должен быть числом от 0 до 100');
        return;
      }

      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/bots/${bot.id}/win-percentage?win_percentage=${newPercentage}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchBotsList();
      showSuccessRU(`Процент выигрышей обновлен на ${newPercentage}%`);
    } catch (error) {
      console.error('Error updating win percentage:', error);
      showErrorRU('Ошибка при обновлении процента выигрышей');
    }
  };

  const handleEditPause = async (bot) => {
    try {
      const currentPause = bot.pause_between_games || 5;
      const userInput = window.prompt(
        `Введите новую паузу между играми для бота ${bot.name || `Bot #${bot.id.substring(0, 3)}`}:\n\nТекущая: ${currentPause} секунд\n(Допустимые значения: 1-3600)`,
        currentPause
      );

      if (userInput === null) return; // Пользователь отменил

      const newPause = parseInt(userInput);
      if (isNaN(newPause) || newPause < 1 || newPause > 3600) {
        showErrorRU('Пауза должна быть числом от 1 до 3600 секунд');
        return;
      }

      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/bots/${bot.id}/pause-settings?pause_between_games=${newPause}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchBotsList();
      showSuccessRU(`Пауза обновлена на ${newPause} секунд`);
    } catch (error) {
      console.error('Error updating pause settings:', error);
      showErrorRU('Ошибка при обновлении настроек паузы');
    }
  };

  return (
    <div className="space-y-6">
      {/* Заголовок и кнопки управления */}
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

      {/* Табы */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="border-b border-border-primary">
          <button
            onClick={() => setActiveTab('bots')}
            className="flex-1 px-6 py-4 text-center font-rajdhani font-bold bg-accent-primary text-white border-b-2 border-accent-primary w-full"
          >
            📋 Список ботов
          </button>
        </div>

        {/* Содержимое табов */}
        <div className="p-6">
          {activeTab === 'bots' && (
            <div className="space-y-6">
              {/* Весь существующий контент со статистикой и списком ботов */}

      {/* Статистика активных ставок */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
        <h3 className="text-lg font-rajdhani font-bold text-white mb-3">Оставшиеся ставки обычных ботов</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-surface-sidebar rounded-lg p-3">
            <div className="text-text-secondary text-sm">Оставшиеся ставки</div>
            <div className="text-white text-xl font-rajdhani font-bold">
              {botsList.filter(bot => bot.is_active).reduce((total, bot) => total + (bot.remaining_slots || 0), 0)}
            </div>
          </div>
          <div className="bg-surface-sidebar rounded-lg p-3">
            <div className="text-text-secondary text-sm">Отыгранные ставки</div>
            <div className="text-accent-primary text-xl font-rajdhani font-bold">
              {botsList.filter(bot => bot.is_active).reduce((total, bot) => total + (bot.current_cycle_games || 0), 0)}
            </div>
          </div>
          <div className="bg-surface-sidebar rounded-lg p-3">
            <div className="text-text-secondary text-sm">Общий потенциал</div>
            <div className="text-green-400 text-xl font-rajdhani font-bold">
              {botsList.filter(bot => bot.is_active).reduce((total, bot) => total + (bot.cycle_games || 12), 0)}
            </div>
          </div>
          <div className="bg-surface-sidebar rounded-lg p-3">
            <div className="text-text-secondary text-sm">Прогресс циклов</div>
            <div className={`text-xl font-rajdhani font-bold ${
              (() => {
                const activeBots = botsList.filter(bot => bot.is_active);
                const totalPlayed = activeBots.reduce((total, bot) => total + (bot.current_cycle_games || 0), 0);
                const totalCycle = activeBots.reduce((total, bot) => total + (bot.cycle_games || 12), 0);
                const percentage = totalCycle > 0 ? Math.round((totalPlayed / totalCycle) * 100) : 0;
                
                return percentage >= 90 ? 'text-red-400' :
                       percentage >= 70 ? 'text-yellow-400' : 'text-green-400';
              })()
            }`}>
              {(() => {
                const activeBots = botsList.filter(bot => bot.is_active);
                const totalPlayed = activeBots.reduce((total, bot) => total + (bot.current_cycle_games || 0), 0);
                const totalCycle = activeBots.reduce((total, bot) => total + (bot.cycle_games || 12), 0);
                return totalCycle > 0 ? Math.round((totalPlayed / totalCycle) * 100) : 0;
              })()}%
            </div>
          </div>
        </div>
        
        {/* Прогресс-бар */}
        <div className="mt-4">
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                (() => {
                  const activeBots = botsList.filter(bot => bot.is_active);
                  const totalPlayed = activeBots.reduce((total, bot) => total + (bot.current_cycle_games || 0), 0);
                  const totalCycle = activeBots.reduce((total, bot) => total + (bot.cycle_games || 12), 0);
                  const percentage = totalCycle > 0 ? Math.round((totalPlayed / totalCycle) * 100) : 0;
                  
                  return percentage >= 90 ? 'bg-red-500' :
                         percentage >= 70 ? 'bg-yellow-500' : 'bg-green-500';
                })()
              }`}
              style={{ 
                width: `${(() => {
                  const activeBots = botsList.filter(bot => bot.is_active);
                  const totalPlayed = activeBots.reduce((total, bot) => total + (bot.current_cycle_games || 0), 0);
                  const totalCycle = activeBots.reduce((total, bot) => total + (bot.cycle_games || 12), 0);
                  const percentage = totalCycle > 0 ? Math.round((totalPlayed / totalCycle) * 100) : 0;
                  return Math.min(100, percentage);
                })()}%`
              }}
            ></div>
          </div>
          <div className="text-text-secondary text-xs mt-1">
            {botsList.filter(bot => bot.is_active).reduce((total, bot) => total + (bot.current_cycle_games || 0), 0)} отыгранных из {botsList.filter(bot => bot.is_active).reduce((total, bot) => total + (bot.cycle_games || 12), 0)} общего потенциала
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

      {/* Модальное окно накопителей прибыли конкретного бота */}
      {isBotProfitModalOpen && selectedBotForProfit && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-blue-500 border-opacity-50 rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-border-primary">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-600 rounded-lg">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-rajdhani text-xl font-bold text-white">📊 Накопители прибыли бота</h3>
                  <p className="text-blue-400 font-rajdhani font-bold">{selectedBotForProfit.name}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setIsBotProfitModalOpen(false);
                  setSelectedBotForProfit(null);
                  setBotProfitAccumulators([]);
                }}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Информация о боте */}
            <div className="px-6 py-4 bg-surface-sidebar border-b border-border-primary">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{selectedBotForProfit.current_cycle_games || 0}</div>
                  <div className="text-text-secondary text-sm">Текущий цикл игр</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">{selectedBotForProfit.active_bets || 0}</div>
                  <div className="text-text-secondary text-sm">Активные ставки</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">{selectedBotForProfit.win_rate || 0}%</div>
                  <div className="text-text-secondary text-sm">Win Rate</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${selectedBotForProfit.is_active ? 'text-green-400' : 'text-red-400'}`}>
                    {selectedBotForProfit.is_active ? 'Активен' : 'Неактивен'}
                  </div>
                  <div className="text-text-secondary text-sm">Статус бота</div>
                </div>
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(90vh-280px)]">
              {botProfitAccumulators.length === 0 ? (
                <div className="text-center text-text-secondary py-12">
                  <div className="text-8xl mb-4">📊</div>
                  <h4 className="font-rajdhani text-xl font-bold mb-2">Нет данных о циклах</h4>
                  <p className="text-lg">У бота <span className="text-blue-400 font-bold">{selectedBotForProfit.name}</span> пока нет завершённых циклов</p>
                  <div className="mt-4 text-sm text-text-secondary bg-surface-sidebar rounded-lg p-4 max-w-md mx-auto">
                    <p><strong>Примечание:</strong> Циклы появятся здесь после того, как бот сыграет достаточно игр или цикл будет завершён принудительно</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Сводка по всем циклам */}
                  <div className="bg-surface-sidebar rounded-lg p-4">
                    <h4 className="font-rajdhani text-lg font-bold text-white mb-3">📈 Сводка по всем циклам</h4>
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                      <div className="text-center">
                        <div className="text-lg font-bold text-blue-400">
                          {botProfitAccumulators.length}
                        </div>
                        <div className="text-text-secondary text-sm">Всего циклов</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-red-400">
                          ${botProfitAccumulators.reduce((sum, acc) => sum + acc.total_spent, 0).toFixed(2)}
                        </div>
                        <div className="text-text-secondary text-sm">Потрачено</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-400">
                          ${botProfitAccumulators.reduce((sum, acc) => sum + acc.total_earned, 0).toFixed(2)}
                        </div>
                        <div className="text-text-secondary text-sm">Заработано</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-lg font-bold ${
                          botProfitAccumulators.reduce((sum, acc) => sum + acc.profit, 0) > 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          ${botProfitAccumulators.reduce((sum, acc) => sum + acc.profit, 0).toFixed(2)}
                        </div>
                        <div className="text-text-secondary text-sm">Общая прибыль</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-purple-400">
                          {botProfitAccumulators.length > 0 ? (
                            (botProfitAccumulators.reduce((sum, acc) => sum + acc.win_rate, 0) / botProfitAccumulators.length).toFixed(1)
                          ) : 0}%
                        </div>
                        <div className="text-text-secondary text-sm">Средний Win Rate</div>
                      </div>
                    </div>
                  </div>

                  {/* Таблица циклов */}
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-surface-sidebar">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Цикл</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Игры</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Потрачено</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Заработано</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Прибыль</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Win Rate</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Статус</th>
                          <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Период</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-primary">
                        {botProfitAccumulators.map((accumulator) => (
                          <tr key={accumulator.id} className="hover:bg-surface-sidebar hover:bg-opacity-50">
                            <td className="px-4 py-3 text-blue-400 font-bold text-lg">#{accumulator.cycle_number}</td>
                            <td className="px-4 py-3 text-white">
                              <div className="flex items-center space-x-2">
                                <span className="font-bold">{accumulator.games_completed}</span>
                                <span className="text-text-secondary text-sm">игр</span>
                                <span className="text-green-400 font-bold">({accumulator.games_won} ★)</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-red-400 font-bold">${accumulator.total_spent.toFixed(2)}</td>
                            <td className="px-4 py-3 text-green-400 font-bold">${accumulator.total_earned.toFixed(2)}</td>
                            <td className={`px-4 py-3 font-bold text-lg ${
                              accumulator.profit > 0 ? 'text-green-400' : 
                              accumulator.profit < 0 ? 'text-red-400' : 'text-gray-400'
                            }`}>
                              {accumulator.profit > 0 ? '+' : ''}${accumulator.profit.toFixed(2)}
                            </td>
                            <td className="px-4 py-3 text-white font-bold">{accumulator.win_rate.toFixed(1)}%</td>
                            <td className="px-4 py-3">
                              <span className={`px-3 py-1 text-xs rounded-full font-rajdhani font-bold ${
                                accumulator.is_cycle_completed 
                                  ? 'bg-green-600 text-white' 
                                  : 'bg-yellow-600 text-white'
                              }`}>
                                {accumulator.is_cycle_completed ? '✓ Завершён' : '⏳ Активный'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-text-secondary text-sm">
                              <div>{new Date(accumulator.created_at).toLocaleDateString('ru-RU')}</div>
                              {accumulator.cycle_end_date && (
                                <div className="text-xs">
                                  - {new Date(accumulator.cycle_end_date).toLocaleDateString('ru-RU')}
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Пагинация */}
              {botProfitPagination.total_pages > 1 && (
                <div className="flex justify-center mt-6">
                  <div className="flex space-x-2">
                    {Array.from({ length: botProfitPagination.total_pages }, (_, i) => i + 1).map(page => (
                      <button
                        key={page}
                        onClick={() => {/* TODO: Implement pagination for bot profit */}}
                        className={`px-3 py-1 rounded ${
                          page === botProfitPagination.current_page
                            ? 'bg-blue-600 text-white'
                            : 'bg-surface-sidebar text-text-secondary hover:text-white'
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-between items-center p-6 border-t border-border-primary">
              <div className="text-text-secondary text-sm">
                💡 <strong>Совет:</strong> Используйте кнопку "⚡ Завершить цикл" для принудительного завершения текущего цикла
              </div>
              <button
                onClick={() => {
                  setIsBotProfitModalOpen(false);
                  setSelectedBotForProfit(null);
                  setBotProfitAccumulators([]);
                }}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Таблица ботов */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border-primary">
          <h3 className="text-lg font-rajdhani font-bold text-white">Список обычных ботов</h3>
        </div>

        {/* Панель массовых действий */}
        {showBulkActions && (
          <div className="p-4 bg-accent-primary bg-opacity-10 border-b border-border-primary">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-white font-roboto text-sm">
                  Выбрано ботов: <span className="font-bold">{selectedBots.size}</span>
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleBulkToggleStatus(true)}
                  disabled={bulkActionLoading}
                  className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
                >
                  {bulkActionLoading ? 'Загрузка...' : 'Включить всех'}
                </button>
                <button
                  onClick={() => handleBulkToggleStatus(false)}
                  disabled={bulkActionLoading}
                  className="px-3 py-1 bg-yellow-600 text-white text-xs rounded hover:bg-yellow-700 disabled:opacity-50 transition-colors"
                >
                  {bulkActionLoading ? 'Загрузка...' : 'Выключить всех'}
                </button>
                <button
                  onClick={handleBulkDelete}
                  disabled={bulkActionLoading}
                  className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {bulkActionLoading ? 'Загрузка...' : 'Удалить всех'}
                </button>
                <button
                  onClick={clearSelection}
                  className="px-3 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-700 transition-colors"
                >
                  Отменить выбор
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-sidebar">
              <tr>
                <th className="px-4 py-3 text-center text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  <input
                    type="checkbox"
                    checked={selectAll}
                    onChange={handleSelectAll}
                    className="w-4 h-4 text-accent-primary bg-surface-primary border-border-primary rounded focus:ring-accent-primary focus:ring-2"
                  />
                </th>
                <th className="px-4 py-3 text-center text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  №
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Имя
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Статус
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Ставки
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Статистика
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  %
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Лимиты
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Цикл
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Активность бота
                </th>                
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Ставки
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Сумма цикла
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Стратегия
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Пауза
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Регистрация
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-primary">
              {botsList.length === 0 ? (
                <tr>
                  <td colSpan="16" className="px-4 py-8 text-center text-text-secondary">
                    Нет ботов для отображения
                  </td>
                </tr>
              ) : (
                botsList.map((bot, index) => (
                  <tr key={bot.id} className="hover:bg-surface-sidebar hover:bg-opacity-50">
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <input
                        type="checkbox"
                        checked={selectedBots.has(bot.id)}
                        onChange={() => handleSelectBot(bot.id)}
                        className="w-4 h-4 text-accent-primary bg-surface-primary border-border-primary rounded focus:ring-accent-primary focus:ring-2"
                      />
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="text-white font-roboto text-sm font-bold">
                        {index + 1}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="text-white font-roboto text-sm">
                        {bot.name || `Bot #${bot.id.substring(0, 3)}`}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <span className={`px-2 py-1 text-xs rounded-full font-roboto font-medium ${
                        bot.is_active 
                          ? 'bg-green-600 text-white' 
                          : 'bg-red-600 text-white'
                      }`}>
                        {bot.is_active ? 'Активен' : 'Отключен'}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <button
                        onClick={() => handleActiveBetsModal(bot)}
                        className="text-blue-400 hover:text-blue-300 underline font-roboto text-sm cursor-pointer"
                        title="Показать активные ставки"
                      >
                        {bot.remaining_slots || (bot.cycle_games - bot.current_cycle_games) || 0}
                      </button>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-left">
                      <div className="text-white font-roboto text-xs space-y-1">
                        <div>Игры: {bot.completed_cycles || 0}</div>
                        <div>W/L/D: {bot.current_cycle_wins || 0}/{bot.current_cycle_losses || 0}/{bot.current_cycle_draws || 0}</div>
                        <div className="text-green-400">Прибыль: ${(bot.current_cycle_profit || 0).toFixed(2)}</div>
                        <div className="text-blue-400">Чистая: ${(bot.total_net_profit || 0).toFixed(2)}</div>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center space-x-1">
                        <span className="text-orange-400 font-roboto text-sm font-bold">
                          {Math.round(bot.win_percentage || 55)}%
                        </span>
                        <button
                          onClick={() => handleEditWinPercentage(bot)}
                          className="text-gray-400 hover:text-white transition-colors p-1"
                          title="Редактировать процент выигрышей"
                        >
                          ✏️
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="text-accent-primary font-roboto text-xs">
                        <div>Мин: {formatAsGems(bot.min_bet_amount || bot.min_bet || 1)}</div>
                        <div>Макс: {formatAsGems(bot.max_bet_amount || bot.max_bet || 100)}</div>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="w-full max-w-24 mx-auto">
                        <div className="w-full bg-surface-sidebar rounded-full h-2 mb-2">
                          <div
                            className="bg-green-500 h-2 rounded-full transition-all duration-300"
                            style={{
                              width: `${Math.min(((bot.current_cycle_games || 0) / (bot.cycle_games || 12)) * 100, 100)}%`
                            }}
                          ></div>
                        </div>
                        <div className="flex items-center justify-center space-x-2">
                          <button
                            onClick={() => handleCycleModal(bot)}
                            className="text-green-400 hover:text-green-300 cursor-pointer font-roboto text-sm font-medium"
                            title="Показать историю цикла"
                          >
                            {bot.cycle_progress || `${(bot.current_cycle_games || 0)}/${bot.cycle_games || 12}`}
                          </button>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center">
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={bot.is_active || false}
                            onChange={() => toggleBotStatus(bot.id)}
                            className="sr-only peer"
                          />
                          <div className="relative w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                          <span className="ml-3 text-sm font-medium text-white">
                            {bot.is_active ? 'Вкл' : 'Выкл'}
                          </span>
                        </label>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <button
                        onClick={() => handleActiveBetsModal(bot)}
                        className="text-yellow-400 hover:text-yellow-300 font-roboto text-sm font-bold cursor-pointer"
                        title="Показать активные ставки"
                      >
                        {bot.active_bets || 0}
                      </button>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="text-accent-primary font-roboto text-sm">
                        {Math.round(((bot.min_bet_amount || bot.min_bet || 1) + (bot.max_bet_amount || bot.max_bet || 100)) / 2 * (bot.cycle_games || 12))}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <span className={`px-3 py-1 text-xs rounded-full font-roboto font-medium ${
                        (() => {
                          const strategy = bot.profit_strategy || 'balanced';
                          switch(strategy) {
                            case 'start-positive': 
                            case 'start_profit': 
                              return 'bg-blue-600 text-white';
                            case 'start-negative': 
                            case 'end_loss': 
                              return 'bg-red-600 text-white';
                            case 'balanced': 
                            default: 
                              return 'bg-green-600 text-white';
                          }
                        })()
                      }`}>
                        {(() => {
                          const strategy = bot.profit_strategy || 'balanced';
                          switch(strategy) {
                            case 'start-positive': return 'Ранняя прибыль';
                            case 'start_profit': return 'Ранняя прибыль';
                            case 'start-negative': return 'Поздние потери';
                            case 'end_loss': return 'Поздние потери';
                            case 'balanced': return 'Сбалансированная';
                            default: return 'Сбалансированная';
                          }
                        })()}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center space-x-1">
                        <span className="text-cyan-400 font-roboto text-sm font-bold">
                          {bot.pause_between_cycles || bot.pause_between_games ? `${bot.pause_between_cycles || bot.pause_between_games}с` : '5с'}
                        </span>
                        <button
                          onClick={() => handleEditPause(bot)}
                          className="text-gray-400 hover:text-white transition-colors p-1"
                          title="Редактировать паузу между циклами"
                        >
                          ✏️
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="text-white font-roboto text-sm">
                        {bot.created_at ? new Date(bot.created_at).toLocaleDateString('ru-RU') : 'Не указано'}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="flex space-x-2 justify-center">
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
                          onClick={() => recalculateBotBets(bot.id)}
                          className="p-1 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                          title="Пересчет ставок"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleForceCompleteModal(bot)}
                          className="p-1 bg-orange-600 text-white rounded hover:bg-orange-700"
                          title="Завершить цикл принудительно"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDeleteModal(bot)}
                          className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                          title="Удалить"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
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
            </div>
          )}
        </div>
      </div>

      {/* Модальное окно создания бота */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-white">
                {editingBot ? 'Редактировать бота' : 'Создать обычного бота'}
              </h3>
              <button
                onClick={() => {
                  setIsCreateModalOpen(false);
                  setEditingBot(null);
                }}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

              {/* Имя бота */}
              <div>
                <label className="block text-text-secondary text-sm mb-2">Имя бота (опционально):</label>
                <input
                  type="text"
                  value={botForm.name}
                  onChange={(e) => {
                    setBotForm({...botForm, name: e.target.value});
                    validateExtendedFormInRealTime({...botForm, name: e.target.value});
                  }}
                  placeholder="Оставьте пустым для автоматической генерации"
                  className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                />
                <div className="text-xs text-text-secondary mt-1">
                  Отображается только в админке, игрокам показывается просто "Bot"
                </div>
              </div>

            <div className="space-y-6">
              {/* Диапазон ставок */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Диапазон ставок</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Минимальная ставка (гемы):</label>
                    <input
                      type="number"
                      min="1"
                      max="10000"
                      step="1"
                      value={botForm.min_bet_amount}
                      onChange={(e) => {
                        const newForm = {...botForm, min_bet_amount: parseInt(e.target.value) || 1};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Максимальная ставка (гемы):</label>
                    <input
                      type="number"
                      min="1"
                      max="10000"
                      step="1"
                      value={botForm.max_bet_amount}
                      onChange={(e) => {
                        const newForm = {...botForm, max_bet_amount: parseInt(e.target.value) || 50};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                </div>
                <div className="text-xs text-text-secondary mt-1">
                  Диапазон сумм ставок в гемах (1-10000)
                </div>
              </div>

              {/* Процент побед и стратегия прибыли */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Настройки выигрыша</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Процент побед:</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={botForm.win_percentage}
                      onChange={(e) => {
                        const newForm = {...botForm, win_percentage: parseFloat(e.target.value) || 55.0};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                    <div className="text-xs text-text-secondary mt-1">
                      Целевой процент побед (0-100%, по умолчанию 55%)
                    </div>
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Стратегия прибыли:</label>
                    <select
                      value={botForm.profit_strategy}
                      onChange={(e) => {
                        const newForm = {...botForm, profit_strategy: e.target.value};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    >
                      <option value="start-positive">В начале в плюсе</option>
                      <option value="balanced">Баланс</option>
                      <option value="start-negative">В минусе</option>
                    </select>
                    <div className="text-xs text-text-secondary mt-1">
                      Поведение бота в рамках цикла
                    </div>
                  </div>
                </div>
              </div>

              {/* Игр в цикле и индивидуальный лимит */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Циклы и лимиты</h4>
                <div>
                  <label className="block text-text-secondary text-sm mb-1">Игр в цикле:</label>
                  <input
                    type="number"
                    min="1"
                    max="66"
                    value={botForm.cycle_games}
                    onChange={(e) => {
                      const newValue = parseInt(e.target.value) || 12;
                      const newForm = {...botForm, cycle_games: newValue};
                      setBotForm(newForm);
                      validateExtendedFormInRealTime(newForm);
                    }}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                  />
                </div>
                <div className="text-xs text-text-secondary mt-1">
                  Количество игр в одном цикле (1-66)
                </div>
              </div>

              {/* Настройки таймингов */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Настройки таймингов</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Пауза между циклами (сек):</label>
                    <input
                      type="number"
                      min="1"
                      max="300"
                      value={botForm.pause_between_cycles}
                      onChange={(e) => {
                        const newForm = {...botForm, pause_between_cycles: parseInt(e.target.value) || 5};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                    <div className="text-xs text-text-secondary mt-1">
                      Интервал после завершения цикла до начала нового
                    </div>
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Пауза при ничье (сек):</label>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      value={botForm.pause_on_draw}
                      onChange={(e) => {
                        const newForm = {...botForm, pause_on_draw: parseInt(e.target.value) || 1};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                    <div className="text-xs text-text-secondary mt-1">
                      При ничье создается новая ставка через указанное время
                    </div>
                  </div>
                </div>
              </div>

              {/* Автоматически рассчитанная сумма за цикл */}
              <div className="border border-blue-500 bg-blue-900 bg-opacity-20 rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-blue-400 mb-2">Автоматический расчёт</h4>
                <div className="text-lg font-bold text-white">
                  Сумма за цикл: ${botForm.cycle_total_amount}
                </div>
                <div className="text-sm text-blue-300 mt-1">
                  Рассчитывается по формуле: (Мин. ставка + Макс. ставка) / 2 × Игр в цикле
                </div>
              </div>

              {/* Отображение ошибок валидации */}
              {!extendedValidation.isValid && (
                <div className="border border-red-500 bg-red-900 bg-opacity-20 rounded-lg p-4">
                  <h4 className="font-rajdhani font-bold text-red-400 mb-2">Ошибки валидации:</h4>
                  <ul className="space-y-1">
                    {extendedValidation.errors.map((error, index) => (
                      <li key={index} className="text-red-300 text-sm">• {error}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Кнопки */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={createExtendedBot}
                  disabled={!extendedValidation.isValid}
                  className={`px-6 py-3 rounded-lg font-rajdhani font-bold transition-colors ${
                    extendedValidation.isValid 
                      ? 'bg-accent-primary text-white hover:bg-accent-secondary' 
                      : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {editingBot ? 'Сохранить изменения' : 'Создать бота'}
                </button>
                <button
                  onClick={() => {
                    setIsCreateModalOpen(false);
                    setEditingBot(null);
                    setExtendedValidation({ isValid: true, errors: [] });
                  }}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      
      {/* Модальное окно просмотра активных ставок */}
      {isActiveBetsModalOpen && selectedBotForActiveBets && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 w-full max-w-6xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                {/* Иконка приложения */}
                <div className="p-2 bg-blue-600 rounded-lg">
                  <img src="/Bot.svg" alt="Bot" className="w-8 h-8 filter brightness-0 invert" />
                </div>
                <h3 className="font-russo text-xl text-white">
                  Активные ставки — Bot
                </h3>
              </div>
              
              {/* Общая сумма в правом верхнем углу */}
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-text-secondary text-sm">Общая сумма</div>
                  <div className="text-accent-primary text-2xl font-rajdhani font-bold">
                    ${activeBetsData?.bets ? 
                      activeBetsData.bets.reduce((sum, bet) => sum + (bet.bet_amount || bet.amount || 0), 0).toFixed(2) : 
                      0}
                  </div>
                </div>
                <button
                  onClick={() => {
                    setIsActiveBetsModalOpen(false);
                    setSelectedBotForActiveBets(null);
                    setActiveBetsData(null);
                  }}
                  className="text-text-secondary hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>
            </div>
            
            {loadingActiveBets ? (
              <div className="flex justify-center items-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary"></div>
                <span className="ml-3 text-text-secondary">Загрузка активных ставок...</span>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Детальная статистика */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-surface-sidebar rounded-lg p-4">
                    <div className="text-text-secondary text-sm">Активные ставки</div>
                    <div className="text-blue-400 text-2xl font-rajdhani font-bold">
                      {activeBetsData?.totalBets || 0}
                    </div>
                    <div className="text-text-secondary text-xs">
                      Из {activeBetsData?.remaining_slots || 0} возможных
                    </div>
                  </div>
                  <div className="bg-surface-sidebar rounded-lg p-4">
                    <div className="text-text-secondary text-sm">Прогресс цикла</div>
                    <div className="text-white text-2xl font-rajdhani font-bold">
                      {activeBetsData?.current_cycle_played || 0}/{activeBetsData?.cycle_games || 12}
                    </div>
                    <div className="text-text-secondary text-xs">
                      Отыгранных ставок
                    </div>
                  </div>
                  <div className="bg-surface-sidebar rounded-lg p-4">
                    <div className="text-text-secondary text-sm">Выигрыши бота</div>
                    <div className="text-green-400 text-2xl font-rajdhani font-bold">
                      {activeBetsData?.botWins || 0}
                    </div>
                    <div className="text-text-secondary text-xs">
                      Побед
                    </div>
                  </div>
                  <div className="bg-surface-sidebar rounded-lg p-4">
                    <div className="text-text-secondary text-sm">Выигрыши игроков</div>
                    <div className="text-orange-400 text-2xl font-rajdhani font-bold">
                      {activeBetsData?.playerWins || 0}
                    </div>
                    <div className="text-text-secondary text-xs">
                      Поражений
                    </div>
                  </div>
                </div>

                {/* Информация о действиях */}
                {activeBetsData?.actions_taken && (activeBetsData.actions_taken.cancelled > 0 || activeBetsData.actions_taken.created > 0) && (
                  <div className="bg-blue-900 bg-opacity-20 border border-blue-500 rounded-lg p-4 mb-4">
                    <div className="flex items-center space-x-2">
                      <span className="text-blue-400 text-xl">ℹ️</span>
                      <div>
                        <h4 className="font-rajdhani font-bold text-blue-400">Автоматические действия</h4>
                        <p className="text-blue-300 text-sm">
                          {activeBetsData.actions_taken.cancelled > 0 && 
                            `Отменено ${activeBetsData.actions_taken.cancelled} лишних ставок. `}
                          {activeBetsData.actions_taken.created > 0 && 
                            `Создано ${activeBetsData.actions_taken.created} новых ставок. `}
                          Количество активных ставок приведено в соответствие с циклом бота.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {!activeBetsData?.bets || activeBetsData.bets.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-text-secondary text-lg">
                      У бота нет активных ставок в данный момент
                    </div>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-surface-sidebar">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">№</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">ID</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Дата</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Время</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Ставка</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Гемы</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Ходы</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Соперник</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Статус</th>
                          <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Результат</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-primary">
                        {activeBetsData.bets.map((bet, index) => {
                          const betDate = new Date(bet.created_at);
                          const dateStr = betDate.toLocaleDateString('ru-RU');
                          const timeStr = betDate.toLocaleTimeString('ru-RU');
                          
                          return (
                            <tr key={bet.id || index} className="hover:bg-green-900 hover:bg-opacity-20 transition-colors hover:border-l-4 hover:border-green-400">
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto text-white font-bold">
                                  {index + 1}
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto text-white font-mono">
                                  {bet.id ? bet.id.substring(0, 8) : `#${index + 1}`}
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto text-white">
                                  {dateStr}
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto text-white">
                                  {timeStr}
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto font-bold text-accent-primary">
                                  ${bet.bet_amount || bet.amount || 0}
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto text-text-secondary">
                                  {bet.bet_gems ? 
                                    Object.entries(bet.bet_gems).map(([gem, qty]) => `${gem}: ${qty}`).join(', ') : 
                                    'N/A'
                                  }
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-xs space-y-1">
                                  <div className="text-blue-300">Бот: {bet.bot_move || bet.move || '—'}</div>
                                  <div className="text-orange-300">Соперник: {bet.opponent_move || '—'}</div>
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-roboto font-medium ${
                                  bet.status === 'active' ? 'bg-green-600 text-white' :
                                  bet.status === 'waiting' ? 'bg-yellow-600 text-white' :
                                  bet.status === 'reveal' ? 'bg-blue-600 text-white' :
                                  bet.status === 'completed' ? 'bg-purple-600 text-white' :
                                  'bg-gray-600 text-white'
                                }`}>
                                  {bet.status === 'active' ? 'Активна' :
                                   bet.status === 'waiting' ? 'Ожидает' :
                                   bet.status === 'reveal' ? 'Раскрытие' :
                                   bet.status === 'completed' ? 'Завершена' :
                                   bet.status || 'Неизвестно'}
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto text-white">
                                  {bet.opponent_name || bet.opponent_id || '—'}
                                </div>
                              </td>
                              <td className="px-4 py-3">
                                <div className="text-sm font-roboto">
                                  {bet.status === 'completed' ? (
                                    <span className={`font-bold ${
                                      bet.winner_id === selectedBotForActiveBets.id ? 'text-green-400' : 
                                      bet.winner_id ? 'text-red-400' : 'text-gray-400'
                                    }`}>
                                      {bet.winner_id === selectedBotForActiveBets.id ? 'Победа' : 
                                       bet.winner_id ? 'Поражение' : 'Ничья'}
                                    </span>
                                  ) : (
                                    <span className="text-text-secondary">—</span>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => {
                  setIsActiveBetsModalOpen(false);
                  setSelectedBotForActiveBets(null);
                  setActiveBetsData(null);
                }}
                className="px-4 py-2 bg-surface-sidebar text-white rounded-lg hover:bg-opacity-80 transition-colors font-roboto"
              >
                Закрыть
              </button>
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
                    <label className="block text-text-secondary text-sm mb-1">Мин. ставка (гемы):</label>
                    <input
                      type="number"
                      min="1"
                      max="10000"
                      step="1"
                      value={editingBot.min_bet_amount}
                      onChange={(e) => setEditingBot({...editingBot, min_bet_amount: parseInt(e.target.value) || 1})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Макс. ставка (гемы):</label>
                    <input
                      type="number"
                      min="1"
                      max="10000"
                      step="1"
                      value={editingBot.max_bet_amount}
                      onChange={(e) => setEditingBot({...editingBot, max_bet_amount: parseInt(e.target.value) || 100})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                </div>
              </div>

              {/* Дополнительные настройки */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Поведение и стратегия</h4>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Стратегия прибыли:</label>
                    <select
                      value={editingBot.profit_strategy || 'balanced'}
                      onChange={(e) => setEditingBot({...editingBot, profit_strategy: e.target.value})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    >
                      <option value="balanced">Сбалансированная</option>
                      <option value="start_profit">Ранняя прибыль</option>
                      <option value="end_loss">Поздние потери</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Поведение бота:</label>
                    <select
                      value={editingBot.bot_behavior || 'balanced'}
                      onChange={(e) => setEditingBot({...editingBot, bot_behavior: e.target.value})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    >
                      <option value="balanced">Сбалансированное</option>
                      <option value="aggressive">Агрессивное</option>
                      <option value="cautious">Осторожное</option>
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Индивидуальный лимит:</label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={editingBot.current_limit || editingBot.cycle_games || 12}
                      onChange={(e) => setEditingBot({...editingBot, current_limit: parseInt(e.target.value) || 12})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Пауза между играми (сек):</label>
                    <input
                      type="number"
                      min="0"
                      max="300"
                      value={editingBot.pause_between_games || 0}
                      onChange={(e) => setEditingBot({...editingBot, pause_between_games: parseInt(e.target.value) || 0})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    />
                  </div>
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

      {/* Модальное окно активных ставок */}

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
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">ID</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Дата</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Время</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Ставка</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Гемы</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Ходы</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Соперник</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Статус</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Результат</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-primary">
                      {cycleData.games.map((game, index) => (
                        <tr key={game.game_id} className="hover:bg-surface-card hover:bg-opacity-50">
                          <td className="px-4 py-3 text-white">{game.game_number || (index + 1)}</td>
                          <td className="px-4 py-3 text-accent-primary text-sm font-mono">{game.game_id || 'N/A'}</td>
                          <td className="px-4 py-3 text-text-secondary text-sm">
                            {new Date(game.completed_at || game.created_at).toLocaleDateString('ru-RU')}
                          </td>
                          <td className="px-4 py-3 text-text-secondary text-sm">
                            {new Date(game.completed_at || game.created_at).toLocaleTimeString('ru-RU')}
                          </td>
                          <td className="px-4 py-3 text-accent-primary font-bold">${game.bet_amount}</td>
                          <td className="px-4 py-3 text-text-secondary text-xs">
                            {Object.entries(game.bet_gems || {}).map(([gem, qty]) => `${gem}: ${qty}`).join(', ') || 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className="text-xs space-y-1">
                              <div>Бот: {game.bot_move || '—'}</div>
                              <div>Соперник: {game.opponent_move || '—'}</div>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-white">{game.opponent || 'N/A'}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs rounded-full font-rajdhani font-bold ${
                              game.status === 'COMPLETED' ? 'bg-green-600 text-white' :
                              game.status === 'ACTIVE' ? 'bg-blue-600 text-white' :
                              game.status === 'WAITING' ? 'bg-yellow-600 text-white' :
                              'bg-gray-600 text-white'
                            }`}>
                              {game.status || 'Unknown'}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs rounded-full font-rajdhani font-bold ${
                              game.result === 'Победа' ? 'bg-green-600 text-white' :
                              game.result === 'Поражение' ? 'bg-red-600 text-white' :
                              game.result === 'Ничья' ? 'bg-yellow-600 text-white' :
                              'bg-gray-600 text-white'
                            }`}>
                              {game.result || '—'}
                            </span>
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

      {/* Модальное окно накопителей прибыли */}
      {isProfitAccumulatorsModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-50 rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b border-border-primary">
              <h3 className="font-rajdhani text-xl font-bold text-white">📊 Накопители прибыли ботов</h3>
              <button
                onClick={() => setIsProfitAccumulatorsModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              {profitAccumulators.length === 0 ? (
                <div className="text-center text-text-secondary py-8">
                  <div className="text-6xl mb-4">📊</div>
                  <h4 className="font-rajdhani text-lg font-bold mb-2">Нет данных</h4>
                  <p>Накопители прибыли пока не найдены</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-surface-sidebar">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Бот</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Цикл</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Игры</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Потрачено</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Заработано</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Прибыль</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Win Rate</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Статус</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Дата создания</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-primary">
                      {profitAccumulators.map((accumulator) => (
                        <tr key={accumulator.id} className="hover:bg-surface-sidebar hover:bg-opacity-50">
                          <td className="px-4 py-3 text-white font-rajdhani">{accumulator.bot_name}</td>
                          <td className="px-4 py-3 text-accent-primary font-bold">#{accumulator.cycle_number}</td>
                          <td className="px-4 py-3 text-white">{accumulator.games_completed}/{accumulator.games_won}</td>
                          <td className="px-4 py-3 text-red-400 font-bold">${accumulator.total_spent.toFixed(2)}</td>
                          <td className="px-4 py-3 text-green-400 font-bold">${accumulator.total_earned.toFixed(2)}</td>
                          <td className={`px-4 py-3 font-bold ${
                            accumulator.profit > 0 ? 'text-green-400' : 
                            accumulator.profit < 0 ? 'text-red-400' : 'text-gray-400'
                          }`}>
                            {accumulator.profit > 0 ? '+' : ''}${accumulator.profit.toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-white">{accumulator.win_rate.toFixed(1)}%</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs rounded-full font-rajdhani font-bold ${
                              accumulator.is_cycle_completed 
                                ? 'bg-green-600 text-white' 
                                : 'bg-yellow-600 text-white'
                            }`}>
                              {accumulator.is_cycle_completed ? 'Завершён' : 'Активный'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-text-secondary text-sm">
                            {new Date(accumulator.created_at).toLocaleString('ru-RU')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Пагинация */}
              {profitPagination.total_pages > 1 && (
                <div className="flex justify-center mt-6">
                  <div className="flex space-x-2">
                    {Array.from({ length: profitPagination.total_pages }, (_, i) => i + 1).map(page => (
                      <button
                        key={page}
                        onClick={() => {/* TODO: Implement pagination */}}
                        className={`px-3 py-1 rounded ${
                          page === profitPagination.current_page
                            ? 'bg-accent-primary text-white'
                            : 'bg-surface-sidebar text-text-secondary hover:text-white'
                        }`}
                      >
                        {page}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end p-6 border-t border-border-primary">
              <button
                onClick={() => setIsProfitAccumulatorsModalOpen(false)}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Модальное окно принудительного завершения цикла */}
      {isForceCompleteModalOpen && selectedBotForForceComplete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="font-russo text-xl text-white mb-4">⏹️ Принудительное завершение цикла</h3>
            
            <div className="space-y-4">
              <div className="bg-surface-sidebar rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-2">Информация о боте</h4>
                <div className="space-y-2 text-sm">
                  <div><strong>Имя:</strong> {selectedBotForForceComplete.name}</div>
                  <div><strong>Текущий цикл:</strong> {selectedBotForForceComplete.current_cycle_games || 0}/{selectedBotForForceComplete.cycle_games || 12} игр</div>
                  <div><strong>Активные ставки:</strong> {selectedBotForForceComplete.active_bets || 0}</div>
                  <div><strong>Сумма цикла:</strong> ${selectedBotForForceComplete.cycle_total_amount || 0}</div>
                </div>
              </div>

              <div className="bg-yellow-900 bg-opacity-20 border border-yellow-500 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <span className="text-yellow-400 text-xl">⚠️</span>
                  <div>
                    <h4 className="font-rajdhani font-bold text-yellow-400">Внимание!</h4>
                    <p className="text-yellow-300 text-sm">
                      Все активные ставки бота будут отменены, и цикл будет завершен принудительно.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  onClick={handleForceCompleteCycle}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-rajdhani font-bold"
                >
                  Завершить цикл
                </button>
                <button
                  onClick={() => {
                    setIsForceCompleteModalOpen(false);
                    setSelectedBotForForceComplete(null);
                  }}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-rajdhani font-bold"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно принудительного завершения цикла */}
      {isForceCompleteModalOpen && selectedBotForForceComplete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-orange-500 border-opacity-50 rounded-lg p-6 max-w-lg w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-orange-400">⚡ Завершить цикл принудительно</h3>
              <button
                onClick={() => setIsForceCompleteModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              {/* Информация о боте */}
              <div className="bg-surface-sidebar rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-2">Информация о боте:</h4>
                <div className="text-text-secondary text-sm space-y-1">
                  <div><strong>Имя:</strong> {selectedBotForForceComplete.name}</div>
                  <div><strong>Текущий цикл:</strong> {selectedBotForForceComplete.current_cycle_games || 0}/12 игр</div>
                  <div><strong>Активные ставки:</strong> {selectedBotForForceComplete.active_bets || 0}</div>
                </div>
              </div>

              {/* Предупреждение */}
              <div className="bg-orange-900 border border-orange-600 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-6 h-6 text-orange-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <div>
                    <h4 className="text-orange-200 font-bold text-sm">Принудительное завершение</h4>
                    <p className="text-orange-300 text-sm mt-1">
                      Текущий цикл бота будет завершён досрочно. Прибыль будет рассчитана и переведена в раздел "Доход от ботов". 
                      Счётчики игр будут сброшены.
                    </p>
                  </div>
                </div>
              </div>

              {/* Кнопки */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={handleForceCompleteCycle}
                  className="px-6 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-rajdhani font-bold transition-colors"
                >
                  ⚡ Завершить цикл
                </button>
                <button
                  onClick={() => {
                    setIsForceCompleteModalOpen(false);
                    setSelectedBotForForceComplete(null);
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

      {/* Модальное окно подтверждения */}
      <ConfirmationModal {...confirmationModal} />
      
      {/* Модальное окно ввода */}
      <InputModal {...inputModal} />
    </div>
  );
};

export default RegularBotsManagement;