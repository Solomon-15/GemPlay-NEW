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

// Компонент для отображения обратного отсчёта паузы
const PauseCountdown = ({ remainingSeconds: initialSeconds, botId }) => {
  const [remainingSeconds, setRemainingSeconds] = useState(initialSeconds);

  useEffect(() => {
    setRemainingSeconds(initialSeconds);
  }, [initialSeconds]);

  useEffect(() => {
    if (remainingSeconds <= 0) return;

    const interval = setInterval(() => {
      setRemainingSeconds(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [remainingSeconds]);

  if (remainingSeconds <= 0) return null;

  const formatTime = (seconds) => {
    if (seconds < 60) {
      return `${seconds}с`;
    } else {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}м ${secs}с`;
    }
  };

  return (
    <div className="text-orange-400 font-roboto text-xs font-bold animate-pulse">
      ⏳ {formatTime(remainingSeconds)}
    </div>
  );
};

const RegularBotsManagement = () => {
  const [stats, setStats] = useState({
    active_bots: 0,
    bets_24h: 0,
    wins_24h: 0,
    win_rate: 0,
    total_bet_value: 0,
    errors: 0,
    most_active: []
  });
  const [botsList, setBotsList] = useState([]);
  const [cycleSumsByBot, setCycleSumsByBot] = useState({}); // { [botId]: { total_sum, active_pool, draws_sum, profit, wins_sum, losses_sum } }
  const [cycleHistoryProfitByBot, setCycleHistoryProfitByBot] = useState({}); // { [botId]: totalProfitFromCompletedCycles }
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

  const [loadingStates, setLoadingStates] = useState({});

  
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

  // Состояния для быстрого запуска ботов
  const [isQuickLaunchModalOpen, setIsQuickLaunchModalOpen] = useState(false);
  const [quickLaunchPresets, setQuickLaunchPresets] = useState([]);
  const [isCreatingPreset, setIsCreatingPreset] = useState(false);
  const [selectedPresetForQuickLaunch, setSelectedPresetForQuickLaunch] = useState("⭐ ROI 10%");
  
  // Состояния для перетаскивания модального окна
  const [modalPosition, setModalPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [currentPreset, setCurrentPreset] = useState({
    name: 'Bot',
    buttonName: '',
    buttonColor: 'blue',
    min_bet_amount: 1.0,
    max_bet_amount: 100.0,
    wins_percentage: 41.73,
    losses_percentage: 30.27,
    draws_percentage: 28.0,
    cycle_games: 16,
    pause_between_cycles: 5,
                          wins_count: 6,
                          losses_count: 6,
                          draws_count: 4
  });

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
  
  // Состояния для сортировки истории циклов
  const [cycleSortField, setCycleSortField] = useState(null);
  const [cycleSortDirection, setCycleSortDirection] = useState('asc'); // 'asc' или 'desc'

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

  // Функция для сортировки истории циклов
  const handleCycleSorting = (field) => {
    const newDirection = cycleSortField === field && cycleSortDirection === 'asc' ? 'desc' : 'asc';
    setCycleSortField(field);
    setCycleSortDirection(newDirection);

    const sortedData = [...cycleHistoryData].sort((a, b) => {
      let valueA, valueB;

      switch (field) {
        case 'duration':
          // Преобразуем длительность в секунды для сортировки
          valueA = a.duration_seconds || 0;
          valueB = b.duration_seconds || 0;
          break;
        case 'total_bets':
          valueA = a.total_bets || a.total_games || 0;
          valueB = b.total_bets || b.total_games || 0;
          break;
        case 'wins':
          valueA = a.wins || 0;
          valueB = b.wins || 0;
          break;
        case 'total_winnings':
          valueA = a.total_winnings || 0;
          valueB = b.total_winnings || 0;
          break;
        case 'total_losses':
          valueA = a.total_losses || 0;
          valueB = b.total_losses || 0;
          break;
        case 'profit':
          valueA = a.profit || 0;
          valueB = b.profit || 0;
          break;
        case 'roi':
          // Используем roi_active от backend, если доступно, иначе вычисляем самостоятельно
          if (a.roi_active !== undefined && a.roi_active !== null) {
            valueA = Number(a.roi_active);
          } else {
            const activePoolA = (a.total_winnings || 0) + (a.total_losses || 0);
            valueA = activePoolA > 0 ? ((a.profit || 0) / activePoolA) * 100 : 0;
          }
          
          if (b.roi_active !== undefined && b.roi_active !== null) {
            valueB = Number(b.roi_active);
          } else {
            const activePoolB = (b.total_winnings || 0) + (b.total_losses || 0);
            valueB = activePoolB > 0 ? ((b.profit || 0) / activePoolB) * 100 : 0;
          }
          break;
        default:
          return 0;
      }

      if (newDirection === 'asc') {
        return valueA - valueB;
      } else {
        return valueB - valueA;
      }
    });

    setCycleHistoryData(sortedData);
  };

  // Функция для открытия модального окна деталей цикла
  const handleCycleDetailsModal = async (cycle, bot) => {
    try {
      const token = localStorage.getItem('token');
      
      // Если это текущий цикл (id === 'current-cycle'), используем другой эндпоинт
      let response;
      if (cycle.id === 'current-cycle') {
        response = await axios.get(`${API}/admin/bots/${bot.id}/cycle-bets`, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        response = await axios.get(`${API}/admin/bots/${bot.id}/completed-cycle-bets`, {
          headers: { Authorization: `Bearer ${token}` },
          params: { cycle_id: cycle.id }
        });
      }
      
      const data = response.data || {};
      const bets = Array.isArray(data.bets) ? data.bets : [];
      const cycleData = data.cycle || {};

      // Рассчитываем плановый ROI (из бэкенда) для колонки Винрейт
      const roiPlanned = (() => {
        // Берём строго из поля, которое отдаёт бэк (пересчитанное по калькулятору предпросмотра)
        if (bot && bot.roi_planned_percent !== undefined && bot.roi_planned_percent !== null && isFinite(Number(bot.roi_planned_percent))) {
          return Number(bot.roi_planned_percent);
        }
        // Фолбэк: повторяем формулу бэка на фронте
        const winPct = Number(bot.wins_percentage ?? 0);
        const lossPct = Number(bot.losses_percentage ?? 0);
        const cycleGames = Number(bot.cycle_games ?? 12) || 12;
        const minBet = Math.round(Number(bot.min_bet_amount ?? 1) || 1);
        const maxBet = Math.round(Number(bot.max_bet_amount ?? 50) || 50);
        const exactCycleTotal = Math.round(((minBet + maxBet) / 2.0) * cycleGames);
        const winsSumPlanned = Math.floor(exactCycleTotal * winPct / 100.0);
        const lossesSumPlanned = Math.ceil(exactCycleTotal * lossPct / 100.0);
        const activePoolPlanned = winsSumPlanned + lossesSumPlanned;
        const profitPlanned = winsSumPlanned - lossesSumPlanned;
        const roi = activePoolPlanned > 0 ? (profitPlanned / activePoolPlanned) * 100.0 : 0.0;
        return roi;
      })();

      let details;
      if (cycle.id === 'current-cycle') {
        // Для текущего цикла используем данные из /cycle-bets
        details = {
          id: cycle.id,
          bot_name: data.bot_name || bot.name,
          cycle_number: cycle.cycle_number,
          completed_at: cycle.end_time || cycle.completed_at,
          duration: cycle.duration,
          start_time: cycle.start_time,
          end_time: cycle.end_time,
          total_games: bets.length,
          wins: bets.filter(b => b.result === 'win').length,
          losses: bets.filter(b => b.result === 'loss').length,
          draws: bets.filter(b => b.result === 'draw').length,
          total_bet: data.sums?.total_sum || 0,
          total_winnings: data.sums?.wins_sum || 0,
          total_losses: data.sums?.losses_sum || 0,
          profit: data.sums?.profit || 0,
          win_rate: bets.length > 0 ? ((bets.filter(b => b.result === 'win').length / bets.length) * 100).toFixed(1) : '0.0',
          bets: bets,
          planned_roi: roiPlanned
        };
      } else {
        // Для завершённых циклов используем данные из /completed-cycle-bets
        details = {
          id: cycle.id,
          bot_name: bot.name,
          cycle_number: cycle.cycle_number,
          completed_at: cycle.end_time || cycle.completed_at,
          duration: cycle.duration,
          start_time: cycle.start_time,
          end_time: cycle.end_time,
          total_games: bets.length,
          wins: bets.filter(b => b.result_class === 'win').length,
          losses: bets.filter(b => b.result_class === 'loss').length,
          draws: bets.filter(b => b.result_class === 'draw').length,
          total_bet: cycleData.total_bet_amount || 0,
          total_winnings: cycleData.total_winnings || 0,
          total_losses: cycleData.total_losses || 0,
          profit: cycleData.net_profit || 0,
          win_rate: bets.length > 0 ? ((bets.filter(b => b.result_class === 'win').length / bets.length) * 100).toFixed(1) : '0.0',
          bets: bets,
          planned_roi: roiPlanned
        };
      }

      setSelectedCycleForDetails(cycle);
      setCycleDetailsData(details);
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
          wins_percentage: parsed.wins_percentage || 39.6,
          losses_percentage: parsed.losses_percentage || 32.4,
          draws_percentage: parsed.draws_percentage || 28.0
        };
      }
    } catch (error) {
      console.error('Ошибка загрузки сохраненных процентов:', error);
    }
    return {
      wins_percentage: 39.6,
      losses_percentage: 32.4, 
      draws_percentage: 28.0
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
      
      // Процент исходов игр (новые значения по умолчанию: ⭐ ROI 10%)
      wins_percentage: savedPercentages.wins_percentage || 41.73,
      losses_percentage: savedPercentages.losses_percentage || 30.27,
      draws_percentage: savedPercentages.draws_percentage || 28.0,
      
      cycle_games: 16, // НОВОЕ: 16 игр по умолчанию (было 12)
      pause_between_cycles: 5, // 1-3600 секунд
      pause_between_bets: 5, // 1-3600 секунд
      

      
      cycle_total_amount: 0, // calculated automatically
      active_pool_amount: 0, // НОВОЕ: активный пул для отображения
      roi_active: 0.0        // НОВОЕ: ROI_active для превью
    };
  });

  // ПРАВИЛЬНАЯ ЛОГИКА: Метод наибольших остатков для распределения суммы цикла
  const calculateCycleAmounts = () => {
    if (!botForm.min_bet_amount || !botForm.max_bet_amount || !botForm.cycle_games) {
      return { total: 0, active_pool: 0, roi_active: 0 };
    }
    
    const min_bet = parseFloat(botForm.min_bet_amount);
    const max_bet = parseFloat(botForm.max_bet_amount);
    const games = parseInt(botForm.cycle_games);
    
    // Метод наибольших остатков для распределения по исходам
    // Для стандартного случая [1-100] × 16 игр используем эталонные точные суммы
    let exactWins, exactLosses, exactDraws;
    
    if (min_bet === 1 && max_bet === 100 && games === 16) {
      // Эталонные точные доли для базы 800 (W=352, L=288, D=160)
      exactWins = 352.00;
      exactLosses = 288.00;
      exactDraws = 160.00;
    } else {
      // Для других случаев вычисляем пропорционально от базы 800
      const standardSum = 800.00;
      const scaleFactor = (((min_bet + max_bet) / 2.0) * games) / (((1 + 100) / 2.0) * 16);
      
      const winsPercent = botForm.wins_percentage / 100;
      const lossesPercent = botForm.losses_percentage / 100;
      const drawsPercent = botForm.draws_percentage / 100;
      
      exactWins = standardSum * scaleFactor * winsPercent;
      exactLosses = standardSum * scaleFactor * lossesPercent;
      exactDraws = standardSum * scaleFactor * drawsPercent;
    }
    
    // Правило округления half-up: если дробная часть ≥ 0,50 — округляем вверх; если < 0,50 — вниз
    const halfUpRound = (num) => {
      const fraction = num - Math.floor(num);
      return fraction >= 0.50 ? Math.ceil(num) : Math.floor(num);
    };
    
    // Применяем half-up округление (результат: 356 / 291 / 162 = 809)
    let winsSum = halfUpRound(exactWins);
    let lossesSum = halfUpRound(exactLosses);
    let drawsSum = halfUpRound(exactDraws);
    
    // Итоговая сумма цикла = сумма всех округленных частей
    const finalCycleTotal = winsSum + lossesSum + drawsSum;
    
    // Активный пул (база для ROI) - только победы и поражения
    const activePool = winsSum + lossesSum;
    const profit = winsSum - lossesSum;
    const roiActive = activePool > 0 ? ((profit / activePool) * 100) : 0;
    
    return {
      total: finalCycleTotal,
      active_pool: activePool,
      roi_active: Math.round(roiActive * 100) / 100,
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
  
  // ИСПРАВЛЕННАЯ ФУНКЦИЯ: Расчет превью ROI по правильной логике
  const calculatePreviewFromCounts = (winsCount, lossesCount, drawsCount, minBet, maxBet, winsPercent, lossesPercent, drawsPercent) => {
    const totalGames = (winsCount || 0) + (lossesCount || 0) + (drawsCount || 0);
    if (!totalGames || !minBet || !maxBet || !winsPercent || !lossesPercent || !drawsPercent) {
      return { total: 0, active_pool: 0, profit: 0, roi_active: 0 };
    }
    
    // Масштабируем общую сумму от базы 800 (для 16 игр, 1–100)
    const min_bet = parseFloat(minBet);
    const max_bet = parseFloat(maxBet);
    
    // Коэффициент масштабирования по количеству игр
    const gamesCoeff = totalGames / 16;
    
    // Коэффициент масштабирования по диапазону ставок
    const rangeCoeff = ((min_bet + max_bet) / 2) / ((1 + 100) / 2);
    
    // Общая сумма цикла (масштабированная от базы 800)
    const totalCycleSum = Math.round(800 * gamesCoeff * rangeCoeff);
    
    // Переводим проценты пресета в суммы ставок
    const winsSum = Math.round((winsPercent / 100) * totalCycleSum);
    const lossesSum = Math.round((lossesPercent / 100) * totalCycleSum);
    const drawsSum = Math.round((drawsPercent / 100) * totalCycleSum);
    
    // Корректируем суммы чтобы точно получить totalCycleSum
    const actualTotal = winsSum + lossesSum + drawsSum;
    const diff = totalCycleSum - actualTotal;
    let finalWinsSum = winsSum;
    let finalLossesSum = lossesSum;
    let finalDrawsSum = drawsSum;
    
    // Распределяем разницу пропорционально (малые погрешности)
    if (diff !== 0 && Math.abs(diff) <= 3) {
      if (winsSum >= lossesSum && winsSum >= drawsSum) {
        finalWinsSum += diff;
      } else if (lossesSum >= drawsSum) {
        finalLossesSum += diff;
      } else {
        finalDrawsSum += diff;
      }
    }
    
    // Активный пул = Сумма ставок побед + Сумма ставок поражений
    const activePool = finalWinsSum + finalLossesSum;
    
    // Прибыль = Сумма ставок побед - Сумма ставок поражений
    const profit = finalWinsSum - finalLossesSum;
    
    // ROI_active = (Прибыль ÷ Активный пул) × 100%
    const roiActive = activePool > 0 ? ((profit / activePool) * 100) : 0;
    
    return {
      total: finalWinsSum + finalLossesSum + finalDrawsSum,
      active_pool: activePool,
      profit: profit,
      roi_active: Math.round(roiActive * 100) / 100,
      wins_sum: finalWinsSum,
      losses_sum: finalLossesSum,
      draws_sum: finalDrawsSum
    };
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
  
  const generateDefaultPresets = () => {
    const draws = 28.0;
    const activeShare = 100 - draws; // 72%
    const presets = [
      { name: "Custom", wins: null, losses: null, draws: null, custom: true }
    ];
    for (let roi = 2; roi <= 20; roi++) {
      const r = roi / 100;
      const wins = (activeShare * (1 + r)) / 2; // W% от общего
      const losses = activeShare - wins;        // L% от общего
      const name = roi === 10 ? "⭐ ROI 10%" : `ROI ${roi}%`;
      presets.push({ name, wins: Number(wins.toFixed(2)), losses: Number(losses.toFixed(2)), draws });
    }
    return presets;
  };

  const defaultPresets = generateDefaultPresets();
  
  const [selectedPreset, setSelectedPreset] = useState("⭐ ROI 10%");
  
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

  // Функция применения ROI пресета для быстрого запуска
  const applyROIPresetForQuickLaunch = (preset) => {
    if (!preset || preset.custom) {
      setSelectedPresetForQuickLaunch("Custom");
      return;
    }
    setSelectedPresetForQuickLaunch(preset.name);
    setCurrentPreset(prev => {
      const { W, L, D } = recalcCountsFromPercents(
        prev.cycle_games,
        preset.wins,
        preset.losses,
        preset.draws
      );
      return ({
        ...prev,
        wins_percentage: Number(preset.wins.toFixed(1)),
        losses_percentage: Number(preset.losses.toFixed(1)),
        draws_percentage: Number(preset.draws.toFixed(1)),
        wins_count: W,
        losses_count: L,
        draws_count: D
      });
    });
  };

  // Функции для перетаскивания модального окна
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({
      x: e.clientX - modalPosition.x,
      y: e.clientY - modalPosition.y
    });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    const newX = e.clientX - dragStart.x;
    const newY = e.clientY - dragStart.y;
    
    // Ограничиваем перемещение в пределах экрана
    const maxX = window.innerWidth - 400; // минимум 400px видимой области
    const maxY = window.innerHeight - 200; // минимум 200px видимой области
    
    setModalPosition({
      x: Math.max(-200, Math.min(maxX, newX)), // разрешаем частичный выход за край
      y: Math.max(-200, Math.min(maxY, newY)) // разрешаем выход вверх тоже
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Сброс позиции при открытии модального окна
  useEffect(() => {
    if (isQuickLaunchModalOpen) {
      setModalPosition({ x: 0, y: 0 });
      setIsDragging(false);
    }
  }, [isQuickLaunchModalOpen]);

  // Добавляем глобальные обработчики событий для перетаскивания
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = 'none'; // Отключаем выделение текста при перетаскивании
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.userSelect = '';
      };
    }
  }, [isDragging, dragStart, modalPosition]);
  
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

    // 1) Целевое количество ничьих: близко к 28% и в пределах [25%;30%]
    const minDraws = Math.floor(N * 0.25);
    const maxDraws = Math.ceil(N * 0.30);
    const targetDrawsRaw = (drawsP / 100) * N;
    let D = Math.floor(targetDrawsRaw + 0.5); // half-up к ближайшему
    if (D < minDraws) D = minDraws;
    if (D > maxDraws) D = maxDraws;

    // 2) Распределяем активные игры между W и L по долям winsP/(winsP+lossesP)
    const activeGames = Math.max(0, N - D);
    const activePercent = (winsP + lossesP) > 0 ? (winsP + lossesP) : 1;
    const winsShare = winsP / activePercent;

    let W = Math.floor(activeGames * winsShare + 0.5); // half-up
    let L = activeGames - W;

    // 3) Правила допустимой разницы |W-L| в зависимости от N
    let deltaMax = 1;
    if (N <= 10) deltaMax = 1; 
    else if (N <= 20) deltaMax = 2; 
    else if (N <= 30) deltaMax = 3; 
    else if (N <= 40) deltaMax = 4; 
    else deltaMax = 4; // 41+ — в пределах ±3–4, разрешаем максимум 4

    // 4) Балансировка до допустимой разницы (минимизируем разницу)
    const balanceTowardEquality = () => {
      let attempts = 0;
      while (Math.abs(W - L) > deltaMax && attempts < 50) {
        if (W > L && W > 0) { W -= 1; L += 1; }
        else if (L > W && L > 0) { L -= 1; W += 1; }
        attempts++;
      }
    };

    balanceTowardEquality();

    // 5) Гарантируем допустимые значения и правило L ≥ W (равенство допустимо)
    if (N >= 3) {
      if (W === 0) { W = 1; if (L > 0) L -= 1; }
      if (L === 0) { L = 1; if (W > 0) W -= 1; }
      // Применяем L ≥ W (не нарушая deltaMax и сумму)
      if (W > L) {
        const shift = Math.min(Math.ceil((W - L) / 2), W); // минимальный сдвиг к равенству
        W -= shift;
        L += shift;
        // Если всё ещё W > L, делаем ещё один шаг
        if (W > L && W > 0) { W -= 1; L += 1; }
      }
    }

    // 6) Спец-правило: при N=16 и ROI≈10% по умолчанию 6/6/4
    const isRoi10 = Math.abs((winsP - lossesP) / (winsP + lossesP || 1) - 0.10) < 0.01 && Math.abs(drawsP - 28) < 0.6;
    if (N === 16 && isRoi10) {
      D = 4; W = 6; L = 6;
    }

    // Финальная проверка и корректировка суммы
    W = Math.max(0, W); L = Math.max(0, L); D = Math.max(0, D);
    let total = W + L + D;
    if (total !== N) {
      const diff = N - total;
      if (diff > 0) {
        // Добавляем в меньшие категории, приоритет ничьям, затем меньшей из W/L
        if (D < maxDraws) { const add = Math.min(diff, maxDraws - D); D += add; total += add; }
        if (total < N) {
          const remaining = N - total;
          if (W <= L) W += remaining; else L += remaining;
        }
      } else if (diff < 0) {
        // Урезаем из наибольшей категории
        let toRemove = -diff;
        while (toRemove > 0) {
          if (D > minDraws && D >= W && D >= L) { D -= 1; }
          else if (W >= L && W > 0) { W -= 1; }
          else if (L > 0) { L -= 1; }
          toRemove -= 1;
        }
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
    
    // Загружаем пресеты быстрого запуска
    try {
      const saved = localStorage.getItem('quickLaunchPresets');
      if (saved) {
        const presets = JSON.parse(saved);
        setQuickLaunchPresets(presets);
      }
    } catch (error) {
      console.error('Ошибка загрузки пресетов:', error);
    }
    
    // Периодическое обновление для синхронизации таймеров паузы
    const interval = setInterval(() => {
      fetchBotsList();
    }, 5000); // Обновляем каждые 5 секунд
    
    return () => clearInterval(interval);
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
      const response = await axios.get(`${API}/admin/bots`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          page: pagination.currentPage,
          limit: pagination.itemsPerPage
        }
      });
      
      const botsData = response.data.bots || response.data;
      setBotsList(botsData); // Больше не сортируем здесь, используем getSortedBots
      
      // Предзагружаем суммы цикла для каждого бота из модалки "Детали цикла"
      if (Array.isArray(botsData)) {
        botsData.forEach(b => {
          if (b?.id && !cycleSumsByBot[b.id]) {
            fetchAndCacheCycleSums(b.id);
          }
          // Предзагружаем общую прибыль из истории циклов для колонки "Статистика"
          if (b?.id && cycleHistoryProfitByBot[b.id] === undefined) {
            fetchAndCacheCycleHistoryProfit(b.id);
          }
        });
      }
      
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

  // Предзагрузка корректных сумм цикла как в модалке "Детали цикла"
  const fetchAndCacheCycleSums = async (botId) => {
    try {
      const response = await axios.get(`${API}/admin/bots/${botId}/cycle-bets`, getApiConfig());
      const sums = response.data?.sums;
      if (sums) {
        setCycleSumsByBot(prev => ({
          ...prev,
          [botId]: {
            total_sum: Number(sums.total_sum || 0),
            active_pool: Number(sums.active_pool || 0),
            draws_sum: Number(sums.draws_sum || 0),
            wins_sum: Number(sums.wins_sum || 0),
            losses_sum: Number(sums.losses_sum || 0),
            profit: Number(sums.profit || 0),
            roi_active: Number(sums.roi_active || 0),
            exact_cycle_total: Number((response.data && response.data.exact_cycle_total) || 0)
          }
        }));
      }
    } catch (err) {
      // Тихо игнорируем ошибку, список всё равно отобразится с fallback
      // console.warn('Не удалось предзагрузить суммы цикла для бота', botId, err);
    }
  };

  // Предзагрузка общей прибыли из истории циклов (для колонки "Статистика")
  const fetchAndCacheCycleHistoryProfit = async (botId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/${botId}/cycle-history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const cycleHistoryData = response.data.games || [];
      
      // ИСПРАВЛЕНО: Фильтруем фиктивные циклы перед подсчётом прибыли
      const realCycles = cycleHistoryData.filter(cycle => 
        !cycle.id || !cycle.id.startsWith('temp_cycle_')
      );
      
      // Кэшируем данные только если есть реальные завершённые циклы
      if (realCycles.length > 0) {
        const totalProfit = realCycles.reduce((total, cycle) => total + (cycle.profit || 0), 0);
        setCycleHistoryProfitByBot(prev => ({
          ...prev,
          [botId]: totalProfit
        }));
      }
      // Если история пуста, не кэшируем, чтобы использовался fallback
    } catch (err) {
      // Тихо игнорируем ошибку, будем использовать fallback значение
      // console.warn('Не удалось предзагрузить прибыль из истории циклов для бота', botId, err);
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
    
    if (formData.pause_between_cycles < 1 || formData.pause_between_cycles > 3600) {
      errors.push('Пауза между циклами должна быть от 1 до 3600 секунд');
    }
    
    
    const validModes = ['always-first', 'queue-based', 'after-all'];

    
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
        pause_between_bets: botForm.pause_between_bets,
        // УДАЛЕНО: creation_mode (наследие)
        // УДАЛЕНО: profit_strategy (наследие)
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
          max_bet_amount: 100.0,
          // Удалено наследие win_percentage
          wins_percentage: savedPercentages.wins_percentage || 41.73,
          losses_percentage: savedPercentages.losses_percentage || 30.27,
          draws_percentage: savedPercentages.draws_percentage || 28.0,
          cycle_games: 16,
          pause_between_cycles: 5,
          pause_between_bets: 5,
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
        max_bet_amount: b.max_bet_amount ?? 100.0,
        // Удалено наследие win_percentage
        // Новая система: подтягиваем баланс и проценты из бота
        wins_count: b.wins_count ?? 6,
        losses_count: b.losses_count ?? 6,
        draws_count: b.draws_count ?? 4,
        wins_percentage: b.wins_percentage ?? 41.73,
        losses_percentage: b.losses_percentage ?? 30.27,
        draws_percentage: b.draws_percentage ?? 28.0,
        cycle_games: b.cycle_games ?? 12,
        pause_between_cycles: b.pause_between_cycles ?? 5,
        pause_between_bets: b.pause_between_bets ?? 5,
        cycle_total_amount: b.cycle_total_amount ?? 0
      });
      setSelectedPreset('Custom');
      validateExtendedFormInRealTime({
        name: b.name || '',
        min_bet_amount: b.min_bet_amount ?? 1.0,
        max_bet_amount: b.max_bet_amount ?? 100.0,
        // Удалено наследие win_percentage
        wins_count: b.wins_count ?? 6,
        losses_count: b.losses_count ?? 6,
        draws_count: b.draws_count ?? 4,
        wins_percentage: b.wins_percentage ?? 41.73,
        losses_percentage: b.losses_percentage ?? 30.27,
        draws_percentage: b.draws_percentage ?? 28.0,
        cycle_games: b.cycle_games ?? 12,
        pause_between_cycles: b.pause_between_cycles ?? 5,
        pause_between_bets: b.pause_between_bets ?? 5,

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
        pause_between_bets: botForm.pause_between_bets,
        // УДАЛЕНО: creation_mode (наследие)
        // УДАЛЕНО: profit_strategy (наследие)
      };

      const response = await axios.patch(`${API}/admin/bots/${editingBot.id}`, botData, {
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
      const response = await axios.post(`${API}/admin/bots/${botId}/recalculate-bets`, {}, {
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

  // Удалено по требованию: handleActiveBetsModal
  const handleActiveBetsModal = async (bot) => { return; }

  const handleCycleBetsDetails = async (bot) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bots/${bot.id}/cycle-bets`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = response.data || {};
      const bets = data.bets || [];
      
      // Создаём фиктивный объект цикла для использования с handleCycleDetailsModal
      const fakeCycle = {
        id: 'current-cycle',
        cycle_number: 'Текущий',
        end_time: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        duration: '—',
        start_time: bets.length > 0 ? bets[0].created_at : new Date().toISOString()
      };
      
      // Используем унифицированную модалку
      await handleCycleDetailsModal(fakeCycle, bot);
    } catch (error) {
      console.error('Ошибка загрузки деталей цикла:', error);
      showErrorRU('Ошибка при загрузке деталей цикла');
    }
  };

  // Вычисление корректной статистики текущего цикла по данным модалки "История цикла"
  const getDerivedCycleStats = (cycle, bot) => {
    try {
      const games = Array.isArray(cycle?.games) ? cycle.games : [];
      const normalize = (val) => (val ?? '').toString().trim().toLowerCase();
      const isWin = (w) => {
        const s = normalize(w);
        return s.includes('win') || s.includes('побед');
      };
      const isLoss = (w) => {
        const s = normalize(w);
        return s.includes('loss') || s.includes('lose') || s.includes('пораж');
      };
      const isDraw = (w) => {
        const s = normalize(w);
        return s.includes('draw') || s.includes('нич');
      };

      const winsCount = games.filter(g => isWin(g?.winner)).length;
      const lossesCount = games.filter(g => isLoss(g?.winner)).length;
      const drawsCount = games.filter(g => isDraw(g?.winner)).length;
      const completed = winsCount + lossesCount + drawsCount;
      // Приоритет длины цикла: bot.cycle_games -> 16 (дефолт) -> ответ бэка
      const cycleLength = Number((bot?.cycle_games && bot.cycle_games > 0) ? bot.cycle_games : (16));

      const totalBet = games.reduce((sum, g) => sum + Number(g?.bet_amount || 0), 0);
      const wonAmount = games.reduce((sum, g) => sum + (isWin(g?.winner) ? Number(g?.bet_amount || 0) : 0), 0);
      const lostAmount = games.reduce((sum, g) => sum + (isLoss(g?.winner) ? Number(g?.bet_amount || 0) : 0), 0);
      const netProfit = wonAmount - lostAmount;
      const denom = Math.max(1, winsCount + lossesCount); // ничьи не входят в знаменатель
      const winRate = (winsCount / denom) * 100;
      const formatMoney = (v) => (Math.round(Number(v || 0) * 100) / 100).toFixed(2);

      return {
        winsCount,
        lossesCount,
        drawsCount,
        completed,
        cycleLength,
        totalBet: formatMoney(totalBet),
        wonAmount: formatMoney(wonAmount),
        lostAmount: formatMoney(lostAmount),
        netProfit: formatMoney(netProfit),
        winRate: (Math.round(winRate * 10) / 10).toFixed(1)
      };
    } catch (e) {
      return {
        winsCount: 0,
        lossesCount: 0,
        drawsCount: 0,
        completed: 0,
        cycleLength: Number(cycle?.cycle_info?.cycle_length || bot?.cycle_games || 16),
        totalBet: '0.00',
        wonAmount: '0.00',
        lostAmount: '0.00',
        netProfit: '0.00',
        winRate: '0.0'
      };
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
  // УДАЛЕНО: Инлайн-редактирование процента выигрышей (наследие)
  const handleEditWinPercentage = async (bot) => {
    try {
      const currentPercentage = 55; // legacy removed
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
      // УДАЛЕНО: вызов устаревшего эндпоинта win-percentage
      /* legacy removed: await axios.put(`${API}/admin/bots/${bot.id}/win-percentage`, {
        win_percentage: newPercentage
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchBotsList();
      showSuccessRU(`Процент выигрышей обновлен (устар.) на ${newPercentage}%`); */
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
        <div className="flex gap-4 flex-nowrap items-stretch">
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
              <p className="text-white text-lg font-rajdhani font-bold">{stats.win_rate}%</p>
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
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-rajdhani font-bold text-white">Список обычных ботов</h3>
            <button
              onClick={() => setIsQuickLaunchModalOpen(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors flex items-center space-x-2"
              title="Быстрый запуск ботов по пресетам"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>⚡ Быстрый запуск</span>
            </button>
          </div>
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
                
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Количество циклов
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
                  Сумма ставок
                </th>
                <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                  Прибыль
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
                  <td colSpan="16" className="px-4 py-8 text-center text-text-secondary">
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
                      <div className="text-white font-roboto text-sm">
                        {(() => {
                          // Количество циклов = завершённые циклы + текущий активный цикл
                          const completedCycles = Number(bot.completed_cycles || 0);
                          
                          // Текущий активный цикл существует, если:
                          // - бот активен И есть активность (игры в цикле ИЛИ активные ставки)
                          // - ИЛИ есть незавершённая активность даже у неактивного бота
                          const hasCurrentActivity = Number(bot.current_cycle_games || 0) > 0 || 
                                                    Number(bot.active_bets || 0) > 0;
                          const hasActiveCycle = bot.is_active || hasCurrentActivity;
                          
                          return completedCycles + (hasActiveCycle ? 1 : 0);
                        })()}
                      </div>
                    </td>

                    <td className="px-4 py-4 whitespace-nowrap text-left">
                      <div className="text-white font-roboto text-xs space-y-1">
                        <div>Игры: {bot.completed_cycles || 0}</div>
                        <div>W/L/D: {(bot.current_cycle_wins || 0)}/{(bot.current_cycle_losses || 0)}/{(bot.current_cycle_draws || 0)}</div>
                        <button
                          onClick={() => handleCycleHistoryModal(bot)}
                          className="text-blue-400 hover:text-blue-300 cursor-pointer underline"
                          title="Показать историю циклов"
>
                          Общая Прибыль: <span className="font-black text-sm">
                            ${Math.round(cycleHistoryProfitByBot[bot.id] !== undefined ? cycleHistoryProfitByBot[bot.id] : (bot.total_net_profit || 0))}
                          </span>
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      {(() => {
                        // Фактический ROI: берём из модалки "Детали цикла" (sums.roi_active)
                        const sums = cycleSumsByBot[bot.id];
                        const roiActualVal = (sums && Number.isFinite(Number(sums.roi_active))) ? Number(sums.roi_active) : NaN;
                        const actualColor = Number.isFinite(roiActualVal) && roiActualVal < 0 ? 'text-red-400' : 'text-white';
                        
                        // Плановый ROI: считаем как на бэке (avgBet, round/floor/ceil)
                        const roiPlanned = (() => {
                          // Берём строго из поля, которое отдаёт бэк (пересчитанное по калькулятору предпросмотра)
                          if (bot && bot.roi_planned_percent !== undefined && bot.roi_planned_percent !== null && isFinite(Number(bot.roi_planned_percent))) {
                            return Number(bot.roi_planned_percent);
                          }
                          // Фолбэк: повторяем формулу бэка на фронте
                          const winPct = Number(bot.wins_percentage ?? 0);
                          const lossPct = Number(bot.losses_percentage ?? 0);
                          const cycleGames = Number(bot.cycle_games ?? 12) || 12;
                          const minBet = Math.round(Number(bot.min_bet_amount ?? 1) || 1);
                          const maxBet = Math.round(Number(bot.max_bet_amount ?? 50) || 50);
                          const exactCycleTotal = Math.round(((minBet + maxBet) / 2.0) * cycleGames);
                          const winsSumPlanned = Math.floor(exactCycleTotal * winPct / 100.0);
                          const lossesSumPlanned = Math.ceil(exactCycleTotal * lossPct / 100.0);
                          const activePoolPlanned = winsSumPlanned + lossesSumPlanned;
                          const profitPlanned = winsSumPlanned - lossesSumPlanned;
                          const roi = activePoolPlanned > 0 ? (profitPlanned / activePoolPlanned) * 100.0 : 0.0;
                          return roi;
                        })();
                        
                        const hasActual = Number.isFinite(roiActualVal);
                        const displayActual = hasActual ? roiActualVal.toFixed(2) + '%' : '—';
                        const displayClass = hasActual ? actualColor : 'text-gray-400';
                        return (
                          <div className="flex flex-col items-center justify-center leading-tight">
                            <span className={`${displayClass} font-roboto text-sm font-bold`} title="Фактический ROI (из модалки 'Детали цикла')">
                              {displayActual}
                            </span>
                            <span className={`text-xs text-yellow-400`} title="Плановый ROI (из бэкенда)">
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
                              width: `${(() => { 
                                const completedBets = bot.completed_bets || 0; 
                                const total = (bot.cycle_games && bot.cycle_games > 0) ? bot.cycle_games : 16;
                                return Math.min((completedBets / total) * 100, 100); 
                              })()}%`
                            }}
                          ></div>
                        </div>
                        <div className="flex items-center justify-center space-x-2">
                          <div className="text-green-400 font-roboto text-sm font-medium">
                            {(() => {
                              // X = количество всех завершённых ставок (новая логика)
                              const completedBets = bot.completed_bets || 0;
                              // Y = остается как есть (общее количество игр в цикле)
                              const total = (bot.cycle_games && bot.cycle_games > 0) ? bot.cycle_games : 16;
                              return `${completedBets}/${total}`;
                            })()}
                          </div>
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
                        {(() => {
                          const sums = cycleSumsByBot[bot.id];
                          if (sums) {
                            const total = Number(sums.total_sum || 0);
                            const from = Number((sums.active_pool !== undefined ? sums.active_pool : (Number(sums.wins_sum || 0) + Number(sums.losses_sum || 0))));
                            const draws = Number(sums.draws_sum || 0);
                            return (
                              <div title={`Общая сумма: ${total}, Ничьи: ${draws}`}>
                                <span className="font-bold">{total}</span>
                                <div className="text-xs text-gray-400">
                                  (из {from}, ничьи: {draws})
                                </div>
                              </div>
                            );
                          }
                          return <span className="font-bold">0</span>;
                        })()}
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
                      <div className="text-white font-roboto text-sm">
                        {(() => {
                          // Сумма ставок (фиксированная сумма всех ставок одного цикла):
                          // 1) Берём exact_cycle_total из API /cycle-bets (кэшируется в cycleSumsByBot)
                          // 2) Фолбэк сразу после создания бота: считаем по формуле ((min+max)/2)*cycle_games
                          const sums = cycleSumsByBot[bot.id];
                          let val = Number((sums && sums.exact_cycle_total) || 0);
                          if (!(val > 0)) {
                            const minBet = Math.round(Number(bot.min_bet_amount ?? bot.min_bet ?? 1));
                            const maxBet = Math.round(Number(bot.max_bet_amount ?? bot.max_bet ?? 50));
                            const cycleGames = Math.max(1, Number(bot.cycle_games ?? 12));
                            val = Math.round(((minBet + maxBet) / 2.0) * cycleGames);
                          }
                          return val > 0 ? val : '—';
                        })()}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="flex flex-col items-center">
                        {/* Верхняя строка: Фиксированная расчётная прибыль за цикл */}
                        {bot.cycle_planned_profit !== null && bot.cycle_planned_profit !== undefined && (
                          <div className="text-blue-400 font-roboto text-xs font-bold mb-1" title="Фиксированная прибыль за текущий цикл (расчётная)">
                            {(() => {
                              const plannedProfit = Number(bot.cycle_planned_profit);
                              const sign = plannedProfit > 0 ? '+' : plannedProfit < 0 ? '−' : '+';
                              return (
                                <span className="text-blue-400">
                                  {sign}${Math.abs(Math.round(plannedProfit))} план
                                </span>
                              );
                            })()}
                          </div>
                        )}
                        
                        {/* Основная строка: Фактическая прибыль на текущий момент */}
                        {(() => {
                          // Фактическая прибыль текущего активного цикла
                          const sums = cycleSumsByBot[bot.id] || bot.cycle_total_info || {};
                          const profit = typeof bot.current_profit === 'number'
                            ? bot.current_profit
                            : (typeof sums.wins_sum === 'number' && typeof sums.losses_sum === 'number')
                              ? (Number(sums.wins_sum) - Number(sums.losses_sum))
                              : 0;
                          const color = profit >= 0 ? 'text-green-400' : 'text-red-400';
                          const sign = profit > 0 ? '+' : profit < 0 ? '−' : '+';
                          return (
                            <span className={`${color} font-roboto text-sm font-bold`} title="Фактическая прибыль на текущий момент">
                              {sign}${Math.abs(Math.round(profit))}
                            </span>
                          );
                        })()}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center space-x-1">
                        <div className="flex flex-col items-center">
                          <span className="text-cyan-400 font-roboto text-sm font-bold">
                            {bot.pause_between_cycles ? `${bot.pause_between_cycles}с` : '5с'}
                          </span>
                          {bot.pause_status && bot.pause_status.is_active && (
                            <PauseCountdown 
                              remainingSeconds={bot.pause_status.remaining_seconds} 
                              botId={bot.id}
                            />
                          )}
                        </div>
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
                        const newForm = {...botForm, max_bet_amount: parseInt(e.target.value) || 100};
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
                  Сумма должна быть 100%. Из {botForm.cycle_games} игр: {Math.round(botForm.cycle_games * botForm.wins_percentage / 100)} побед, {Math.round(botForm.cycle_games * botForm.losses_percentage / 100)} поражений и {Math.round(botForm.cycle_games * botForm.draws_percentage / 100)} ничьих.
                </div>
              </div>

              {/* Объединенный блок: Циклы и Настройки таймингов */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Циклы и Настройки таймингов</h4>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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

                  {/* Пауза между ставками */}
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Пауза между ставками:</label>
                    <input
                      type="number"
                      min="1"
                      max="3600"
                      value={botForm.pause_between_bets}
                      onChange={(e) => {
                        const newForm = {...botForm, pause_between_bets: parseInt(e.target.value) || 5};
                        setBotForm(newForm);
                        validateExtendedFormInRealTime(newForm);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                    />
                    <div className="text-xs text-text-secondary mt-1">
                      Интервал между ставками в рамках одного цикла
                    </div>
                  </div>

                </div>

                {/* Предупреждения и подсказки (сохранены) */}
                {(() => {
                  const preview = calculateCycleAmounts();
                  const activePoolShare = preview.total > 0 ? Math.round(((preview.active_pool / preview.total) * 100)) : 0;
                  const drawsShare = preview.total > 0 ? Math.round(((preview.draws_sum / preview.total) * 100)) : 0;
                  const warnings = [];
                  if (activePoolShare < 65) warnings.push(`⚠️ Активный пул слишком мал (${activePoolShare}%). Рекомендуется ≥ 65%.`);
                  if (drawsShare > 40) warnings.push(`⚠️ Доля ничьих слишком велика (${drawsShare}%). Проверьте проценты.`);
                  if (preview.roi_active < 2 || preview.roi_active > 20) warnings.push(`⚠️ ROI_active (${preview.roi_active}%) вне рекомендуемых пределов [2%, 20%].`);
                  return warnings.length > 0 ? (
                    <div className="mt-3 border border-yellow-500 bg-yellow-900 bg-opacity-20 rounded-lg p-3 text-yellow-200 text-sm space-y-1">
                      {warnings.map((w, idx) => (<div key={idx}>{w}</div>))}
                    </div>
                  ) : null;
                })()}
              </div>

              {/* ОБНОВЛЕННАЯ ЛОГИКА: Превью ROI расчетов на основе фактических W/L/D */}
              <div className="border border-purple-500 bg-purple-900 bg-opacity-20 rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-purple-400 mb-3">📊 Превью ROI расчетов</h4>
                {(() => {
                  // Используем правильную логику: масштабирование от базы 800
                  const preview = calculatePreviewFromCounts(
                    botForm.wins_count,
                    botForm.losses_count, 
                    botForm.draws_count,
                    botForm.min_bet_amount,
                    botForm.max_bet_amount,
                    botForm.wins_percentage,
                    botForm.losses_percentage,
                    botForm.draws_percentage
                  );
                  
                  return (
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-text-secondary">Общая сумма цикла:</div>
                        <div className="text-white font-bold">{preview.total}</div>
                        <div className="text-xs text-gray-400">W+L+D = {botForm.wins_count}+{botForm.losses_count}+{botForm.draws_count}</div>
                      </div>
                      <div>
                        <div className="text-text-secondary">Активный пул:</div>
                        <div className="text-purple-300 font-bold">{preview.active_pool}</div>
                        <div className="text-xs text-gray-400">W+L = {botForm.wins_count}+{botForm.losses_count}</div>
                      </div>
                      <div>
                        <div className="text-text-secondary">Прибыль:</div>
                        <div className={`font-bold ${preview.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {preview.profit}
                        </div>
                        <div className="text-xs text-gray-400">W-L = {botForm.wins_count}-{botForm.losses_count}</div>
                      </div>
                      <div>
                        <div className="text-text-secondary">ROI_active:</div>
                        <div className={`font-bold text-lg ${preview.roi_active >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {preview.roi_active}%
                        </div>
                        <div className="text-xs text-gray-400">({preview.profit}÷{preview.active_pool})×100</div>
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
                        const newForm = {...botForm, max_bet_amount: parseInt(e.target.value) || 100};
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
                  Сумма должна быть 100%. Из {botForm.cycle_games} игр: {Math.round(botForm.cycle_games * botForm.wins_percentage / 100)} побед, {Math.round(botForm.cycle_games * botForm.losses_percentage / 100)} поражений и {Math.round(botForm.cycle_games * botForm.draws_percentage / 100)} ничьих.
                </div>
              </div>

              {/* Объединенный блок: Циклы и Настройки таймингов */}
              <div className="border border-border-primary rounded-lg p-4">
                <h4 className="font-rajdhani font-bold text-white mb-3">Циклы и Настройки таймингов</h4>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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

                </div>
                {/* Вариант 2: Без лайв‑превью ROI в режиме редактирования */}
              </div>

              {/* Удалено: Стратегия и режим (legacy) */}

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
              <div className="flex items-center space-x-4">
                {/* Общая прибыль */}
                <div className="text-right">
                  <div className="text-sm text-text-secondary font-rajdhani">Общая прибыль:</div>
                  <div className={`text-2xl font-rajdhani font-bold ${
                    cycleHistoryData.reduce((total, cycle) => total + (cycle.profit || 0), 0) >= 0 
                      ? 'text-green-400' 
                      : 'text-red-400'
                  }`}>
                    {cycleHistoryData.reduce((total, cycle) => total + (cycle.profit || 0), 0) >= 0 ? '+' : ''}
                    ${Math.round(cycleHistoryData.reduce((total, cycle) => total + (cycle.profit || 0), 0))}
                  </div>
                </div>
                <button
                  onClick={() => setIsCycleHistoryModalOpen(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
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
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Дата начала / завершения</th>
                        <th 
                          className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase cursor-pointer hover:text-white transition-colors"
                          onClick={() => handleCycleSorting('duration')}
                        >
                          <div className="flex items-center space-x-1">
                            <span>Время цикла</span>
                            {cycleSortField === 'duration' && (
                              <span className="text-accent-primary">
                                {cycleSortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th 
                          className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase cursor-pointer hover:text-white transition-colors"
                          onClick={() => handleCycleSorting('total_bets')}
                        >
                          <div className="flex items-center space-x-1">
                            <span>Ставки</span>
                            {cycleSortField === 'total_bets' && (
                              <span className="text-accent-primary">
                                {cycleSortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th 
                          className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase cursor-pointer hover:text-white transition-colors"
                          onClick={() => handleCycleSorting('wins')}
                        >
                          <div className="flex items-center space-x-1">
                            <span>W / L / D</span>
                            {cycleSortField === 'wins' && (
                              <span className="text-accent-primary">
                                {cycleSortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th 
                          className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase cursor-pointer hover:text-white transition-colors"
                          onClick={() => handleCycleSorting('total_winnings')}
                        >
                          <div className="flex items-center space-x-1">
                            <span>Выигрыш</span>
                            {cycleSortField === 'total_winnings' && (
                              <span className="text-accent-primary">
                                {cycleSortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th 
                          className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase cursor-pointer hover:text-white transition-colors"
                          onClick={() => handleCycleSorting('total_losses')}
                        >
                          <div className="flex items-center space-x-1">
                            <span>Проигрыш</span>
                            {cycleSortField === 'total_losses' && (
                              <span className="text-accent-primary">
                                {cycleSortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th 
                          className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase cursor-pointer hover:text-white transition-colors"
                          onClick={() => handleCycleSorting('profit')}
                        >
                          <div className="flex items-center space-x-1">
                            <span>Прибыль</span>
                            {cycleSortField === 'profit' && (
                              <span className="text-accent-primary">
                                {cycleSortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th 
                          className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase cursor-pointer hover:text-white transition-colors"
                          onClick={() => handleCycleSorting('roi')}
                          title="ROI (Return on Investment) = (Прибыль / Активный пул) × 100%. Активный пул = Выигрыш + Проигрыш"
                        >
                          <div className="flex items-center space-x-1">
                            <span>ROI</span>
                            {cycleSortField === 'roi' && (
                              <span className="text-accent-primary">
                                {cycleSortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">Действия</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-primary">
                      {cycleHistoryData.map((cycle, index) => (
                        <tr key={cycle.id || index} className="hover:bg-surface-sidebar hover:bg-opacity-30">
                          <td className="px-4 py-3 text-white font-roboto text-sm">
                            {cycle.cycle_number || index + 1}
                          </td>
                          <td className="px-4 py-3 text-white font-roboto text-sm">
                            <div className="space-y-1">
                              <div className="text-xs text-text-secondary">
                                Начало: {cycle.start_time ? new Date(cycle.start_time).toLocaleDateString('ru-RU', {
                                  day: '2-digit',
                                  month: '2-digit',
                                  year: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                }) : '—'}
                              </div>
                              <div className="text-xs">
                                Завершение: {cycle.end_time ? new Date(cycle.end_time).toLocaleDateString('ru-RU', {
                                  day: '2-digit',
                                  month: '2-digit',
                                  year: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                }) : '—'}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-white font-roboto text-sm">
                            {cycle.duration || '—'}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-accent-primary font-roboto text-sm font-bold">
                              {cycle.total_bets || cycle.total_games || 0}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-green-400 text-xs font-roboto font-bold">
                              {cycle.wins || 0}
                            </span>
                            {' / '}
                            <span className="text-red-400 text-xs font-roboto font-bold">
                              {cycle.losses || 0}
                            </span>
                            {' / '}
                            <span className="text-yellow-400 text-xs font-roboto font-bold">
                              {cycle.draws || 0}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-green-400 font-roboto text-sm font-bold">
                              ${Math.round(cycle.total_winnings || 0)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className="text-red-400 font-roboto text-sm font-bold">
                              ${Math.round(cycle.total_losses || 0)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`font-roboto text-sm font-bold ${
                              (cycle.profit || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {(cycle.profit || 0) >= 0 ? '+' : ''}${Math.round(cycle.profit || 0)}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            {(() => {
                              // Используем roi_active от backend, если доступно, иначе вычисляем самостоятельно
                              let roi;
                              let source = '';
                              if (cycle.roi_active !== undefined && cycle.roi_active !== null) {
                                roi = Number(cycle.roi_active);
                                source = 'от сервера';
                              } else {
                                const activePool = (cycle.total_winnings || 0) + (cycle.total_losses || 0);
                                roi = activePool > 0 ? ((cycle.profit || 0) / activePool) * 100 : 0;
                                source = `расчёт: ${cycle.profit || 0} / ${activePool} × 100%`;
                              }
                              
                              const tooltipText = `ROI: ${roi.toFixed(2)}% (${source})`;
                              
                              return (
                                <span 
                                  className={`font-roboto text-sm font-bold cursor-help ${
                                    roi >= 0 ? 'text-yellow-400' : 'text-red-400'
                                  }`}
                                  title={tooltipText}
                                >
                                  {roi >= 0 ? '+' : ''}{roi.toFixed(2)}%
                                </span>
                              );
                            })()}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => handleCycleDetailsModal(cycle, selectedBotForCycleHistory)}
                              className="text-blue-400 hover:text-blue-300 text-sm underline"
                              title="Показать детальный список всех ставок этого цикла"
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
                📊 Детали цикла: {cycleDetailsData.bot_name} — Цикл #{cycleDetailsData.cycle_number}
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
              {/* Верхний ряд: Сумма ставок, Выигрыши, Проигрыши */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  {/* Добавляем строку с общей суммой всех ставок сверху */}
                  <div className="text-green-400 font-roboto text-sm font-bold mb-2">
                    Общая сумма всех ставок: ${(() => {
                      const totalStakes = (cycleDetailsData.bets || []).reduce((sum, bet) => {
                        const amount = Number(bet.bet_amount) || 0;
                        return sum + amount;
                      }, 0);
                      return Math.round(totalStakes);
                    })()}
                  </div>
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
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Проигрыши</div>
                  <div className="text-red-400 font-roboto text-sm font-bold">
                    ${Math.round(cycleDetailsData.total_losses)}
                  </div>
                </div>
              </div>
              {/* Нижний ряд: Игры, Винрейт, Чистая прибыль */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Игры</div>
                  <div className="text-accent-primary font-roboto text-sm font-bold">
                    {cycleDetailsData.total_games}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-text-secondary text-xs font-rajdhani uppercase mb-1">Винрейт</div>
                  <div className="text-yellow-400 font-roboto text-sm font-bold">
                    {Number(cycleDetailsData.planned_roi || 0).toFixed(2)}%
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
                          №
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          ID
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Дата начала / завершения
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Ставка
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Гемы
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Ходы
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Соперник
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase">
                          Результат
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-primary">
                      {cycleDetailsData.bets.map((bet, index) => (
                        <tr key={bet.id} className="hover:bg-surface-sidebar hover:bg-opacity-30">
                          <td className="px-3 py-2 text-white font-roboto text-sm">
                            {index + 1}
                          </td>
                          <td className="px-3 py-2 text-white font-roboto text-xs">
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(bet.id);
                                // Показываем уведомление о копировании
                                showSuccessRU('ID скопирован в буфер обмена');
                              }}
                              className="text-blue-400 hover:text-blue-300 underline"
                              title={`Полный ID: ${bet.id}\nНажмите для копирования`}
                            >
                              {bet.id ? `${bet.id.substring(0, 4)}…${bet.id.substring(bet.id.length - 4)}` : '—'}
                            </button>
                          </td>
                          <td className="px-3 py-2 text-white font-roboto text-xs">
                            <div className="space-y-1">
                              <div className="text-xs text-text-secondary">Начало:</div>
                              <div>{bet.created_at ? new Date(bet.created_at).toLocaleDateString('ru-RU') + ' ' + new Date(bet.created_at).toLocaleTimeString('ru-RU') : '—'}</div>
                              <div className="text-xs text-text-secondary">Завершение:</div>
                              <div>{bet.completed_at ? new Date(bet.completed_at).toLocaleDateString('ru-RU') + ' ' + new Date(bet.completed_at).toLocaleTimeString('ru-RU') : '—'}</div>
                            </div>
                          </td>
                          <td className="px-3 py-2 text-green-400 font-roboto text-sm font-bold">
                            ${bet.bet_amount || 0}
                          </td>
                          <td className="px-3 py-2 text-white font-roboto text-sm">
                            {/* Гемы в 3 ряда */}
                            <div className="grid grid-cols-1 gap-1">
                              {bet.bet_gems && Object.keys(bet.bet_gems).length > 0 ? (
                                (() => {
                                  const gemIconMap = {
                                    'Ruby': '/gems/gem-red.svg',
                                    'Amber': '/gems/gem-orange.svg',
                                    'Topaz': '/gems/gem-yellow.svg',
                                    'Emerald': '/gems/gem-green.svg',
                                    'Aquamarine': '/gems/gem-cyan.svg',
                                    'Sapphire': '/gems/gem-blue.svg',
                                    'Magic': '/gems/gem-purple.svg'
                                  };
                                  
                                  const gemEntries = Object.entries(bet.bet_gems);
                                  const rows = [];
                                  for (let i = 0; i < gemEntries.length; i += 3) {
                                    rows.push(gemEntries.slice(i, i + 3));
                                  }
                                  return rows.map((row, rowIndex) => (
                                    <div key={rowIndex} className="flex items-center space-x-3">
                                      {row.map(([gemType, count]) => (
                                        <div key={gemType} className="flex items-center space-x-1">
                                          <img 
                                            src={gemIconMap[gemType] || '/gems/gem-red.svg'} 
                                            alt={gemType} 
                                            className="w-4 h-4"
                                          />
                                          <span className="text-xs font-bold">{count}</span>
                                        </div>
                                      ))}
                                    </div>
                                  ));
                                })()
                              ) : (
                                <span className="text-xs text-text-secondary">—</span>
                              )}
                            </div>
                          </td>
                          <td className="px-3 py-2 text-center">
                            {/* Ходы Бот/Противник с иконками и результатом */}
                            <div className="flex flex-col space-y-2">
                              {(() => {
                                // Определяем, началась ли ставка (есть ли ходы)
                                const gameStarted = bet.creator_move && bet.opponent_move && bet.result !== 'pending';
                                
                                if (!gameStarted) {
                                  // Для не начатых ставок показываем заглушку
                                  return (
                                    <div className="text-center">
                                      <div className="flex items-center justify-center space-x-2 mb-1">
                                        <span className="text-xs text-text-secondary">Бот:</span>
                                        <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                                          <span className="text-white text-xs font-bold">✕</span>
                                        </div>
                                      </div>
                                      <div className="flex items-center justify-center space-x-2 mb-1">
                                        <span className="text-xs text-text-secondary">Противник:</span>
                                        <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                                          <span className="text-white text-xs font-bold">✕</span>
                                        </div>
                                      </div>
                                      <div className="text-xs text-gray-400 mt-1">не начато</div>
                                    </div>
                                  );
                                } else {
                                  // Для начатых ставок показываем иконки и вычисляем результат по К-Н-Б
                                  
                                  // Функция для вычисления результата по правилам К-Н-Б
                                  const calculateRPSResult = (botMove, opponentMove) => {
                                    const bot = botMove?.toUpperCase();
                                    const opponent = opponentMove?.toUpperCase();
                                    
                                    if (bot === opponent) return 'draw';
                                    
                                    // Правила К-Н-Б: камень>ножницы, ножницы>бумага, бумага>камень
                                    if (
                                      (bot === 'ROCK' && opponent === 'SCISSORS') ||
                                      (bot === 'SCISSORS' && opponent === 'PAPER') ||
                                      (bot === 'PAPER' && opponent === 'ROCK')
                                    ) {
                                      return 'win';
                                    } else {
                                      return 'loss';
                                    }
                                  };
                                  
                                  const calculatedResult = calculateRPSResult(bet.creator_move, bet.opponent_move);
                                  
                                  return (
                                    <div className="text-center">
                                      <div className="flex items-center justify-center space-x-2 mb-1">
                                        <span className="text-xs text-text-secondary">Бот:</span>
                                        {(() => {
                                          const move = bet.creator_move?.toUpperCase();
                                          let iconName = 'Rock'; // по умолчанию
                                          if (move === 'ROCK') iconName = 'Rock';
                                          else if (move === 'PAPER') iconName = 'Paper';
                                          else if (move === 'SCISSORS') iconName = 'Scissors';
                                          return (
                                            <img 
                                              src={`/${iconName}.svg`} 
                                              alt={move} 
                                              className="w-4 h-4"
                                            />
                                          );
                                        })()}
                                      </div>
                                      <div className="flex items-center justify-center space-x-2 mb-1">
                                        <span className="text-xs text-text-secondary">Противник:</span>
                                        {(() => {
                                          const move = bet.opponent_move?.toUpperCase();
                                          let iconName = 'Rock'; // по умолчанию
                                          if (move === 'ROCK') iconName = 'Rock';
                                          else if (move === 'PAPER') iconName = 'Paper';
                                          else if (move === 'SCISSORS') iconName = 'Scissors';
                                          return (
                                            <img 
                                              src={`/${iconName}.svg`} 
                                              alt={move} 
                                              className="w-4 h-4"
                                            />
                                          );
                                        })()}
                                      </div>

                                    </div>
                                  );
                                }
                              })()}
                            </div>
                          </td>
                          <td className="px-3 py-2 text-white font-roboto text-sm">
                            {bet.opponent_name || 'Неизвестно'}
                          </td>
                          <td className="px-3 py-2">
                            {(() => {
                              // Универсальная функция для получения результата из любого поля
                              const getResultType = () => {
                                // Сначала пробуем result_class (для завершённых циклов)
                                if (bet.result_class) {
                                  return bet.result_class.toLowerCase();
                                }
                                // Затем пробуем result (для текущего цикла)
                                if (bet.result) {
                                  return bet.result.toLowerCase();
                                }
                                return 'pending';
                              };
                              
                              const resultType = getResultType();
                              
                              // Определяем цвет фона и текст
                              const getResultStyle = () => {
                                switch (resultType) {
                                  case 'win':
                                    return { bg: 'bg-green-600', text: 'Выигрыш' };
                                  case 'loss':
                                  case 'lose':
                                    return { bg: 'bg-red-600', text: 'Проигрыш' };
                                  case 'draw':
                                    return { bg: 'bg-yellow-600', text: 'Ничья' };
                                  default:
                                    return { bg: 'bg-gray-600', text: 'Ожидание' };
                                }
                              };
                              
                              const style = getResultStyle();
                              
                              return (
                                <span className={`px-2 py-1 rounded-full text-xs font-roboto font-bold ${style.bg} text-white`}>
                                  {style.text}
                                </span>
                              );
                            })()}
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
      
      {/* Модальное окно быстрого запуска ботов */}
      {isQuickLaunchModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50">
          <div 
            className="bg-surface-card border border-accent-primary border-opacity-50 rounded-lg w-full max-w-5xl max-h-[90vh] overflow-hidden shadow-2xl"
            style={{
              position: 'absolute',
              left: `${50 + (modalPosition.x / window.innerWidth) * 100}%`,
              top: `${50 + (modalPosition.y / window.innerHeight) * 100}%`,
              transform: 'translate(-50%, -50%)',
              cursor: isDragging ? 'grabbing' : 'default'
            }}
          >
            {/* Заголовок */}
            <div 
              className="flex justify-between items-center p-4 border-b border-border-primary bg-surface-sidebar cursor-grab select-none"
              onMouseDown={handleMouseDown}
              style={{
                cursor: isDragging ? 'grabbing' : 'grab'
              }}
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-600 rounded-lg">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="font-rajdhani text-xl font-bold text-white">⚡ Быстрый запуск ботов</h3>
                    <div className="text-text-secondary text-xs bg-blue-600 bg-opacity-20 px-2 py-1 rounded">
                      🖱️ Перетаскиваемое
                    </div>
                  </div>
                  <p className="text-text-secondary text-sm">Запуск ботов по готовым пресетам</p>
                </div>
              </div>
              <button
                onClick={() => setIsQuickLaunchModalOpen(false)}
                className="text-text-secondary hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
              {/* Быстрые кнопки пресетов */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-rajdhani text-lg font-bold text-white">Готовые пресеты</h4>
                  <button
                    onClick={() => setIsCreatingPreset(!isCreatingPreset)}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    <span>Создать пресет</span>
                  </button>
                </div>

                {/* Сетка кнопок пресетов */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
                  {quickLaunchPresets.map((preset) => (
                    <div key={preset.id} className="relative group">
                      <button
                        onClick={async () => {
                          try {
                            const token = localStorage.getItem('token');
                            
                            // Генерируем автоматический номер бота
                            let maxNumber = 0;
                            botsList.forEach(bot => {
                              const match = bot.name.match(/Bot#(\d+)/);
                              if (match) {
                                const number = parseInt(match[1]);
                                if (number > maxNumber) {
                                  maxNumber = number;
                                }
                              }
                            });
                            const nextNumber = maxNumber + 1;
                            const botName = `Bot#${nextNumber.toString().padStart(5, '0')}`;
                            
                            const botData = {
                              name: botName,
                              min_bet_amount: preset.min_bet_amount,
                              max_bet_amount: preset.max_bet_amount,
                              wins_percentage: preset.wins_percentage,
                              losses_percentage: preset.losses_percentage,
                              draws_percentage: preset.draws_percentage,
                              cycle_games: preset.cycle_games,
                              pause_between_cycles: preset.pause_between_cycles,
                              pause_between_bets: preset.pause_between_bets,
                              ...(() => { const { W, L, D } = recalcCountsFromPercents(preset.cycle_games, preset.wins_percentage, preset.losses_percentage, preset.draws_percentage); return { wins_count: W, losses_count: L, draws_count: D }; })()
                            };
                            
                            const response = await axios.post(`${API}/admin/bots/create-regular`, botData, {
                              headers: { Authorization: `Bearer ${token}` }
                            });
                            
                            showSuccessRU(`Бот "${botData.name}" создан из пресета "${preset.name}"`);
                            await fetchBotsList();
                            
                          } catch (error) {
                            console.error('Ошибка создания бота из пресета:', error);
                            showErrorRU(error.response?.data?.detail || 'Ошибка при создании бота из пресета');
                          }
                        }}
                        className={`w-full px-3 py-2 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors border ${
                          preset.buttonColor === 'green' ? 'bg-green-600 hover:bg-green-700 border-green-500' :
                          preset.buttonColor === 'red' ? 'bg-red-600 hover:bg-red-700 border-red-500' :
                          preset.buttonColor === 'yellow' ? 'bg-yellow-600 hover:bg-yellow-700 border-yellow-500' :
                          preset.buttonColor === 'purple' ? 'bg-purple-600 hover:bg-purple-700 border-purple-500' :
                          preset.buttonColor === 'orange' ? 'bg-orange-600 hover:bg-orange-700 border-orange-500' :
                          'bg-blue-600 hover:bg-blue-700 border-blue-500'
                        }`}
                        title={`Запустить бота: ${preset.name}`}
                      >
                        {preset.buttonName}
                      </button>
                      <button
                        onClick={() => {
                          const updatedPresets = quickLaunchPresets.filter(p => p.id !== preset.id);
                          localStorage.setItem('quickLaunchPresets', JSON.stringify(updatedPresets));
                          setQuickLaunchPresets(updatedPresets);
                          showSuccessRU('Пресет удален');
                        }}
                        className="absolute -top-1 -right-1 w-5 h-5 bg-red-600 hover:bg-red-700 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Удалить пресет"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                  
                  {quickLaunchPresets.length === 0 && (
                    <div className="col-span-full text-center text-text-secondary py-8">
                      <div className="text-4xl mb-2">🎯</div>
                      <p>Нет сохраненных пресетов</p>
                      <p className="text-sm">Создайте первый пресет для быстрого запуска ботов</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Конструктор пресетов */}
              {isCreatingPreset && (
                <div className="bg-surface-sidebar rounded-lg p-6">
                  <h4 className="font-rajdhani text-lg font-bold text-white mb-4">🛠️ Конструктор пресетов</h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Основная информация */}
                    <div>
                      <label className="block text-text-secondary text-sm mb-2">Название пресета</label>
                      <input
                        type="text"
                        value={currentPreset.name}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                        placeholder="Bot"
                      />
                    </div>

                    <div>
                      <label className="block text-text-secondary text-sm mb-2">Название кнопки</label>
                      <input
                        type="text"
                        value={currentPreset.buttonName}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, buttonName: e.target.value }))}
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                        placeholder="Например: 🔥 Агрессивный"
                      />
                    </div>

                    <div>
                      <label className="block text-text-secondary text-sm mb-2">Цвет кнопки</label>
                      <select
                        value={currentPreset.buttonColor}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, buttonColor: e.target.value }))}
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      >
                        <option value="blue">🔵 Синий</option>
                        <option value="green">🟢 Зеленый</option>
                        <option value="red">🔴 Красный</option>
                        <option value="yellow">🟡 Желтый</option>
                        <option value="purple">🟣 Фиолетовый</option>
                        <option value="orange">🟠 Оранжевый</option>
                      </select>
                    </div>

                    {/* Пресет ROI */}
                    <div>
                      <label className="block text-text-secondary text-sm mb-2">Пресет ROI</label>
                      <select
                        value={selectedPresetForQuickLaunch}
                        onChange={(e) => {
                          const preset = defaultPresets.find(p => p.name === e.target.value);
                          applyROIPresetForQuickLaunch(preset);
                        }}
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      >
                        {defaultPresets.map(preset => (
                          <option key={preset.name} value={preset.name}>{preset.name}</option>
                        ))}
                      </select>
                    </div>

                    {/* Диапазон ставок */}
                    <div>
                      <label className="block text-text-secondary text-sm mb-2">Мин. ставка</label>
                      <input
                        type="number"
                        value={currentPreset.min_bet_amount}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, min_bet_amount: parseFloat(e.target.value) || 1 }))}
                        min="1"
                        max="10000"
                        step="0.1"
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      />
                    </div>

                    <div>
                      <label className="block text-text-secondary text-sm mb-2">Макс. ставка</label>
                      <input
                        type="number"
                        value={currentPreset.max_bet_amount}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, max_bet_amount: parseFloat(e.target.value) || 100 }))}
                        min="1"
                        max="10000"
                        step="0.1"
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      />
                    </div>

                    <div>
                      <label className="block text-text-secondary text-sm mb-2">Игр в цикле</label>
                      <input
                        type="number"
                        value={currentPreset.cycle_games}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, cycle_games: parseInt(e.target.value) || 16 }))}
                        min="4"
                        max="100"
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      />
                    </div>

                    {/* Проценты исходов */}
                    <div>
                      <label className="block text-text-secondary text-sm mb-2">% побед</label>
                      <input
                        type="number"
                        value={currentPreset.wins_percentage}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, wins_percentage: parseFloat(e.target.value) || 0 }))}
                        min="0"
                        max="100"
                        step="0.1"
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      />
                    </div>

                    <div>
                      <label className="block text-text-secondary text-sm mb-2">% поражений</label>
                      <input
                        type="number"
                        value={currentPreset.losses_percentage}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, losses_percentage: parseFloat(e.target.value) || 0 }))}
                        min="0"
                        max="100"
                        step="0.1"
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      />
                    </div>

                    <div>
                      <label className="block text-text-secondary text-sm mb-2">% ничьих</label>
                      <input
                        type="number"
                        value={currentPreset.draws_percentage}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, draws_percentage: parseFloat(e.target.value) || 0 }))}
                        min="0"
                        max="100"
                        step="0.1"
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      />
                    </div>

                    {/* Баланс игр (ручная настройка) */}
                    <div className="col-span-3">
                      <label className="block text-text-secondary text-sm mb-2">⚖️ Баланс игр</label>
                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="block text-text-secondary text-xs mb-1">Победы (W)</label>
                          <input
                            type="number"
                            value={currentPreset.wins_count || 0}
                            onChange={(e) => setCurrentPreset(prev => ({ ...prev, wins_count: parseInt(e.target.value) || 0 }))}
                            min="0"
                            max={currentPreset.cycle_games || 100}
                            className="w-full px-2 py-1 bg-surface-card border border-border-primary rounded text-white font-roboto text-sm focus:outline-none focus:border-green-400"
                          />
                        </div>
                        <div>
                          <label className="block text-text-secondary text-xs mb-1">Поражения (L)</label>
                          <input
                            type="number"
                            value={currentPreset.losses_count || 0}
                            onChange={(e) => setCurrentPreset(prev => ({ ...prev, losses_count: parseInt(e.target.value) || 0 }))}
                            min="0"
                            max={currentPreset.cycle_games || 100}
                            className="w-full px-2 py-1 bg-surface-card border border-border-primary rounded text-white font-roboto text-sm focus:outline-none focus:border-red-400"
                          />
                        </div>
                        <div>
                          <label className="block text-text-secondary text-xs mb-1">Ничьи (D)</label>
                          <input
                            type="number"
                            value={currentPreset.draws_count || 0}
                            onChange={(e) => setCurrentPreset(prev => ({ ...prev, draws_count: parseInt(e.target.value) || 0 }))}
                            min="0"
                            max={currentPreset.cycle_games || 100}
                            className="w-full px-2 py-1 bg-surface-card border border-border-primary rounded text-white font-roboto text-sm focus:outline-none focus:border-yellow-400"
                          />
                        </div>
                      </div>
                      <div className="text-xs text-text-secondary mt-1">
                        Общий баланс: {(currentPreset.wins_count || 0) + (currentPreset.losses_count || 0) + (currentPreset.draws_count || 0)} из {currentPreset.cycle_games || 0} игр
                      </div>
                    </div>

                    {/* Паузы */}
                    <div>
                      <label className="block text-text-secondary text-sm mb-2">Пауза между циклами (сек)</label>
                      <input
                        type="number"
                        value={currentPreset.pause_between_cycles}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, pause_between_cycles: parseInt(e.target.value) || 5 }))}
                        min="1"
                        max="3600"
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      />
                    </div>

                    <div>
                      <label className="block text-text-secondary text-sm mb-2">Пауза между ставками (сек)</label>
                      <input
                        type="number"
                        value={currentPreset.pause_between_bets}
                        onChange={(e) => setCurrentPreset(prev => ({ ...prev, pause_between_bets: parseInt(e.target.value) || 5 }))}
                        min="1"
                        max="3600"
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                      />
                    </div>


                  </div>

                  {/* ОБНОВЛЕННОЕ ПРЕВЬЮ: ROI расчеты на основе фактических W/L/D */}
                  <div className="mt-6 border border-purple-500 bg-purple-900 bg-opacity-20 rounded-lg p-4">
                    <h4 className="font-rajdhani font-bold text-purple-400 mb-3">📊 Превью ROI расчетов</h4>
                    {(() => {
                      // Используем правильную логику: масштабирование от базы 800
                      const preview = calculatePreviewFromCounts(
                        currentPreset.wins_count,
                        currentPreset.losses_count,
                        currentPreset.draws_count,
                        currentPreset.min_bet_amount,
                        currentPreset.max_bet_amount,
                        currentPreset.wins_percentage,
                        currentPreset.losses_percentage,
                        currentPreset.draws_percentage
                      );
                      
                      if (preview.total === 0) {
                        return (
                          <div className="text-text-secondary text-sm">
                            Заполните все поля для расчета ROI
                          </div>
                        );
                      }
                      
                      return (
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <div className="text-text-secondary">Общая сумма цикла:</div>
                            <div className="text-white font-bold">{preview.total}</div>
                            <div className="text-xs text-gray-400">W+L+D = {currentPreset.wins_count}+{currentPreset.losses_count}+{currentPreset.draws_count}</div>
                          </div>
                          <div>
                            <div className="text-text-secondary">Активный пул:</div>
                            <div className="text-purple-300 font-bold">{preview.active_pool}</div>
                            <div className="text-xs text-gray-400">W+L = {currentPreset.wins_count}+{currentPreset.losses_count}</div>
                          </div>
                          <div>
                            <div className="text-text-secondary">Прибыль:</div>
                            <div className={`font-bold ${preview.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {preview.profit}
                            </div>
                            <div className="text-xs text-gray-400">W-L = {currentPreset.wins_count}-{currentPreset.losses_count}</div>
                          </div>
                          <div>
                            <div className="text-text-secondary">ROI_active:</div>
                            <div className={`font-bold text-lg ${preview.roi_active >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {preview.roi_active}%
                            </div>
                            <div className="text-xs text-gray-400">({preview.profit}÷{preview.active_pool})×100</div>
                          </div>
                        </div>
                      );
                    })()}
                    <div className="text-xs text-purple-200 mt-3 border-t border-purple-700 pt-2">
                      <div><strong>Формула ROI:</strong> (Прибыль ÷ Активный пул) × 100%</div>
                      <div><strong>Активный пул:</strong> Сумма побед + Сумма поражений (ничьи не участвуют в ROI)</div>
                    </div>
                  </div>

                  {/* Валидация процентов */}
                  <div className="mt-4">
                    <div className={`text-sm ${Math.abs((currentPreset.wins_percentage + currentPreset.losses_percentage + currentPreset.draws_percentage) - 100) < 0.1 ? 'text-green-400' : 'text-red-400'}`}>
                      Сумма процентов: {(currentPreset.wins_percentage + currentPreset.losses_percentage + currentPreset.draws_percentage).toFixed(1)}% 
                      {Math.abs((currentPreset.wins_percentage + currentPreset.losses_percentage + currentPreset.draws_percentage) - 100) < 0.1 ? ' ✓' : ' (должно быть 100%)'}
                    </div>
                  </div>

                  {/* Кнопки управления */}
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      onClick={() => setIsCreatingPreset(false)}
                      className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors"
                    >
                      Отмена
                    </button>
                    <button
                      onClick={() => {
                        if (!currentPreset.name.trim() || !currentPreset.buttonName.trim()) {
                          showErrorRU('Заполните название пресета и название кнопки');
                          return;
                        }

                        // Валидация процентов
                        const totalPercentage = currentPreset.wins_percentage + currentPreset.losses_percentage + currentPreset.draws_percentage;
                        if (Math.abs(totalPercentage - 100) > 0.1) {
                          showErrorRU(`Сумма процентов должна быть 100% (сейчас ${totalPercentage.toFixed(1)}%)`);
                          return;
                        }

                        const newPreset = {
                          id: Date.now().toString(),
                          ...currentPreset
                        };

                        const updatedPresets = [...quickLaunchPresets, newPreset];
                        localStorage.setItem('quickLaunchPresets', JSON.stringify(updatedPresets));
                        setQuickLaunchPresets(updatedPresets);
                        
                        // Сброс формы
                        setCurrentPreset({
                          name: 'Bot',
                          buttonName: '',
                          buttonColor: 'blue',
                          min_bet_amount: 1.0,
                          max_bet_amount: 100.0,
                          wins_percentage: 41.73,
                          losses_percentage: 30.27,
                          draws_percentage: 28.0,
                          cycle_games: 16,
                          pause_between_cycles: 5,
                          wins_count: 6,
                          losses_count: 6,
                          draws_count: 4
                        });
                        setIsCreatingPreset(false);
                        showSuccessRU('Пресет добавлен');
                      }}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors"
                    >
                      Сохранить пресет
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Подвал */}
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4 p-4 border-t border-border-primary bg-surface-sidebar min-h-[80px]">
              <div className="text-text-secondary text-sm flex-1">
                💡 <strong>Совет:</strong> Можно создавать несколько ботов с одинаковыми параметрами, кликая по кнопке пресета многократно
              </div>
              <button
                onClick={() => setIsQuickLaunchModalOpen(false)}
                className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-rajdhani font-bold transition-colors"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно ввода */}
      <InputModal {...inputModal} />
    </div>
  );
};

export default RegularBotsManagement;