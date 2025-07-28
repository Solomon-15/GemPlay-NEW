import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import { formatAsGems } from '../utils/economy';
import useConfirmation from '../hooks/useConfirmation';
import useInput from '../hooks/useInput';
import ConfirmationModal from './ConfirmationModal';
import InputModal from './InputModal';
import HumanBotActiveBetsModal from './HumanBotActiveBetsModal';
import HumanBotCommissionModal from './HumanBotCommissionModal';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HumanBotsList = ({ 
  humanBots = [], 
  loading = false, 
  currentPage = 1, 
  totalPages = 1, 
  pageSize = 10,
  priorityFields = true,
  onEditBot, 
  onCreateBot,
  onPageChange,
  onRefresh
}) => {
  const { addNotification } = useNotifications();
  const { confirm, confirmationModal } = useConfirmation();
  const { prompt, inputModal } = useInput();

  // Remove local humanBots state since we now use props
  // const [humanBots, setHumanBots] = useState([]);
  // const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [globalSettings, setGlobalSettings] = useState({}); // Global settings state
  
  // Multiple selection states
  const [selectedBots, setSelectedBots] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);

  // Active bets modal states
  const [isActiveBetsModalOpen, setIsActiveBetsModalOpen] = useState(false);
  const [selectedBotForActiveBets, setSelectedBotForActiveBets] = useState(null);
  const [activeBetsData, setActiveBetsData] = useState(null);
  const [loadingActiveBets, setLoadingActiveBets] = useState(false);
  const [showAllBets, setShowAllBets] = useState(false);
  const [allBetsData, setAllBetsData] = useState(null);
  const [allBetsPage, setAllBetsPage] = useState(1);

  // Commission modal states
  const [isCommissionModalOpen, setIsCommissionModalOpen] = useState(false);
  const [selectedBotForCommission, setSelectedBotForCommission] = useState(null);
  const [commissionData, setCommissionData] = useState(null);
  const [loadingCommission, setLoadingCommission] = useState(false);
  const [commissionPage, setCommissionPage] = useState(1);

  useEffect(() => {
    fetchStats();
    fetchGlobalSettings();
  }, []);

  // Remove local fetchHumanBots function since data comes from props
  // const fetchHumanBots = async () => { ... }

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

  const fetchGlobalSettings = async () => {
    try {
      const response = await executeOperation('/admin/human-bots/settings', 'GET');
      if (response.success !== false) {
        setGlobalSettings(response.settings || {});
      }
    } catch (error) {
      console.error('Ошибка получения глобальных настроек:', error);
    }
  };

  // Helper function to execute API operations
  const executeOperation = async (endpoint, method = 'GET', data = null) => {
    try {
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
        // Handle standard error with detail (might be object with detailed info)
        else if (errorData.detail) {
          if (typeof errorData.detail === 'object') {
            // For structured error responses (like active games info)
            errorMessage = errorData.detail.message || 'Structured error';
            // Store the full error detail for parsing
            const error = new Error(errorMessage);
            error.detailData = errorData.detail;
            throw error;
          } else {
            errorMessage = errorData.detail;
          }
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
      
      addNotification(errorMessage, 'error');
      throw new Error(errorMessage);
    }
  };

  // Multiple selection handlers
  const handleSelectBot = (botId) => {
    const newSelected = new Set(selectedBots);
    if (newSelected.has(botId)) {
      newSelected.delete(botId);
    } else {
      newSelected.add(botId);
    }
    setSelectedBots(newSelected);
    setShowBulkActions(newSelected.size > 0);
    setSelectAll(newSelected.size === humanBots.length && humanBots.length > 0);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedBots(new Set());
      setShowBulkActions(false);
    } else {
      const allBotIds = new Set(humanBots.map(bot => bot.id));
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

  // Bulk actions
  const handleBulkToggleStatus = async (activate) => {
    if (selectedBots.size === 0) return;

    const action = activate ? 'активировать' : 'деактивировать';
    const confirmed = await confirm({
      title: `${activate ? 'Активация' : 'Деактивация'} выбранных Human-ботов`,
      message: `Вы уверены, что хотите ${action} ${selectedBots.size} выбранных Human-ботов?`,
      type: activate ? "success" : "warning"
    });

    if (confirmed) {
      setBulkActionLoading(true);
      try {
        const selectedBotIds = Array.from(selectedBots);
        let successCount = 0;

        for (const botId of selectedBotIds) {
          try {
            await executeOperation(`/admin/human-bots/${botId}/toggle-status`, 'POST');
            successCount++;
          } catch (error) {
            console.error(`Ошибка для бота ${botId}:`, error);
          }
        }

        addNotification(`Успешно ${action} ${successCount} из ${selectedBots.size} Human-ботов`, 'success');
        clearSelection();
        if (onRefresh) onRefresh(); // Use parent refresh function
        await fetchStats();
      } catch (error) {
        console.error('Ошибка массового изменения статуса:', error);
      } finally {
        setBulkActionLoading(false);
      }
    }
  };

  const handleGenderToggle = async (botId, currentGender) => {
    const newGender = currentGender === 'male' ? 'female' : 'male';
    
    try {
      const response = await executeOperation(`/admin/human-bots/${botId}`, 'PUT', {
        gender: newGender
      });
      
      // Trigger global lobby refresh to update avatars in real-time
      const globalRefresh = getGlobalLobbyRefresh();
      globalRefresh.triggerLobbyRefresh();
      
      addNotification(`Пол Human-бота изменен на ${newGender === 'male' ? 'мужской' : 'женский'}`, 'success');
      
      // Use parent refresh function instead of local state update
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Ошибка изменения пола Human-бота:', error);
      addNotification('Ошибка изменения пола Human-бота', 'error');
    }
  };

  const handleBetLimitAmountChange = async (bot, newAmount) => {
    if (isNaN(newAmount) || newAmount < 1 || newAmount > 100000) {
      addNotification('Ограничение должно быть от 1 до 100000', 'error');
      return;
    }

    try {
      const response = await executeOperation(`/admin/human-bots/${bot.id}`, 'PUT', {
        bet_limit_amount: newAmount
      });
      
      // Update local state
      setHumanBots(prevBots => 
        prevBots.map(b => 
          b.id === bot.id ? { ...b, bet_limit_amount: newAmount } : b
        )
      );
      
      addNotification(`Ограничение Human-бота "${bot.name}" изменено на ${newAmount}`, 'success');
    } catch (error) {
      console.error('Ошибка изменения ограничения Human-бота:', error);
      addNotification('Ошибка изменения ограничения Human-бота', 'error');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedBots.size === 0) return;

    const confirmed = await confirm({
      title: 'Удаление выбранных Human-ботов',
      message: `Вы уверены, что хотите удалить ${selectedBots.size} выбранных Human-ботов? Это действие необратимо!`,
      type: "danger"
    });

    if (confirmed) {
      setBulkActionLoading(true);
      try {
        const selectedBotIds = Array.from(selectedBots);
        let successCount = 0;
        let forceDeleteNeeded = [];
        
        // First pass - try normal delete for all bots
        for (const botId of selectedBotIds) {
          try {
            await executeOperation(`/admin/human-bots/${botId}`, 'DELETE');
            successCount++;
          } catch (error) {
            console.error(`Ошибка удаления бота ${botId}:`, error);
            
            // Check if this bot has active games
            if (error.detailData && error.detailData.force_delete_required) {
              const bot = humanBots.find(b => b.id === botId);
              forceDeleteNeeded.push({
                bot,
                errorInfo: error.detailData
              });
            } else if (error.message.includes('Cannot delete bot with active games')) {
              const bot = humanBots.find(b => b.id === botId);
              forceDeleteNeeded.push({
                bot,
                errorInfo: {
                  active_games_count: 'неизвестно',
                  total_frozen_balance: 0,
                  games: []
                }
              });
            }
          }
        }

        // If some bots need force delete, ask for confirmation
        if (forceDeleteNeeded.length > 0) {
          const totalActiveGames = forceDeleteNeeded.reduce((sum, item) => 
            sum + (typeof item.errorInfo.active_games_count === 'number' ? item.errorInfo.active_games_count : 0), 0
          );
          const totalFrozenBalance = forceDeleteNeeded.reduce((sum, item) => 
            sum + (item.errorInfo.total_frozen_balance || 0), 0
          );

          const forceConfirmed = await confirm({
            title: `⚠️ Принудительное удаление ботов с активными играми`,
            message: (
              <div className="text-left">
                <p className="mb-3">
                  <strong>{forceDeleteNeeded.length} ботов</strong> имеют активные игры:
                </p>
                <div className="bg-yellow-100 border border-yellow-400 rounded p-3 mb-3 text-sm">
                  <div><strong>Общее количество активных игр:</strong> {totalActiveGames}</div>
                  <div><strong>Общая сумма заморожена:</strong> ${totalFrozenBalance.toFixed(2)}</div>
                </div>
                <div className="mb-3 max-h-32 overflow-y-auto text-xs">
                  {forceDeleteNeeded.map((item, index) => (
                    <div key={index} className="border-b py-1">
                      <strong>{item.bot?.name}:</strong> {item.errorInfo.active_games_count} активных игр
                    </div>
                  ))}
                </div>
                <p className="text-sm text-red-600 font-semibold mb-2">
                  ⚠️ При принудительном удалении все активные игры будут отменены, 
                  а средства возвращены игрокам.
                </p>
                <p className="text-sm">
                  Продолжить принудительное удаление {forceDeleteNeeded.length} ботов?
                </p>
              </div>
            ),
            type: "danger"
          });

          if (forceConfirmed) {
            // Force delete the remaining bots
            for (const item of forceDeleteNeeded) {
              try {
                await executeOperation(`/admin/human-bots/${item.bot.id}?force_delete=true`, 'DELETE');
                successCount++;
              } catch (forceError) {
                console.error(`Ошибка принудительного удаления бота ${item.bot.id}:`, forceError);
              }
            }
          }
        }

        addNotification(`Успешно удалено ${successCount} из ${selectedBots.size} Human-ботов`, 'success');
        clearSelection();
        await fetchHumanBots();
        await fetchStats();
      } catch (error) {
        console.error('Ошибка массового удаления:', error);
      } finally {
        setBulkActionLoading(false);
      }
    }
  };

  // Active bets modal handlers
  const handleActiveBetsModal = async (bot) => {
    setSelectedBotForActiveBets(bot);
    setIsActiveBetsModalOpen(true);
    setLoadingActiveBets(true);
    setShowAllBets(false);
    
    try {
      const response = await executeOperation(`/admin/human-bots/${bot.id}/active-bets`, 'GET');
      setActiveBetsData(response);
    } catch (error) {
      console.error('Ошибка получения активных ставок:', error);
      setActiveBetsData(null);
    } finally {
      setLoadingActiveBets(false);
    }
  };

  const handleCommissionModal = async (bot) => {
    setSelectedBotForCommission(bot);
    setIsCommissionModalOpen(true);
    setLoadingCommission(true);
    setCommissionPage(1);
    
    try {
      const response = await executeOperation(`/admin/human-bots/${bot.id}/commission-details?page=1&limit=50`, 'GET');
      setCommissionData(response);
    } catch (error) {
      console.error('Ошибка получения данных комиссий:', error);
      setCommissionData(null);
    } finally {
      setLoadingCommission(false);
    }
  };

  const handleCommissionPageChange = async (page) => {
    if (!selectedBotForCommission || page < 1) return;
    
    setCommissionPage(page);
    setLoadingCommission(true);
    
    try {
      const response = await executeOperation(`/admin/human-bots/${selectedBotForCommission.id}/commission-details?page=${page}&limit=50`, 'GET');
      setCommissionData(response);
    } catch (error) {
      console.error('Ошибка получения данных комиссий:', error);
      setCommissionData(null);
    } finally {
      setLoadingCommission(false);
    }
  };

  const handleShowAllBets = async () => {
    if (!selectedBotForActiveBets) return;
    
    setShowAllBets(true);
    setLoadingActiveBets(true);
    
    try {
      const response = await executeOperation(
        `/admin/human-bots/${selectedBotForActiveBets.id}/all-bets?page=${allBetsPage}&limit=20`, 
        'GET'
      );
      setAllBetsData(response);
    } catch (error) {
      console.error('Ошибка получения всех ставок:', error);
      setAllBetsData(null);
    } finally {
      setLoadingActiveBets(false);
    }
  };

  const handleToggleStatus = async (bot) => {
    try {
      await executeOperation(`/admin/human-bots/${bot.id}/toggle-status`, 'POST');
      addNotification(`Human-бот "${bot.name}" ${bot.is_active ? 'успешно деактивирован' : 'успешно активирован'}`, 'success');
      await fetchHumanBots();
      await fetchStats();
    } catch (error) {
      console.error('Ошибка переключения статуса:', error);
    }
  };

  const handleToggleAutoPlay = async (bot, canPlay) => {
    try {
      await executeOperation(`/admin/human-bots/${bot.id}/toggle-auto-play`, 'POST', {
        can_play_with_other_bots: canPlay
      });
      addNotification(`Настройки Human-бота "${bot.name}" изменены: автоигра с другими ботами ${canPlay ? 'включена' : 'отключена'}`, 'success');
      await fetchHumanBots();
      await fetchStats();
    } catch (error) {
      console.error('Ошибка переключения автоигры:', error);
    }
  };

  const handleTogglePlayWithPlayers = async (bot, canPlay) => {
    // Check if global setting allows play with players
    if (!globalSettings.play_with_players_enabled) {
      addNotification('Невозможно изменить настройку: игра с игроками отключена глобально в настройках системы', 'warning');
      return;
    }
    
    try {
      await executeOperation(`/admin/human-bots/${bot.id}/toggle-play-with-players`, 'POST', {
        can_play_with_players: canPlay
      });
      addNotification(`Настройки Human-бота "${bot.name}" изменены: игра с игроками ${canPlay ? 'включена' : 'отключена'}`, 'success');
      await fetchHumanBots();
      await fetchStats();
    } catch (error) {
      console.error('Ошибка переключения игры с игроками:', error);
    }
  };

  const handleRecalculateBets = async (bot) => {
    const confirmed = await confirm({
      title: `Пересчёт ставок Human-бота`,
      message: `Вы уверены, что хотите пересчитать ставки для Human-бота "${bot.name}"? Все активные ставки будут отменены.`,
      type: "warning"
    });

    if (confirmed) {
      try {
        const response = await executeOperation(`/admin/human-bots/${bot.id}/recalculate-bets`, 'POST');
        addNotification(`Пересчёт ставок завершён: Human-бот "${bot.name}" - отменено ${response.cancelled_bets} активных ставок`, 'success');
        await fetchHumanBots();
        await fetchStats();
      } catch (error) {
        console.error('Ошибка пересчёта ставок:', error);
      }
    }
  };

  const handleResetStats = async (bot) => {
    const confirmed = await confirm({
      title: `Сброс статистики Human-бота`,
      message: `Вы уверены, что хотите сбросить всю статистику для Human-бота "${bot.name}"? Это действие нельзя отменить.`,
      type: "warning"
    });

    if (confirmed) {
      try {
        const response = await executeOperation(`/admin/human-bots/${bot.id}/reset-stats`, 'POST');
        addNotification(`Статистика Human-бота "${bot.name}" успешно сброшена`, 'success');
        await fetchHumanBots();
        await fetchStats();
      } catch (error) {
        console.error('Ошибка сброса статистики:', error);
        addNotification(`Ошибка при сбросе статистики: ${error.message}`, 'error');
      }
    }
  };

  const handleDeleteBot = async (bot) => {
    try {
      // First try normal delete
      await executeOperation(`/admin/human-bots/${bot.id}`, 'DELETE');
      addNotification(`Human-бот "${bot.name}" успешно удален из системы`, 'success');
      await fetchHumanBots();
      await fetchStats();
    } catch (error) {
      console.error('Ошибка удаления бота:', error);
      
      // Check if error has detailed active games info
      if (error.detailData && error.detailData.force_delete_required) {
        await handleDeleteBotWithActiveGames(bot, error.detailData);
        return;
      }
      
      // Check if error message contains active games info
      if (error.message.includes('Cannot delete bot with active games')) {
        await handleDeleteBotWithActiveGames(bot, {
          active_games_count: 'неизвестное количество',
          total_frozen_balance: 0,
          games: []
        });
        return;
      }
      
      // For other errors, show generic error
      addNotification(`Ошибка удаления бота: ${error.message}`, 'error');
    }
  };

  const handleDeleteBotWithActiveGames = async (bot, errorInfo) => {
    const confirmed = await confirm({
      title: `⚠️ Удаление бота с активными играми`,
      message: (
        <div className="text-left">
          <p className="mb-3">
            <strong>Human-бот {bot.name}</strong> имеет активные игры:
          </p>
          <div className="bg-yellow-100 border border-yellow-400 rounded p-3 mb-3 text-sm">
            <div><strong>Активных игр:</strong> {errorInfo.active_games_count}</div>
            <div><strong>Заморожено средств:</strong> ${errorInfo.total_frozen_balance?.toFixed(2) || '0.00'}</div>
          </div>
          {errorInfo.games && errorInfo.games.length > 0 && (
            <div className="mb-3">
              <p className="text-sm font-semibold mb-2">Активные игры:</p>
              <div className="max-h-32 overflow-y-auto text-xs">
                {errorInfo.games.map((game, index) => (
                  <div key={index} className="border-b py-1">
                    <div>Ставка: ${game.bet_amount} | Статус: {game.status}</div>
                    <div>Противник: {game.opponent}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          <p className="text-sm text-red-600 font-semibold">
            ⚠️ При принудительном удалении все активные игры будут отменены, 
            а средства возвращены игрокам.
          </p>
          <p className="mt-2 text-sm">
            Продолжить принудительное удаление?
          </p>
        </div>
      ),
      type: "danger"
    });

    if (confirmed) {
      try {
        const response = await executeOperation(`/admin/human-bots/${bot.id}?force_delete=true`, 'DELETE');
        addNotification(response.message || `Human-бот "${bot.name}" принудительно удален со всеми активными играми`, 'warning');
        await fetchHumanBots();
        await fetchStats();
      } catch (forceError) {
        console.error('Ошибка принудительного удаления:', forceError);
        addNotification(`Ошибка принудительного удаления: ${forceError.message}`, 'error');
      }
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTimeLeft = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getCharacterName = (character) => {
    const characterMap = {
      'STABLE': 'Стабильный',
      'AGGRESSIVE': 'Агрессивный',
      'CAUTIOUS': 'Осторожный',
      'BALANCED': 'Балансированный',
      'IMPULSIVE': 'Импульсивный',
      'ANALYST': 'Аналитик',
      'MIMIC': 'Мимик'
    };
    return characterMap[character] || character;
  };

  return (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border-primary">
        <h3 className="text-lg font-rajdhani font-bold text-white">Список Human ботов</h3>
        {loading && <div className="text-text-secondary">Загрузка...</div>}
      </div>

      {/* Bulk actions panel */}
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
                Отменить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table with horizontal scroll */}
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
              <th className="px-4 py-3 text-center text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Gender
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Статистика
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Ожидающие ставки
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Характер
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Статус
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Диапазон ставок
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Ограничение
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Процент побед
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Лимиты ставок
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Играть друг с другом
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Играть с Игроками  
              </th>
              <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider align-bottom">
                Действия
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-primary">
            {humanBots.length === 0 ? (
              <tr>
                <td colSpan="15" className="px-4 py-8 text-center text-text-secondary">
                  Нет Human-ботов для отображения
                </td>
              </tr>
            ) : (
              humanBots.map((bot, index) => (
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
                      {bot.name}
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center">
                      <label className="gender-toggle">
                        <input
                          type="checkbox"
                          checked={bot.gender === 'female'}
                          onChange={() => handleGenderToggle(bot.id, bot.gender)}
                        />
                        <span className="gender-slider"></span>
                        <span className="gender-label male">M</span>
                        <span className="gender-label female">F</span>
                      </label>
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <div className="text-accent-primary font-roboto text-xs">
                      <div>Игр: {bot.actual_games_played || 0}</div>
                      <div>{(bot.actual_wins || 0)}/{(bot.losses || 0)}/{(bot.draws || 0)}</div>
                      <div>
                        <button
                          onClick={() => handleCommissionModal(bot)}
                          className="text-blue-400 hover:text-blue-300 underline font-roboto cursor-pointer"
                          title="Показать детализацию комиссий"
                        >
                          Общая комиссия: ${(bot.total_commission_paid || 0).toFixed(2)}
                        </button>
                      </div>
                      <div>
                        <span className={((bot.correct_profit || 0)) >= 0 ? 'text-green-400' : 'text-red-400'}>
                          Прибыль: ${(bot.correct_profit || 0).toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className={((bot.correct_profit || 0) - (bot.total_commission_paid || 0)) >= 0 ? 'text-green-400' : 'text-red-400'}>
                          Чистая прибыль: ${((bot.correct_profit || 0) - (bot.total_commission_paid || 0)).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <button
                      onClick={() => handleActiveBetsModal(bot)}
                      className="text-blue-400 hover:text-blue-300 underline font-roboto text-sm cursor-pointer"
                      title="Показать активные ставки"
                    >
                      {bot.active_bets_count || 0}
                    </button>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <span className={`px-2 py-1 text-xs rounded-full font-roboto font-medium text-white ${
                      bot.character === 'AGGRESSIVE' ? 'bg-red-600' :
                      bot.character === 'CAUTIOUS' ? 'bg-blue-600' :
                      bot.character === 'STABLE' ? 'bg-green-600' :
                      bot.character === 'IMPULSIVE' ? 'bg-purple-600' :
                      bot.character === 'ANALYST' ? 'bg-indigo-600' :
                      bot.character === 'MIMIC' ? 'bg-pink-600' :
                      'bg-gray-600'
                    }`}>
                      {getCharacterName(bot.character)}
                    </span>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <span className={`px-2 py-1 text-xs rounded-full font-roboto font-medium ${
                      bot.is_active 
                        ? 'bg-green-600 text-white' 
                        : 'bg-red-600 text-white'
                    }`}>
                      {bot.is_active ? 'Активен' : 'Неактивен'}
                    </span>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <div className="text-accent-primary font-roboto text-xs">
                      <div>Мин: {formatAsGems(bot.min_bet)}</div>
                      <div>Макс: {formatAsGems(bot.max_bet)}</div>
                      <div>Средний: {formatAsGems(bot.average_bet_amount || 0)}</div>
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <input
                      type="number"
                      value={bot.bet_limit_amount || 300}
                      onChange={(e) => handleBetLimitAmountChange(bot, parseFloat(e.target.value) || 300)}
                      className="w-20 px-2 py-1 bg-surface-sidebar text-white rounded border border-border-primary focus:border-accent-primary text-center text-sm"
                      min="1"
                      max="100000"
                    />
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <div className="text-orange-400 font-roboto text-sm">
                      {bot.win_percentage}%
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <div className="text-yellow-400 font-roboto text-sm">
                      {bot.bet_limit || 12}
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <label className="relative inline-flex items-center cursor-pointer group">
                      <input 
                        type="checkbox" 
                        checked={bot.can_play_with_other_bots || false}
                        onChange={(e) => handleToggleAutoPlay(bot, e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="relative w-11 h-6 bg-gray-700 rounded-full peer peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 peer-focus:ring-opacity-50 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all after:duration-300 peer-checked:bg-gradient-to-r peer-checked:from-blue-500 peer-checked:to-purple-600 shadow-lg hover:shadow-xl transition-all duration-300 group-hover:scale-105">
                        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent to-white opacity-20"></div>
                      </div>
                    </label>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <label className={`relative inline-flex items-center group ${globalSettings.play_with_players_enabled ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}`}>
                      <input 
                        type="checkbox" 
                        checked={bot.can_play_with_players || false}
                        onChange={(e) => handleTogglePlayWithPlayers(bot, e.target.checked)}
                        disabled={!globalSettings.play_with_players_enabled}
                        className="sr-only peer"
                      />
                      <div className={`relative w-11 h-6 ${globalSettings.play_with_players_enabled ? 'bg-gray-700' : 'bg-gray-800'} rounded-full peer peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-green-300 peer-focus:ring-opacity-50 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all after:duration-300 peer-checked:bg-gradient-to-r peer-checked:from-green-500 peer-checked:to-emerald-600 shadow-lg ${globalSettings.play_with_players_enabled ? 'hover:shadow-xl transition-all duration-300 group-hover:scale-105' : ''} ${!globalSettings.play_with_players_enabled ? 'opacity-50' : ''}`}>
                        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent to-white opacity-20"></div>
                      </div>
                    </label>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <div className="flex space-x-2 justify-center">
                      <button
                        onClick={() => onEditBot(bot)}
                        className="p-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                        title="Настройки"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleRecalculateBets(bot)}
                        className="p-1 bg-purple-600 text-white rounded hover:bg-purple-700"
                        title="Пересчёт ставок"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleResetStats(bot)}
                        className="p-1 bg-orange-600 text-white rounded hover:bg-orange-700"
                        title="Сбросить статистику"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleToggleStatus(bot)}
                        className={`p-1 text-white rounded hover:opacity-80 ${
                          bot.is_active ? 'bg-yellow-600' : 'bg-green-600'
                        }`}
                        title={bot.is_active ? 'Деактивировать' : 'Активировать'}
                      >
                        {bot.is_active ? (
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        ) : (
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m-7-3a9 9 0 1118 0 9 9 0 01-18 0z" />
                          </svg>
                        )}
                      </button>
                      <button
                        onClick={() => handleDeleteBot(bot)}
                        className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                        title="Удалить бота"
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

      {/* Active Bets Modal */}
      <HumanBotActiveBetsModal
        isOpen={isActiveBetsModalOpen}
        onClose={() => {
          setIsActiveBetsModalOpen(false);
          setSelectedBotForActiveBets(null);
          setActiveBetsData(null);
          setAllBetsData(null);
          setShowAllBets(false);
        }}
        bot={selectedBotForActiveBets}
        addNotification={addNotification}
      />

      {/* Commission Modal */}
      <HumanBotCommissionModal
        isOpen={isCommissionModalOpen}
        onClose={() => {
          setIsCommissionModalOpen(false);
          setSelectedBotForCommission(null);
          setCommissionData(null);
          setCommissionPage(1);
        }}
        bot={selectedBotForCommission}
        data={commissionData}
        loading={loadingCommission}
        onPageChange={handleCommissionPageChange}
      />

      {/* Modals */}
      <ConfirmationModal {...confirmationModal} />
    </div>
  );
};

export default HumanBotsList;