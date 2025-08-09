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

  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc'); // 'asc' or 'desc'

  const [selectedBots, setSelectedBots] = useState(new Set());
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc'); // По умолчанию убывающий порядок
    }
  };

  const getSortedBots = (bots) => {
    return [...bots].sort((a, b) => {
      let aValue, bValue;
      
      switch (sortField) {
        case 'name':
          aValue = a.name || '';
          bValue = b.name || '';
          break;
        case 'is_active':
          aValue = a.is_active ? 1 : 0;
          bValue = b.is_active ? 1 : 0;
          break;
        case 'active_bets':
          aValue = a.active_bets || 0;
          bValue = b.active_bets || 0;
          break;
        case 'total_net_profit':
          aValue = a.bot_profit_amount || 0;
          bValue = b.bot_profit_amount || 0;
          break;
        case 'roi':
          aValue = (a.bot_profit_percent !== undefined ? a.bot_profit_percent : 0);
          bValue = (b.bot_profit_percent !== undefined ? b.bot_profit_percent : 0);
          break;
        case 'cycle_games':
          aValue = a.cycle_games || 0;
          bValue = b.cycle_games || 0;
          break;
        case 'cycle_total_amount':
          aValue = a.cycle_total_amount || 0;
          bValue = b.cycle_total_amount || 0;
          break;
        case 'created_at':
        default:
          aValue = new Date(a.created_at || 0);
          bValue = new Date(b.created_at || 0);
          break;
      }
      
      if (sortDirection === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });
  };

  const [cycleHistoryData, setCycleHistoryData] = useState([]);
  const [selectedBotForCycleHistory, setSelectedBotForCycleHistory] = useState(null);
  const [isCycleHistoryModalOpen, setIsCycleHistoryModalOpen] = useState(false);

  // States for cycle details modal
  const [selectedCycleForDetails, setSelectedCycleForDetails] = useState(null);
  const [isCycleDetailsModalOpen, setIsCycleDetailsModalOpen] = useState(false);
  const [cycleDetailsData, setCycleDetailsData] = useState(null);

  // Функция для открытия модального окна истории циклов
  const handleCycleHistoryModal = async (bot) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/${bot.id}/cycle-history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSelectedBotForCycleHistory(bot);
      setCycleHistoryData(response.data.games || []);
      setIsCycleHistoryModalOpen(true);
    } catch (error) {
      console.error('Ошибка загрузки истории циклов:', error);
      showErrorRU('Ошибка при загрузке истории циклов');
    }
  };

  // Функция для открытия модального окна деталей цикла
  const handleCycleDetailsModal = async (cycle, bot) => {
    try {
      const token = localStorage.getItem('token');
      // Use mock data for now since backend doesn't have real cycle details yet
      const mockCycleDetails = {
        id: cycle.id,
        bot_name: bot.name,
        cycle_number: cycle.cycle_number,
        completed_at: cycle.completed_at,
        duration: cycle.duration,
        total_games: cycle.total_games || cycle.games_played || 12,
        wins: cycle.wins || 7,
        losses: cycle.losses || 4, 
        draws: cycle.draws || 1,
        total_bet: cycle.total_bet || cycle.total_wagered || 150.0,
        total_winnings: cycle.total_winnings || 280.0,
        profit: cycle.profit || 130.0,
        win_percentage: cycle.wins ? ((cycle.wins / (cycle.wins + cycle.losses + cycle.draws)) * 100).toFixed(1) : '58.3',
        // Mock individual bets data - in real implementation this would come from API
        bets: Array.from({ length: cycle.total_games || 12 }, (_, index) => ({
          id: `bet_${cycle.id}_${index + 1}`,
          game_number: index + 1,
          bet_amount: Math.floor(Math.random() * 40) + 10, // Random bet between 10-50
          result: index < (cycle.wins || 7) ? 'win' : 
                 index < (cycle.wins || 7) + (cycle.losses || 4) ? 'loss' : 'draw',
          payout: index < (cycle.wins || 7) ? (Math.floor(Math.random() * 40) + 10) * 1.94 : 0,
          created_at: new Date(Date.now() - (12 - index) * 3600000).toISOString(), // Hours ago
          move: ['rock', 'paper', 'scissors'][Math.floor(Math.random() * 3)],
          opponent_move: ['rock', 'paper', 'scissors'][Math.floor(Math.random() * 3)]
        }))
      };

      setSelectedCycleForDetails(cycle);
      setCycleDetailsData(mockCycleDetails);
      setIsCycleDetailsModalOpen(true);
    } catch (error) {
      console.error('Ошибка загрузки деталей цикла:', error);
      showErrorRU('Ошибка при загрузке деталей цикла');
    }
  };

  const [selectAll, setSelectAll] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);

  // Form states for creating bot with new extended system
  // Функции для работы с localStorage
  const savePercentagesToStorage = (wins, losses, draws) => {
    localStorage.setItem('botPercentages', JSON.stringify({
      wins_percentage: wins,
      losses_percentage: losses,
      draws_percentage: draws,
      saved_at: Date.now()
    }));
  };

  const getPercentagesFromStorage = () => {
    try {
      const saved = localStorage.getItem('botPercentages');
      if (saved) {
        const parsed = JSON.parse(saved);
        return {
          wins_percentage: parsed.wins_percentage || 35,
          losses_percentage: parsed.losses_percentage || 35,
          draws_percentage: parsed.draws_percentage || 30
        };
      }
    } catch (error) {
      console.error('Ошибка загрузки сохраненных процентов:', error);
    }
    return {
      wins_percentage: 35,
      losses_percentage: 35, 
      draws_percentage: 30
    };
  };

  const [botForm, setBotForm] = useState(() => {
    const savedPercentages = getPercentagesFromStorage();
    return {
      name: '',
      
      // НОВАЯ ФОРМУЛА 2.0: Обновленные диапазоны и параметры
      min_bet_amount: 1.0,   // 1-100
      max_bet_amount: 100.0, // 1-100
      
      // УБИРАЕМ: win_percentage (старая логика)
      // ДОБАВЛЯЕМ: Баланс игр
      wins_count: 6,    // Количество побед в цикле
      losses_count: 6,  // Количество поражений в цикле  
      draws_count: 4,   // Количество ничьих в цикле
      
      // Процент исходов игр (новые значения по умолчанию)
      wins_percentage: savedPercentages.wins_percentage || 44.0,
      losses_percentage: savedPercentages.losses_percentage || 36.0,
      draws_percentage: savedPercentages.draws_percentage || 20.0,
      
      cycle_games: 16, // НОВОЕ: 16 игр по умолчанию (было 12)
      pause_between_cycles: 5, // 1-300 секунд
      pause_on_draw: 5, // 1-60 секунд
      
      creation_mode: 'queue-based',
      profit_strategy: 'balanced',
      
      cycle_total_amount: 0, // calculated automatically
      active_pool_amount: 0, // НОВОЕ: активный пул для отображения
      roi_active: 0.0        // НОВОЕ: ROI_active для превью
    };
  });

  // НОВАЯ ФОРМУЛА 2.0: Расчет суммы цикла и ROI для превью
  const calculateCycleAmounts = () => {
    if (!botForm.min_bet_amount || !botForm.max_bet_amount || !botForm.cycle_games) {
      return { total: 0, active_pool: 0, roi_active: 0 };
    }
    
    const min_bet = parseFloat(botForm.min_bet_amount);
    const max_bet = parseFloat(botForm.max_bet_amount);
    const games = parseInt(botForm.cycle_games);
    
    // 1. Имитируем равномерное распределение ставок для общей суммы
    let estimatedTotal = 0;
    const smallBetsCount = Math.max(1, Math.round(games * 0.25));
    const mediumBetsCount = Math.round(games * 0.5);
    const largeBetsCount = games - smallBetsCount - mediumBetsCount;
    
    const smallAvg = min_bet + (max_bet - min_bet) * 0.15;
    const mediumAvg = min_bet + (max_bet - min_bet) * 0.5;
    const largeAvg = min_bet + (max_bet - min_bet) * 0.85;
    
    estimatedTotal = (smallBetsCount * smallAvg) + (mediumBetsCount * mediumAvg) + (largeBetsCount * largeAvg);
    
    // 2. Рассчитываем суммы по процентам исходов
    const winsSum = Math.round(estimatedTotal * botForm.wins_percentage / 100);
    const lossesSum = Math.round(estimatedTotal * botForm.losses_percentage / 100);  
    const drawsSum = Math.round(estimatedTotal * botForm.draws_percentage / 100);
    
    // 3. Активный пул (база для ROI)
    const activePool = winsSum + lossesSum;
    const profit = winsSum - lossesSum;
    const roiActive = activePool > 0 ? ((profit / activePool) * 100) : 0;
    
    return {
      total: Math.round(estimatedTotal),
      active_pool: activePool,
      roi_active: Math.round(roiActive * 100) / 100, // Округляем до 2 знаков
      wins_sum: winsSum,
      losses_sum: lossesSum,
      draws_sum: drawsSum,
      profit: profit
    };
  };
  
  // Обратная совместимость
  const calculateCycleTotalAmount = () => {
    return calculateCycleAmounts().total;
  };
  
  // НОВАЯ ФУНКЦИЯ: Автосвязь баланса игр
  const updateBalanceGames = (newCycleGames, autoUpdate = true) => {
    if (!autoUpdate) return;
    const { W, L, D } = recalcCountsFromPercents(
      newCycleGames,
      botForm.wins_percentage,
      botForm.losses_percentage,
      botForm.draws_percentage
    );
    setBotForm(prev => ({
      ...prev,
      cycle_games: newCycleGames,
      wins_count: W,
      losses_count: L,
      draws_count: D
    }));
  };
  
  // Валидация процентов исходов (должны быть = 100%)
  const validatePercentages = () => {
    const total = botForm.wins_percentage + botForm.losses_percentage + botForm.draws_percentage;
    return Math.abs(total - 100) < 0.1; // Допускаем погрешность 0.1%
  };
  
  // Валидация баланса игр (должны совпадать с cycle_games)
  const validateBalanceGames = () => {
    const total = botForm.wins_count + botForm.losses_count + botForm.draws_count;
    return total === botForm.cycle_games;
  };
  
  // НОВАЯ ЛОГИКА: Пресеты процентов исходов
  const [customPresets, setCustomPresets] = useState([]);
  const [showPresetModal, setShowPresetModal] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');
  
  const defaultPresets = [
    { name: "Custom", wins: null, losses: null, draws: null, custom: true },
    { name: "ROI 2%", wins: 39.3, losses: 37.7, draws: 23.0 },
    { name: "ROI 3%", wins: 40.7, losses: 38.3, draws: 21.0 },
    { name: "ROI 4%", wins: 41.6, losses: 38.4, draws: 20.0 },
    { name: "ROI 5%", wins: 41.5, losses: 37.5, draws: 21.0 },
    { name: "ROI 6%", wins: 41.9, losses: 37.1, draws: 21.0 },
    { name: "ROI 7%", wins: 38.0, losses: 33.0, draws: 29.0 },
    { name: "ROI 8%", wins: 38.9, losses: 33.1, draws: 28.0 },
    { name: "ROI 9%", wins: 42.0, losses: 35.0, draws: 23.0 },
    { name: "ROI 10%", wins: 38.5, losses: 31.5, draws: 30.0 },
    { name: "ROI 11%", wins: 41.6, losses: 33.4, draws: 25.0 },
    { name: "ROI 12%", wins: 39.8, losses: 31.2, draws: 29.0 },
    { name: "ROI 13%", wins: 44.6, losses: 34.4, draws: 21.0 },
    { name: "ROI 14%", wins: 41.6, losses: 31.4, draws: 27.0 },
    { name: "ROI 15%", wins: 46.0, losses: 34.0, draws: 20.0 },
    { name: "ROI 20%", wins: 47.4, losses: 31.6, draws: 21.0 }
  ];

  const [selectedPreset, setSelectedPreset] = useState("Custom");

  const applyPreset = (preset) => {
    if (!preset || preset.custom) {
      setSelectedPreset("Custom");
      return;
    }
    setSelectedPreset(preset.name);
    setBotForm(prev => ({
      ...prev,
      wins_percentage: Number(preset.wins.toFixed(1)),
      losses_percentage: Number(preset.losses.toFixed(1)),
      draws_percentage: Number(preset.draws.toFixed(1))
    }));
  };
  
  const saveCustomPreset = () => {
    if (!newPresetName.trim()) return;
    
    const newPreset = {
      name: newPresetName.trim(),
      wins: botForm.wins_percentage,
      losses: botForm.losses_percentage, 
      draws: botForm.draws_percentage,
      custom: true
    };
    
    setCustomPresets(prev => [...prev, newPreset]);
    setNewPresetName('');
    setShowPresetModal(false);
  };

  // Пересчет counts по процентам (Largest Remainder)
  const recalcCountsFromPercents = (games, winsP, lossesP, drawsP) => {
    const N = Math.max(1, parseInt(games) || 1);
    const w = (winsP / 100) * N;
    const l = (lossesP / 100) * N;
    const d = (drawsP / 100) * N;
    let W = Math.floor(w), L = Math.floor(l), D = Math.floor(d);
    let R = N - (W + L + D);
    const remainders = [
      { key: 'W', rem: w - W },
      { key: 'L', rem: l - L },
      { key: 'D', rem: d - D }
    ].sort((a, b) => b.rem - a.rem);
    let i = 0;
    while (R > 0) {
      const k = remainders[i % remainders.length].key;
      if (k === 'W') W += 1; else if (k === 'L') L += 1; else D += 1;
      R -= 1; i += 1;
    }
    // гарантируем неотрицательность и точную сумму
    W = Math.max(0, W); L = Math.max(0, L); D = Math.max(0, D);
    const total = W + L + D;
    if (total !== N) {
      const diff = N - total;
      if (diff !== 0) {
        if (W >= L && W >= D) W += diff; else if (L >= W && L >= D) L += diff; else D += diff;
      }
    }
    return { W, L, D };
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
      setBotsList(botsData); // Больше не сортируем здесь, используем getSortedBots
      
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
      errors.push('Процент выигрыша должен быть от 0 до 100');
    }
    
    // Валидация процентов исходов игр
    if (formData.wins_percentage < 0 || formData.wins_percentage > 100) {
      errors.push('Процент побед должен быть от 0 до 100');
    }
    
    if (formData.losses_percentage < 0 || formData.losses_percentage > 100) {
      errors.push('Процент поражений должен быть от 0 до 100');
    }
    
    if (formData.draws_percentage < 0 || formData.draws_percentage > 100) {
      errors.push('Процент ничьих должен быть от 0 до 100');
    }
    
    // Проверка что сумма процентов равна 100%
    const totalPercentage = (formData.wins_percentage || 0) + (formData.losses_percentage || 0) + (formData.draws_percentage || 0);
    if (Math.abs(totalPercentage - 100) > 0.1) { // Допускаем небольшую погрешность
      errors.push(`Сумма процентов исходов должна быть 100% (сейчас ${totalPercentage}%)`);
    }
    
    if (formData.cycle_games < 4 || formData.cycle_games > 100) {
      errors.push('Количество игр в цикле должно быть от 4 до 100');
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
        wins_count: botForm.wins_count,
        losses_count: botForm.losses_count,
        draws_count: botForm.draws_count,
        wins_percentage: botForm.wins_percentage,
        losses_percentage: botForm.losses_percentage,
        draws_percentage: botForm.draws_percentage,
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
      
      setBotForm(() => {
        const savedPercentages = getPercentagesFromStorage();
        return {
          name: '',
          min_bet_amount: 1.0,
          max_bet_amount: 50.0,
          win_percentage: 55.0,
          wins_percentage: savedPercentages.wins_percentage,
          losses_percentage: savedPercentages.losses_percentage,
          draws_percentage: savedPercentages.draws_percentage,
          cycle_games: 12,
          pause_between_cycles: 5,
          pause_on_draw: 5,
          creation_mode: 'queue-based',
          profit_strategy: 'balanced',
          cycle_total_amount: 0
        };
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
      
      const b = response.data.bot || {};
      
      setBotForm({
        name: b.name || '',
        min_bet_amount: b.min_bet_amount ?? 1.0,
        max_bet_amount: b.max_bet_amount ?? 50.0,
        win_percentage: b.win_percentage ?? (b.win_rate ? b.win_rate * 100 : 55.0),
        // Новая система: подтягиваем баланс и проценты из бота
        wins_count: b.wins_count ?? 6,
        losses_count: b.losses_count ?? 6,
        draws_count: b.draws_count ?? 4,
        wins_percentage: b.wins_percentage ?? 44.0,
        losses_percentage: b.losses_percentage ?? 36.0,
        draws_percentage: b.draws_percentage ?? 20.0,
        cycle_games: b.cycle_games ?? 12,
        pause_between_cycles: b.pause_between_cycles ?? 5,
        pause_on_draw: b.pause_on_draw ?? 1,
        creation_mode: b.creation_mode ?? 'queue-based',
        profit_strategy: b.profit_strategy ?? 'balanced',
        cycle_total_amount: b.cycle_total_amount ?? 0
      });
      setSelectedPreset('Custom');
      validateExtendedFormInRealTime({
        name: b.name || '',
        min_bet_amount: b.min_bet_amount ?? 1.0,
        max_bet_amount: b.max_bet_amount ?? 50.0,
        win_percentage: b.win_percentage ?? (b.win_rate ? b.win_rate * 100 : 55.0),
        wins_count: b.wins_count ?? 6,
        losses_count: b.losses_count ?? 6,
        draws_count: b.draws_count ?? 4,
        wins_percentage: b.wins_percentage ?? 44.0,
        losses_percentage: b.losses_percentage ?? 36.0,
        draws_percentage: b.draws_percentage ?? 20.0,
        cycle_games: b.cycle_games ?? 12,
        pause_between_cycles: b.pause_between_cycles ?? 5,
        pause_on_draw: b.pause_on_draw ?? 1,
        creation_mode: b.creation_mode ?? 'queue-based',
        profit_strategy: b.profit_strategy ?? 'balanced'
      });
      
      setEditingBot(response.data.bot);
      setIsEditModalOpen(true);
    } catch (error) {
      console.error('Ошибка загрузки данных бота:', error);
      showErrorRU('Ошибка при загрузке данных бота');
    }
  };

  const updateIndividualBotSettings = async () => {
    try {
      const validation = validateExtendedBotForm(botForm);
      if (!validation.isValid) {
        setExtendedValidation(validation);
        showErrorRU(`Ошибка валидации: ${validation.errors.join(', ')}`);
        return;
      }

      const token = localStorage.getItem('token');
      const botData = {
        name: botForm.name,
        min_bet_amount: botForm.min_bet_amount,
        max_bet_amount: botForm.max_bet_amount,
        wins_count: botForm.wins_count,
        losses_count: botForm.losses_count,
        draws_count: botForm.draws_count,
        wins_percentage: botForm.wins_percentage,
        losses_percentage: botForm.losses_percentage,
        draws_percentage: botForm.draws_percentage,
        cycle_games: botForm.cycle_games,
        pause_between_cycles: botForm.pause_between_cycles,
        pause_on_draw: botForm.pause_on_draw,
        creation_mode: botForm.creation_mode,
        profit_strategy: botForm.profit_strategy
      };

      const response = await axios.put(`${API}/admin/bots/${editingBot.id}`, botData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      showSuccessRU(response.data.message || 'Настройки бота успешно обновлены');
      
      // Обновляем editingBot с новыми данными для корректного отображения
      const updatedBot = {
        ...editingBot,
        ...botForm,
        updated_at: new Date().toISOString()
      };
      setEditingBot(updatedBot);
      
      setIsEditModalOpen(false);
      setEditingBot(null);
      await fetchBotsList();
    } catch (error) {
      console.error('Ошибка обновления настроек бота:', error);
      showErrorRU(error.response?.data?.detail || 'Ошибка при обновлении настроек бота');
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

  const handleCycleBetsDetails = async (bot) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/${bot.id}/cycle-bets`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = response.data || {};
      // Собираем удобные для отображения поля
      const details = {
        bot_name: data.bot_name || bot.name,
        cycle_length: data.cycle_length,
        exact_cycle_total: data.exact_cycle_total,
        sums: data.sums || { wins_sum: 0, losses_sum: 0, draws_sum: 0, total_sum: 0, active_pool: 0, profit: 0, roi_active: 0 },
        counts: data.counts || { wins_count: 0, losses_count: 0, draws_count: 0, total_count: 0 },
        breakdown: data.breakdown || { wins: [], losses: [], draws: [] },
        bets: data.bets || []
      };

      setCycleDetailsData(details);
      setIsCycleDetailsModalOpen(true);
    } catch (error) {
      console.error('Ошибка загрузки деталей цикла:', error);
      showErrorRU('Ошибка при загрузке деталей цикла');
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
      await axios.put(`${API}/admin/bots/${bot.id}/win-percentage`, {
        win_percentage: newPercentage
      }, {
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
      const currentPause = bot.pause_between_cycles || 5;
      const userInput = window.prompt(
        `Введите новую паузу между циклами для бота ${bot.name || `Bot #${bot.id.substring(0, 3)}`}:\n\nТекущая: ${currentPause} секунд\n(Допустимые значения: 1-3600)`,
        currentPause
      );

      if (userInput === null) return; // Пользователь отменил

      const newPause = parseInt(userInput);
      if (isNaN(newPause) || newPause < 1 || newPause > 3600) {
        showErrorRU('Пауза должна быть числом от 1 до 3600 секунд');
        return;
      }

      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/bots/${bot.id}/pause-settings`, {
        pause_between_cycles: newPause
      }, {
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
                <th 
                  className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom cursor-pointer hover:bg-surface-card"
                  onClick={() => handleSort('name')}
                >
                  <div className="flex items-center">
                    Имя
                    {sortField === 'name' && (
                      <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom cursor-pointer hover:bg-surface-card"
                  onClick={() => handleSort('is_active')}
                >
                  <div className="flex items-center">
                    Статус
                    {sortField === 'is_active' && (
                      <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom cursor-pointer hover:bg-surface-card"
                  onClick={() => handleSort('active_bets')}
                >
                  <div className="flex items-center">
                    Ставки
                    {sortField === 'active_bets' && (
                      <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom cursor-pointer hover:bg-surface-card"
                  onClick={() => handleSort('total_net_profit')}
                >
                  <div className="flex items-center">
                    Статистика
                    {sortField === 'total_net_profit' && (
                      <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom cursor-pointer hover:bg-surface-card"
                  onClick={() => handleSort('roi')}
                >
                  <div className="flex items-center">
                    ROI
                    {sortField === 'roi' && (
                      <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Лимиты
                </th>
                <th 
                  className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom cursor-pointer hover:bg-surface-card"
                  onClick={() => handleSort('cycle_games')}
                >
                  <div className="flex items-center">
                    Цикл
                    {sortField === 'cycle_games' && (
                      <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Активность бота
                </th>
                <th 
                  className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom cursor-pointer hover:bg-surface-card"
                  onClick={() => handleSort('cycle_total_amount')}
                >
                  <div className="flex items-center">
                    Сумма цикла
                    {sortField === 'cycle_total_amount' && (
                      <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Стратегия
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Пауза
                </th>
                <th 
                  className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom cursor-pointer hover:bg-surface-card"
                  onClick={() => handleSort('created_at')}
                >
                  <div className="flex items-center">
                    Регистрация
                    {sortField === 'created_at' && (
                      <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Действия
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-primary">
              {botsList.length === 0 ? (
                <tr>
                  <td colSpan="15" className="px-4 py-8 text-center text-text-secondary">
                    Нет ботов для отображения
                  </td>
                </tr>
              ) : (
                getSortedBots(botsList).map((bot, index) => (
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
                        <div>W/L/D: {(bot.current_cycle_wins || 0)}/{(bot.current_cycle_losses || 0)}/{(bot.current_cycle_draws || 0)}</div>
                        <div className="text-green-400">Прибыль: ${Math.round(bot.current_cycle_profit || 0)}</div>
                        <button
                          onClick={() => handleCycleHistoryModal(bot)}
                          className="text-blue-400 hover:text-blue-300 cursor-pointer underline"
                          title="Показать историю циклов"
                        >
                          Чистая: ${Math.round(bot.total_net_profit || bot.bot_profit_amount || 0)}
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      {(() => {
                        // Фактический ROI (как есть с бэка)
                        const roiActual = (bot.bot_profit_percent !== undefined ? bot.bot_profit_percent : 0);
                        const actualColor = roiActual < 0 ? 'text-red-400' : 'text-orange-400';
                        
                        // Плановый ROI: всегда показываем нижней строкой
                        // Нижняя строка: индивидуальный плановый ROI по конфигурации бота
                        // Берём проценты из бота: приоритет wins_percentage/losses_percentage, иначе используем win_percentage и выводим losses = 100 - win - draws
                        const roiPlanned = (() => {
                          const hasWinsPct = bot.wins_percentage !== undefined && bot.wins_percentage !== null;
                          const hasLossesPct = bot.losses_percentage !== undefined && bot.losses_percentage !== null;
                          const hasDrawsPct = bot.draws_percentage !== undefined && bot.draws_percentage !== null;
                          const winPct = hasWinsPct ? Number(bot.wins_percentage) : (bot.win_percentage !== undefined ? Number(bot.win_percentage) : 55.0);
                          const drawPct = hasDrawsPct ? Number(bot.draws_percentage) : 20.0;
                          const lossPct = hasLossesPct ? Number(bot.losses_percentage) : Math.max(0, 100.0 - winPct - drawPct);
                          const denom = winPct + lossPct;
                          if (denom <= 0) return 0.0;
                          const roi = ((winPct - lossPct) / denom) * 100.0;
                          return roi;
                        })();
                        
                        return (
                          <div className="flex flex-col items-center justify-center leading-tight">
                            <span className={`${actualColor} font-roboto text-sm font-bold`} title="Фактический ROI">
                              {Number(roiActual).toFixed(2)}%
                            </span>
                            <span className={`text-xs text-gray-400`} title="Плановый ROI">
                              {Number(roiPlanned).toFixed(2)}%
                            </span>
                          </div>
                        );
                      })()}

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
                      <div className="text-accent-primary font-roboto text-sm">
                        {bot.cycle_total_info ? (
                          <div title={`Общая сумма: ${bot.cycle_total_info.total_sum}, Ничьи: ${bot.cycle_total_info.draws_sum}`}>
                            <span className="font-bold">{bot.cycle_total_info.active_pool}</span>
                            <div className="text-xs text-gray-400">
                              (из {bot.cycle_total_info.total_sum}, ничьи: {bot.cycle_total_info.draws_sum})
                            </div>
                          </div>
                        ) : (
                          <span className="font-bold">{bot.cycle_total_amount || 0}</span>
                        )}
                        <div>
                          <button
                            onClick={() => handleCycleBetsDetails(bot)}
                            className="text-blue-400 hover:text-blue-300 underline text-xs mt-1"
                            title="Показать детали цикла (W/L/D и ROI)"
                          >
                            Детали цикла
                          </button>
                        </div>
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
                          {bot.pause_between_cycles ? `${bot.pause_between_cycles}с` : '5с'}
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
      {/* Модалка деталей цикла (W/L/D, суммы, ROI) */}
      {isCycleDetailsModalOpen && cycleDetailsData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-3xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-white">
                Детали цикла: {cycleDetailsData.bot_name}
              </h3>
              <button onClick={() => setIsCycleDetailsModalOpen(false)} className="text-gray-400 hover:text-white">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs">Длина цикла</div>
                <div className="text-white text-lg font-bold">{cycleDetailsData.cycle_length}</div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs">Теоретическая сумма</div>
                <div className="text-white text-lg font-bold">{cycleDetailsData.exact_cycle_total}</div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs">ROI</div>
                <div className="text-white text-lg font-bold">{Number(cycleDetailsData.sums?.roi_active || 0).toFixed(2)}%</div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs">Победы (сумма)</div>
                <div className="text-green-400 text-lg font-bold">{cycleDetailsData.sums?.wins_sum || 0}</div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs">Поражения (сумма)</div>
                <div className="text-red-400 text-lg font-bold">{cycleDetailsData.sums?.losses_sum || 0}</div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs">Ничьи (сумма)</div>
                <div className="text-yellow-400 text-lg font-bold">{cycleDetailsData.sums?.draws_sum || 0}</div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs">Общая сумма</div>
                <div className="text-white text-lg font-bold">{cycleDetailsData.sums?.total_sum || 0}</div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs mb-2">Ставки Побед</div>
                <div className="text-white text-sm break-words">{(cycleDetailsData.breakdown?.wins || []).join(', ') || '—'}</div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs mb-2">Ставки Поражений</div>
                <div className="text-white text-sm break-words">{(cycleDetailsData.breakdown?.losses || []).join(', ') || '—'}</div>
              </div>
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-xs mb-2">Ставки Ничьих</div>
                <div className="text-white text-sm break-words">{(cycleDetailsData.breakdown?.draws || []).join(', ') || '—'}</div>
              </div>
            </div>
          </div>
        </div>
      )}

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

              {/* НОВАЯ ЛОГИКА: Баланс игр */}
              <div className="border border-blue-500 bg-blue-900 bg-opacity-20 rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-blue-400 mb-3">⚖️ Баланс игр</h4>
                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Победы:</label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={botForm.wins_count}
                      onChange={(e) => {
                        const wins = parseInt(e.target.value) || 6;
                        const newForm = {...botForm, wins_count: wins};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Поражения:</label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={botForm.losses_count}
                      onChange={(e) => {
                        const losses = parseInt(e.target.value) || 6;
                        const newForm = {...botForm, losses_count: losses};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Ничьи:</label>
                    <input
                      type="number"
                      min="0"
                      max="20"
                      value={botForm.draws_count}
                      onChange={(e) => {
                        const draws = parseInt(e.target.value) || 4;
                        const newForm = {...botForm, draws_count: draws};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                </div>
                <div className="text-xs text-text-secondary">
                  Количество каждого типа игр в цикле. Сумма: {botForm.wins_count + botForm.losses_count + botForm.draws_count} 
                  {(botForm.wins_count + botForm.losses_count + botForm.draws_count) === botForm.cycle_games ? 
                    <span className="text-green-400 ml-1">✓ Совпадает с "Игр в цикле"</span> : 
                    <span className="text-red-400 ml-1">⚠ Не совпадает с "Игр в цикле" ({botForm.cycle_games})</span>
                  }
                </div>
              </div>

              {/* Новая секция: Процент исходов игр */}
              <div className="border border-green-500 bg-green-900 bg-opacity-20 rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-green-400 mb-3">Процент исходов игр</h4>
                <div className="grid grid-cols-4 gap-4 mb-3">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Пресет ROI:</label>
                    <select
                      value={selectedPreset}
                      onChange={(e) => {
                        const preset = defaultPresets.find(p => p.name === e.target.value);
                        applyPreset(preset);
                        // После смены пресета пересчитаем counts из процентов
                        const { W, L, D } = recalcCountsFromPercents(
                          botForm.cycle_games,
                          preset && !preset.custom ? preset.wins : botForm.wins_percentage,
                          preset && !preset.custom ? preset.losses : botForm.losses_percentage,
                          preset && !preset.custom ? preset.draws : botForm.draws_percentage
                        );
                        setBotForm(prev => ({ ...prev, wins_count: W, losses_count: L, draws_count: D }));
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    >
                      {defaultPresets.map(preset => (
                        <option key={preset.name} value={preset.name}>{preset.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Победы (%):</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={botForm.wins_percentage}
                      onChange={(e) => {
                        const wins = parseFloat(e.target.value) || 0;
                        const newForm = { ...botForm, wins_percentage: wins };
                        setSelectedPreset("Custom");
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                        savePercentagesToStorage(wins, botForm.losses_percentage, botForm.draws_percentage);
                        const { W, L, D } = recalcCountsFromPercents(botForm.cycle_games, wins, botForm.losses_percentage, botForm.draws_percentage);
                        setBotForm(prev => ({ ...prev, wins_count: W, losses_count: L, draws_count: D }));
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Поражения (%):</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={botForm.losses_percentage}
                      onChange={(e) => {
                        const losses = parseFloat(e.target.value) || 0;
                        const newForm = { ...botForm, losses_percentage: losses };
                        setSelectedPreset("Custom");
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                        savePercentagesToStorage(botForm.wins_percentage, losses, botForm.draws_percentage);
                        const { W, L, D } = recalcCountsFromPercents(botForm.cycle_games, botForm.wins_percentage, losses, botForm.draws_percentage);
                        setBotForm(prev => ({ ...prev, wins_count: W, losses_count: L, draws_count: D }));
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Ничьи (%):</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={botForm.draws_percentage}
                      onChange={(e) => {
                        const draws = parseFloat(e.target.value) || 0;
                        const newForm = { ...botForm, draws_percentage: draws };
                        setSelectedPreset("Custom");
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                        savePercentagesToStorage(botForm.wins_percentage, botForm.losses_percentage, draws);
                        const { W, L, D } = recalcCountsFromPercents(botForm.cycle_games, botForm.wins_percentage, botForm.losses_percentage, draws);
                        setBotForm(prev => ({ ...prev, wins_count: W, losses_count: L, draws_count: D }));
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                </div>
                <div className="text-xs text-text-secondary">
                  Сумма должна быть 100%. Из {botForm.cycle_games} игр: {Math.round(botForm.cycle_games * botForm.wins_percentage / 100)} побед, {Math.round(botForm.cycle_games * botForm.losses_percentage / 100)} поражений. Ничьи ({Math.round(botForm.cycle_games * botForm.draws_percentage / 100)} дополнительно) не засчитываются в цикл.
                </div>
              </div>

              {/* Объединенный блок: Циклы и Настройки таймингов */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Циклы и Настройки таймингов</h4>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Игр в цикле */}
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Игр в цикле:</label>
                    <input
                      type="number"
                      min="1"
                      max="66"
                      value={botForm.cycle_games}
                      onChange={(e) => {
                        const newValue = Math.min(100, Math.max(4, parseInt(e.target.value) || 12));
                        updateBalanceGames(newValue, true);
                        const newForm = { ...botForm, cycle_games: newValue };
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                    <div className="text-xs text-text-secondary mt-1">
                      Количество игр в одном цикле (1-66)
                    </div>
                  </div>

                  {/* Пауза между циклами */}
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Пауза между циклами:</label>
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

                  {/* Пауза при ничье */}
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

                {/* Предупреждения и подсказки (сохранены) */}
                {(() => {
                  const preview = calculateCycleAmounts();
                  const activePoolShare = preview.total > 0 ? Math.round(((preview.active_pool / preview.total) * 100)) : 0;
                  const warnings = [];
                  if (activePoolShare < 65) warnings.push(`⚠️ Активный пул слишком мал (${activePoolShare}%). Рекомендуется ≥ 65%.`);
                  if (preview.roi_active < 2 || preview.roi_active > 20) warnings.push(`⚠️ ROI_active (${preview.roi_active}%) вне рекомендуемых пределов [2%, 20%].`);
                  return warnings.length > 0 ? (
                    <div className="mt-3 border border-yellow-500 bg-yellow-900 bg-opacity-20 rounded-lg p-3 text-yellow-200 text-sm space-y-1">
                      {warnings.map((w, idx) => (<div key={idx}>{w}</div>))}
                    </div>
                  ) : null;
                })()}
              </div>

              {/* НОВАЯ ЛОГИКА: Превью ROI расчетов */}
              <div className="border border-purple-500 bg-purple-900 bg-opacity-20 rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-purple-400 mb-3">📊 Превью ROI расчетов</h4>
                {(() => {
                  const preview = calculateCycleAmounts();
                  return (
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-text-secondary">Общая сумма цикла:</div>
                        <div className="text-white font-bold">{preview.total}</div>
                      </div>
                      <div>
                        <div className="text-text-secondary">Активный пул:</div>
                        <div className="text-purple-300 font-bold">{preview.active_pool}</div>
                      </div>
                      <div>
                        <div className="text-text-secondary">Прибыль:</div>
                        <div className={`font-bold ${preview.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {preview.profit}
                        </div>
                      </div>
                      <div>
                        <div className="text-text-secondary">ROI_active:</div>
                        <div className={`font-bold text-lg ${preview.roi_active >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {preview.roi_active}%
                        </div>
                      </div>
                    </div>
                  );
                })()}
                <div className="text-xs text-purple-200 mt-3 border-t border-purple-700 pt-2">
                  <div><strong>Формула ROI:</strong> (Прибыль ÷ Активный пул) × 100%</div>
                  <div><strong>Активный пул:</strong> Сумма побед + Сумма поражений (ничьи не участвуют в ROI)</div>
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
                      activeBetsData.bets.reduce((sum, bet) => sum + (parseInt(bet.bet_amount || bet.amount || 0, 10)), 0) : 
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

            <div className="space-y-6">
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

              {/* Баланс игр */}
              <div className="border border-blue-500 bg-blue-900 bg-opacity-20 rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-blue-400 mb-3">⚖️ Баланс игр</h4>
                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Победы:</label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={botForm.wins_count}
                      onChange={(e) => {
                        const wins = parseInt(e.target.value) || 6;
                        const newForm = {...botForm, wins_count: wins};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Поражения:</label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={botForm.losses_count}
                      onChange={(e) => {
                        const losses = parseInt(e.target.value) || 6;
                        const newForm = {...botForm, losses_count: losses};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Ничьи:</label>
                    <input
                      type="number"
                      min="0"
                      max="20"
                      value={botForm.draws_count}
                      onChange={(e) => {
                        const draws = parseInt(e.target.value) || 4;
                        const newForm = {...botForm, draws_count: draws};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                </div>
                <div className="text-xs text-text-secondary">
                  Количество каждого типа игр в цикле. Сумма: {botForm.wins_count + botForm.losses_count + botForm.draws_count} 
                  {(botForm.wins_count + botForm.losses_count + botForm.draws_count) === botForm.cycle_games ? 
                    <span className="text-green-400 ml-1">✓ Совпадает с "Игр в цикле"</span> : 
                    <span className="text-red-400 ml-1">⚠ Не совпадает с "Игр в цикле" ({botForm.cycle_games})</span>
                  }
                </div>
              </div>

              {/* Процент исходов игр */}
              <div className="border border-green-500 bg-green-900 bg-opacity-20 rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-green-400 mb-3">Процент исходов игр</h4>
                <div className="grid grid-cols-4 gap-4 mb-3">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Пресет ROI:</label>
                    <select
                      value={selectedPreset}
                      onChange={(e) => {
                        const preset = defaultPresets.find(p => p.name === e.target.value);
                        applyPreset(preset);
                        const { W, L, D } = recalcCountsFromPercents(
                          botForm.cycle_games,
                          preset && !preset.custom ? preset.wins : botForm.wins_percentage,
                          preset && !preset.custom ? preset.losses : botForm.losses_percentage,
                          preset && !preset.custom ? preset.draws : botForm.draws_percentage
                        );
                        setBotForm(prev => ({ ...prev, wins_count: W, losses_count: L, draws_count: D }));
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    >
                      {defaultPresets.map(preset => (
                        <option key={preset.name} value={preset.name}>{preset.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Победы (%):</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={botForm.wins_percentage}
                      onChange={(e) => {
                        const wins = parseFloat(e.target.value) || 0;
                        const newForm = { ...botForm, wins_percentage: wins };
                        setSelectedPreset("Custom");
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                        savePercentagesToStorage(wins, botForm.losses_percentage, botForm.draws_percentage);
                        const { W, L, D } = recalcCountsFromPercents(botForm.cycle_games, wins, botForm.losses_percentage, botForm.draws_percentage);
                        setBotForm(prev => ({ ...prev, wins_count: W, losses_count: L, draws_count: D }));
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Поражения (%):</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={botForm.losses_percentage}
                      onChange={(e) => {
                        const losses = parseFloat(e.target.value) || 0;
                        const newForm = { ...botForm, losses_percentage: losses };
                        setSelectedPreset("Custom");
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                        savePercentagesToStorage(botForm.wins_percentage, losses, botForm.draws_percentage);
                        const { W, L, D } = recalcCountsFromPercents(botForm.cycle_games, botForm.wins_percentage, losses, botForm.draws_percentage);
                        setBotForm(prev => ({ ...prev, wins_count: W, losses_count: L, draws_count: D }));
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Ничьи (%):</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={botForm.draws_percentage}
                      onChange={(e) => {
                        const draws = parseFloat(e.target.value) || 0;
                        const newForm = { ...botForm, draws_percentage: draws };
                        setSelectedPreset("Custom");
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                        savePercentagesToStorage(botForm.wins_percentage, botForm.losses_percentage, draws);
                        const { W, L, D } = recalcCountsFromPercents(botForm.cycle_games, botForm.wins_percentage, botForm.losses_percentage, draws);
                        setBotForm(prev => ({ ...prev, wins_count: W, losses_count: L, draws_count: D }));
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                </div>
                <div className="text-xs text-text-secondary">
                  Сумма должна быть 100%. Из {botForm.cycle_games} игр: {Math.round(botForm.cycle_games * botForm.wins_percentage / 100)} побед, {Math.round(botForm.cycle_games * botForm.losses_percentage / 100)} поражений. Ничьи ({Math.round(botForm.cycle_games * botForm.draws_percentage / 100)} дополнительно) не засчитываются в цикл.
                </div>
              </div>

              {/* Объединенный блок: Циклы и Настройки таймингов */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Циклы и Настройки таймингов</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Игр в цикле */}
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Игр в цикле:</label>
                    <input
                      type="number"
                      min="1"
                      max="66"
                      value={botForm.cycle_games}
                      onChange={(e) => {
                        const newValue = Math.min(100, Math.max(4, parseInt(e.target.value) || 12));
                        updateBalanceGames(newValue, true);
                        const newForm = { ...botForm, cycle_games: newValue };
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                    <div className="text-xs text-text-secondary mt-1">Количество игр в одном цикле (1-66)</div>
                  </div>
                  {/* Пауза между циклами */}
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Пауза между циклами:</label>
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
                    <div className="text-xs text-text-secondary mt-1">Интервал после завершения цикла до начала нового</div>
                  </div>
                  {/* Пауза при ничье */}
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
                    <div className="text-xs text-text-secondary mt-1">При ничье создается новая ставка через указанное время</div>
                  </div>
                </div>
                {/* Вариант 2: Без лайв‑превью ROI в режиме редактирования */}
              </div>

              {/* Стратегия и режим */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Стратегия и режим</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Стратегия прибыли:</label>
                    <select
                      value={botForm.profit_strategy}
                      onChange={(e) => setBotForm({...botForm, profit_strategy: e.target.value})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    >
                      <option value="balanced">Сбалансированная</option>
                      <option value="start-positive">Ранняя прибыль</option>
                      <option value="start-negative">Поздние потери</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Режим создания:</label>
                    <select
                      value={botForm.creation_mode}
                      onChange={(e) => setBotForm({...botForm, creation_mode: e.target.value})}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white"
                    >
                      <option value="queue-based">По очереди</option>
                      <option value="always-first">Всегда первый</option>
                      <option value="after-all">После всех</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Ошибки валидации */}
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
              <div className="flex space-x-3 pt-2">
                <button
                  onClick={updateIndividualBotSettings}
                  disabled={!extendedValidation.isValid}
                  className={`px-6 py-3 rounded-lg font-rajdhani font-bold transition-colors ${
                    extendedValidation.isValid 
                      ? 'bg-accent-primary text-white hover:bg-accent-secondary' 
                      : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  }`}
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
                  onClick={() => {
                    setIsEditModalOpen(false);
                    setEditingBot(null);
                    setExtendedValidation({ isValid: true, errors: [] });
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
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Результат</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-primary">
                      {cycleData.games.map((game, index) => {
                        // Функция для получения иконки хода
                        const getMoveIcon = (move) => {
                          switch (move?.toUpperCase()) {
                            case 'ROCK': return '🪨';
                            case 'PAPER': return '📄';
                            case 'SCISSORS': return '✂️';
                            default: return '—';
                          }
                        };

                        // Функция для форматирования гемов с настоящими иконками из /app/frontend/public/gems
                        const formatGemsWithIcons = (gems) => {
                          if (!gems || typeof gems !== 'object') return '—';
                          
                          const gemIconMap = {
                            'Ruby': '/gems/gem-red.svg',
                            'Amber': '/gems/gem-orange.svg', 
                            'Topaz': '/gems/gem-yellow.svg',
                            'Emerald': '/gems/gem-green.svg',
                            'Aquamarine': '/gems/gem-cyan.svg',
                            'Sapphire': '/gems/gem-blue.svg',
                            'Magic': '/gems/gem-purple.svg'
                          };
                          
                          return Object.entries(gems)
                            .filter(([gemType, qty]) => qty > 0)
                            .map(([gemType, qty]) => (
                              <span key={gemType} className="inline-flex items-center mr-2">
                                <img 
                                  src={gemIconMap[gemType] || '/gems/gem-red.svg'} 
                                  alt={gemType} 
                                  className="w-4 h-4 inline-block mr-1"
                                />
                                ×{qty}
                              </span>
                            ));
                        };

                        // Функция для получения цвета роли пользователя (модератор желтый)
                        const getRoleColor = (role) => {
                          const roleColors = {
                            'USER': 'bg-blue-600',
                            'MODERATOR': 'bg-yellow-600', 
                            'ADMIN': 'bg-purple-600',
                            'SUPER_ADMIN': 'bg-red-600'
                          };
                          return roleColors[role] || 'bg-gray-600';
                        };

                        // Сокращенный ID (первые 4 + последние 4)
                        const shortId = game.game_id && game.game_id.length > 8 
                          ? `${game.game_id.substring(0, 4)}…${game.game_id.substring(game.game_id.length - 4)}`
                          : game.game_id || 'N/A';

                        return (
                          <tr key={game.game_id} className="transition-colors hover:border-l-4 hover:bg-gray-900 hover:bg-opacity-20 hover:border-green-400">
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-white font-bold">
                                {index + 1}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-white font-mono">
                                {shortId}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-white">
                                {new Date(game.completed_at || game.created_at).toLocaleDateString('ru-RU')}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-white">
                                {new Date(game.completed_at || game.created_at).toLocaleTimeString('ru-RU')}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto font-bold text-accent-primary">
                                ${game.bet_amount || game.amount || 0}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-white">
                                {formatGemsWithIcons(game.bet_gems)}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-white">
                                <div className="space-y-1">
                                  <div><span className="text-green-400 font-bold">Бот:</span> {getMoveIcon(game.creator_move)}</div>
                                  <div><span className="text-orange-400 font-bold">Соперник:</span> {getMoveIcon(game.opponent_move)}</div>
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-roboto font-bold text-white ${getRoleColor(game.opponent_role || 'USER')}`}>
                                {game.opponent || 'N/A'}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto">
                                <span className={`font-bold ${
                                  game.winner === 'Победа' ? 'text-green-400' : 
                                  game.winner === 'Поражение' ? 'text-red-400' : 'text-gray-400'
                                }`}>
                                  {game.winner || 'Ничья'}
                                </span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
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

      {/* Модальное окно истории циклов */}
      {isCycleHistoryModalOpen && selectedBotForCycleHistory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 w-full max-w-6xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-rajdhani text-2xl font-bold text-white">
                📊 История циклов — {selectedBotForCycleHistory.name}
              </h3>
              <button
                onClick={() => setIsCycleHistoryModalOpen(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              {cycleHistoryData.length === 0 ? (
                <div className="text-center text-text-secondary py-8">
                  <div className="text-6xl mb-4">📅</div>
                  <p className="text-lg">История циклов пока пуста</p>
                  <p className="text-sm mt-2">Завершенные циклы будут отображаться здесь</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-surface-sidebar">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">№</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Дата завершения</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Время цикла</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Игры</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">W/L/D</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Ставки</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Выигрыш</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Прибыль</th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Действия</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-primary">
                      {cycleHistoryData.map((cycle, index) => (
                        <tr key={cycle.id || index} className="hover:bg-surface-sidebar hover:bg-opacity-30">
                          <td className="px-4 py-3 text-white font-roboto text-sm">
                            {index + 1}
                          </td>
                          <td className="px-4 py-3 text-white font-roboto text-sm">
                            {new Date(cycle.completed_at || cycle.created_at).toLocaleDateString('ru-RU')}
                          </td>
                          <td className="px-4 py-3 text-white font-roboto text-sm">
                            {cycle.duration || '—'}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-accent-primary font-roboto text-sm font-bold">
                              {cycle.total_games || cycle.games_played || 0}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-green-400 text-xs font-roboto font-bold">
                              {cycle.wins || 0}
                            </span>
                            /
                            <span className="text-red-400 text-xs font-roboto font-bold">
                              {cycle.losses || 0}
                            </span>
                            /
                            <span className="text-yellow-400 text-xs font-roboto font-bold">
                              {cycle.draws || 0}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-white font-roboto text-sm">
                              ${Math.round(cycle.total_bet || cycle.total_wagered || 0)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-green-400 font-roboto text-sm font-bold">
                              ${Math.round(cycle.total_winnings || 0)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`font-roboto text-sm font-bold ${
                              (cycle.profit || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              ${Math.round(cycle.profit || 0)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => handleCycleDetailsModal(cycle, selectedBotForCycleHistory)}
                              className="text-blue-400 hover:text-blue-300 text-sm underline"
                              title="Показать детали цикла"
                            >
                              Детали
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Кнопки */}
              <div className="flex justify-end pt-4">
                <button
                  onClick={() => setIsCycleHistoryModalOpen(false)}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно деталей цикла */}
      {isCycleDetailsModalOpen && cycleDetailsData && selectedCycleForDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-green-500 border-opacity-50 rounded-lg p-6 max-w-6xl w-full mx-4 max-h-[85vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-green-400">
                📈 История цикла: {cycleDetailsData.bot_name} — Цикл #{cycleDetailsData.cycle_number}
              </h3>
              <button
                onClick={() => setIsCycleDetailsModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Краткая статистика цикла */}
            <div className="bg-surface-sidebar border border-border-primary rounded-lg p-4 mb-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Дата завершения</div>
                  <div className="text-white font-roboto text-sm">
                    {new Date(cycleDetailsData.completed_at).toLocaleDateString('ru-RU')}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Длительность</div>
                  <div className="text-white font-roboto text-sm">{cycleDetailsData.duration}</div>
                </div>
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Игры</div>
                  <div className="text-accent-primary font-roboto text-sm font-bold">
                    {cycleDetailsData.total_games}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Винрейт</div>
                  <div className="text-orange-400 font-roboto text-sm font-bold">
                    {cycleDetailsData.win_percentage}%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">W/L/D</div>
                  <div className="text-white font-roboto text-sm">
                    <span className="text-green-400">{cycleDetailsData.wins}</span>/
                    <span className="text-red-400">{cycleDetailsData.losses}</span>/
                    <span className="text-yellow-400">{cycleDetailsData.draws}</span>
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Сумма ставок</div>
                  <div className="text-white font-roboto text-sm">${Math.round(cycleDetailsData.total_bet)}</div>
                </div>
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Выигрыши</div>
                  <div className="text-green-400 font-roboto text-sm font-bold">
                    ${Math.round(cycleDetailsData.total_winnings)}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Чистая прибыль</div>
                  <div className={`font-roboto text-sm font-bold ${
                    cycleDetailsData.profit >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    ${Math.round(cycleDetailsData.profit)}
                  </div>
                </div>
              </div>
            </div>

            {/* Детали всех ставок цикла */}
            <div className="mb-4">
              <h4 className="text-white font-rajdhani text-lg font-bold mb-3">
                Все ставки цикла ({cycleDetailsData.bets?.length || 0})
              </h4>
              
              {cycleDetailsData.bets && cycleDetailsData.bets.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-surface-sidebar">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          #
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Дата
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Ставка
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Ход
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Против
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Результат
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Выплата
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          P&L
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-primary">
                      {cycleDetailsData.bets.map((bet, index) => (
                        <tr key={bet.id} className="hover:bg-surface-sidebar hover:bg-opacity-30">
                          <td className="px-3 py-2 text-white font-roboto text-sm">
                            {bet.game_number}
                          </td>
                          <td className="px-3 py-2 text-text-secondary font-roboto text-xs">
                            {new Date(bet.created_at).toLocaleString('ru-RU', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </td>
                          <td className="px-3 py-2 text-white font-roboto text-sm">
                            ${bet.bet_amount}
                          </td>
                          <td className="px-3 py-2 text-white font-roboto text-sm">
                            {bet.move === 'rock' ? '🪨' : bet.move === 'paper' ? '📄' : '✂️'}
                          </td>
                          <td className="px-3 py-2 text-white font-roboto text-sm">
                            {bet.opponent_move === 'rock' ? '🪨' : bet.opponent_move === 'paper' ? '📄' : '✂️'}
                          </td>
                          <td className="px-3 py-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-roboto font-bold ${
                              bet.result === 'win' 
                                ? 'bg-green-500 bg-opacity-20 text-green-400' 
                                : bet.result === 'loss'
                                ? 'bg-red-500 bg-opacity-20 text-red-400'
                                : 'bg-yellow-500 bg-opacity-20 text-yellow-400'
                            }`}>
                              {bet.result === 'win' ? 'Выигрыш' : bet.result === 'loss' ? 'Проигрыш' : 'Ничья'}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-white font-roboto text-sm">
                            {bet.result === 'win' ? `$${Math.round(bet.payout)}` : '—'}
                          </td>
                          <td className="px-3 py-2">
                            <span className={`font-roboto text-sm font-bold ${
                              bet.result === 'win' 
                                ? 'text-green-400' 
                                : bet.result === 'loss'
                                ? 'text-red-400'
                                : 'text-text-secondary'
                            }`}>
                              {bet.result === 'win' 
                                ? `+$${Math.round(bet.payout - bet.bet_amount)}` 
                                : bet.result === 'loss'
                                ? `-$${bet.bet_amount}`
                                : '$0'
                              }
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center text-text-secondary py-4">
                  <p>Нет данных о ставках для этого цикла</p>
                </div>
              )}
            </div>

            {/* Кнопка закрытия */}
            <div className="flex justify-end">
              <button
                onClick={() => setIsCycleDetailsModalOpen(false)}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold"
              >
                Закрыть
              </button>
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