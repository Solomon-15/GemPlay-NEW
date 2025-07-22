import { useState, useEffect, useCallback } from 'react';
import { useApi } from './useApi';
import { useNotifications } from '../components/NotificationContext';

/**
 * ОПТИМИЗИРОВАННЫЙ хук для управления ботами
 * Объединяет функциональность useBotsManagement + useBotOperations
 * Использует useApi для устранения дублирования HTTP запросов
 */
export const useBotsManagement = () => {
  const { botsApi, errorUtils, loading: apiLoading } = useApi();
  const { showSuccessRU, showErrorRU } = useNotifications();
  
  // Централизованные состояния
  const [botsList, setBotsList] = useState([]);
  const [stats, setStats] = useState({});
  const [activeBetsStats, setActiveBetsStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Состояния операций (объединенные из двух хуков)
  const [operationStates, setOperationStates] = useState({});
  const [validationErrors, setValidationErrors] = useState({});

  /**
   * Универсальная функция для управления состояниями операций
   */
  const setOperationState = useCallback((operation, state) => {
    setOperationStates(prev => ({
      ...prev,
      [operation]: state
    }));
  }, []);

  const getOperationState = useCallback((operation) => {
    return operationStates[operation] || false;
  }, [operationStates]);

  /**
   * Валидация данных бота (из useBotOperations)
   */
  const validateBotData = useCallback((botData) => {
    const errors = {};
    
    if (!botData.name || botData.name.trim().length < 3) {
      errors.name = 'Имя бота должно содержать минимум 3 символа';
    }
    
    if (botData.cycle_games && (botData.cycle_games < 1 || botData.cycle_games > 100)) {
      errors.cycle_games = 'Количество игр в цикле должно быть от 1 до 100';
    }
    
    if (botData.win_rate && (botData.win_rate < 10 || botData.win_rate > 90)) {
      errors.win_rate = 'Win rate должен быть от 10% до 90%';
    }
    
    if (botData.min_bet_amount && botData.max_bet_amount) {
      if (botData.min_bet_amount >= botData.max_bet_amount) {
        errors.bet_range = 'Минимальная ставка должна быть меньше максимальной';
      }
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, []);

  /**
   * Получение списка ботов (использует useApi вместо прямого axios)
   */
  const fetchBotsList = useCallback(async (page = 1, limit = 50) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await botsApi.getList({ page, limit });
      
      if (response.success) {
        setBotsList(response.bots || []);
        return response;
      } else {
        throw new Error(response.message || 'Ошибка получения списка ботов');
      }
    } catch (err) {
      const errorMessage = errorUtils.getErrorMessage(err);
      setError(errorMessage);
      showErrorRU(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, [botsApi, errorUtils, showErrorRU]);

  /**
   * Получение статистики ботов (использует useApi)
   */
  const fetchStats = useCallback(async () => {
    try {
      const response = await botsApi.getStats();
      if (response.success) {
        setStats(response.stats || {});
        return response.stats;
      }
    } catch (err) {
      console.error('Ошибка загрузки статистики:', err);
    }
  }, [botsApi]);

  /**
   * Получение статистики активных ставок (использует useApi)
   */
  const fetchActiveBetsStats = useCallback(async () => {
    try {
      const response = await botsApi.getActiveBetsStats();
      if (response.success) {
        setActiveBetsStats(response.stats || {});
        return response.stats;
      }
    } catch (err) {
      console.error('Ошибка загрузки статистики активных ставок:', err);
    }
  }, [botsApi]);

  /**
   * Создание бота с валидацией (объединенная логика)
   */
  const createBot = useCallback(async (botData) => {
    try {
      setOperationState('creating', true);
      
      if (!validateBotData(botData)) {
        throw new Error('Пожалуйста, исправьте ошибки в форме');
      }
      
      const response = await botsApi.create(botData);
      
      if (response.success) {
        showSuccessRU(response.message || 'Бот успешно создан');
        setValidationErrors({});
        
        // Обновляем данные
        await Promise.all([fetchBotsList(), fetchStats()]);
        
        return response;
      } else {
        throw new Error(response.message || 'Ошибка создания бота');
      }
    } catch (error) {
      const errorMessage = errorUtils.getErrorMessage(error);
      showErrorRU(errorMessage);
      throw error;
    } finally {
      setOperationState('creating', false);
    }
  }, [botsApi, errorUtils, showSuccessRU, showErrorRU, validateBotData, fetchBotsList, fetchStats]);

  /**
   * Обновление бота с валидацией (объединенная логика)
   */
  const updateBot = useCallback(async (botId, botData) => {
    try {
      setOperationState(`updating_${botId}`, true);
      
      if (!validateBotData(botData)) {
        throw new Error('Пожалуйста, исправьте ошибки в форме');
      }
      
      const response = await botsApi.update(botId, botData);
      
      if (response.success) {
        showSuccessRU(response.message || 'Бот успешно обновлен');
        setValidationErrors({});
        
        // Обновляем список
        await fetchBotsList();
        
        return response;
      } else {
        throw new Error(response.message || 'Ошибка обновления бота');
      }
    } catch (error) {
      const errorMessage = errorUtils.getErrorMessage(error);
      showErrorRU(errorMessage);
      throw error;
    } finally {
      setOperationState(`updating_${botId}`, false);
    }
  }, [botsApi, errorUtils, showSuccessRU, showErrorRU, validateBotData, fetchBotsList]);

  /**
   * Удаление бота с валидацией причины (объединенная логика)
   */
  const deleteBot = useCallback(async (botId, reason) => {
    try {
      setOperationState(`deleting_${botId}`, true);
      
      if (!reason || reason.trim().length < 5) {
        throw new Error('Укажите причину удаления (минимум 5 символов)');
      }
      
      const response = await botsApi.delete(botId, reason);
      
      if (response.success) {
        showSuccessRU(response.message || 'Бот успешно удален');
        
        // Обновляем данные
        await Promise.all([fetchBotsList(), fetchStats()]);
        
        return response;
      } else {
        throw new Error(response.message || 'Ошибка удаления бота');
      }
    } catch (error) {
      const errorMessage = errorUtils.getErrorMessage(error);
      showErrorRU(errorMessage);
      throw error;
    } finally {
      setOperationState(`deleting_${botId}`, false);
    }
  }, [botsApi, errorUtils, showSuccessRU, showErrorRU, fetchBotsList, fetchStats]);

  /**
   * Переключение статуса бота (объединенная логика)
   */
  const toggleBotStatus = useCallback(async (botId, currentStatus) => {
    try {
      setOperationState(`toggling_${botId}`, true);
      
      const response = await botsApi.toggleStatus(botId);
      
      if (response.success) {
        const newStatus = !currentStatus;
        showSuccessRU(response.message || `Бот ${newStatus ? 'включен' : 'выключен'}`);
        
        // Обновляем данные
        await Promise.all([fetchBotsList(), fetchStats()]);
        
        return response;
      } else {
        throw new Error(response.message || 'Ошибка изменения статуса');
      }
    } catch (error) {
      const errorMessage = errorUtils.getErrorMessage(error);
      showErrorRU(errorMessage);
      throw error;
    } finally {
      setOperationState(`toggling_${botId}`, false);
    }
  }, [botsApi, errorUtils, showSuccessRU, showErrorRU, fetchBotsList, fetchStats]);

  /**
   * Получение активных ставок бота (использует useApi)
   */
  const fetchBotActiveBets = useCallback(async (botId) => {
    try {
      setOperationState(`fetching_active_bets_${botId}`, true);
      
      const response = await botsApi.getActiveBets(botId);
      
      if (response.success) {
        return response;
      } else {
        throw new Error(response.message || 'Ошибка получения активных ставок');
      }
    } catch (error) {
      const errorMessage = errorUtils.getErrorMessage(error);
      showErrorRU(errorMessage);
      throw error;
    } finally {
      setOperationState(`fetching_active_bets_${botId}`, false);
    }
  }, [botsApi, errorUtils, showErrorRU]);

  /**
   * Получение истории циклов бота (использует useApi)
   */
  const fetchBotCycleHistory = useCallback(async (botId) => {
    try {
      setOperationState(`fetching_cycle_history_${botId}`, true);
      
      const response = await botsApi.getCycleHistory(botId);
      
      if (response.success) {
        return response;
      } else {
        throw new Error(response.message || 'Ошибка получения истории циклов');
      }
    } catch (error) {
      const errorMessage = errorUtils.getErrorMessage(error);
      showErrorRU(errorMessage);
      throw error;
    } finally {
      setOperationState(`fetching_cycle_history_${botId}`, false);
    }
  }, [botsApi, errorUtils, showErrorRU]);

  /**
   * Обновление лимита ставок бота с валидацией (объединенная логика)
   */
  const updateBotLimit = useCallback(async (botId, newLimit) => {
    try {
      setOperationState(`updating_limit_${botId}`, true);
      
      const limit = parseInt(newLimit);
      
      if (isNaN(limit) || limit < 1 || limit > 100) {
        throw new Error('Лимит должен быть числом от 1 до 100');
      }
      
      const response = await botsApi.updateLimit(botId, limit);
      
      if (response.success) {
        showSuccessRU(response.message || 'Лимит успешно обновлен');
        
        // Обновляем список
        await fetchBotsList();
        
        return response;
      } else {
        throw new Error(response.message || 'Ошибка обновления лимита');
      }
    } catch (error) {
      const errorMessage = errorUtils.getErrorMessage(error);
      showErrorRU(errorMessage);
      throw error;
    } finally {
      setOperationState(`updating_limit_${botId}`, false);
    }
  }, [botsApi, errorUtils, showSuccessRU, showErrorRU, fetchBotsList]);

  /**
   * Массовые операции (объединенные из двух хуков)
   */
  const bulkOperations = {
    /**
     * Переключение всех ботов (использует useApi)
     */
    toggleAllBots: useCallback(async (enabled) => {
      try {
        setOperationState('toggling_all', true);
        
        const response = await botsApi.toggleAll(enabled);
        
        if (response.success) {
          showSuccessRU(response.message || `Все боты ${enabled ? 'включены' : 'выключены'}`);
          
          // Обновляем данные
          await Promise.all([fetchBotsList(), fetchStats()]);
          
          return response;
        } else {
          throw new Error(response.message || 'Ошибка массовой операции');
        }
      } catch (error) {
        const errorMessage = errorUtils.getErrorMessage(error);
        showErrorRU(errorMessage);
        throw error;
      } finally {
        setOperationState('toggling_all', false);
      }
    }, [botsApi, errorUtils, showSuccessRU, showErrorRU, fetchBotsList, fetchStats]),

    /**
     * Запуск обычных ботов (использует useApi)
     */
    startRegularBots: useCallback(async () => {
      try {
        setOperationState('starting_regular', true);
        
        const response = await botsApi.startRegular();
        
        if (response.limit_reached) {
          showErrorRU(`Лимит достигнут: ${response.current_active_bets}/${response.max_active_bets}`);
        } else {
          showSuccessRU(response.message || 'Обычные боты запущены');
        }
        
        // Обновляем данные
        await Promise.all([fetchStats(), fetchActiveBetsStats()]);
        
        return response;
      } catch (error) {
        const errorMessage = errorUtils.getErrorMessage(error);
        showErrorRU(errorMessage);
        throw error;
      } finally {
        setOperationState('starting_regular', false);
      }
    }, [botsApi, errorUtils, showSuccessRU, showErrorRU, fetchStats, fetchActiveBetsStats])
  };

  /**
   * Утилиты для работы с состоянием (из useBotOperations)
   */
  const stateUtils = {
    isOperationInProgress: useCallback((operation) => {
      return getOperationState(operation);
    }, [getOperationState]),

    getActiveOperations: useCallback(() => {
      return Object.keys(operationStates).filter(key => operationStates[key]);
    }, [operationStates]),

    clearAllOperationStates: useCallback(() => {
      setOperationStates({});
    }, []),

    clearValidationErrors: useCallback(() => {
      setValidationErrors({});
    }, [])
  };

  /**
   * Универсальная функция для API операций (включая Human-ботов)
   */
  const executeOperation = useCallback(async (url, method, data = null) => {
    try {
      const { request } = await import('../utils/api');
      const response = await request(url, {
        method,
        data
      });
      return response;
    } catch (error) {
      console.error(`Error executing ${method} ${url}:`, error);
      throw error;
    }
  }, []);

  /**
   * Инициализация данных при монтировании
   */
  useEffect(() => {
    const initializeData = async () => {
      await Promise.all([
        fetchBotsList(),
        fetchStats(),
        fetchActiveBetsStats()
      ]);
    };

    initializeData();
  }, [fetchBotsList, fetchStats, fetchActiveBetsStats]);

  return {
    // Данные
    botsList,
    stats,
    activeBetsStats,
    loading,
    error,
    
    // Состояния операций (объединенные)
    operationStates,
    validationErrors,
    apiLoading, // Из useApi
    
    // Основные операции (объединенные и оптимизированные)
    fetchBotsList,
    fetchStats,
    fetchActiveBetsStats,
    createBot,
    updateBot,
    deleteBot,
    toggleBotStatus,
    
    // Специальные операции
    fetchBotActiveBets,
    fetchBotCycleHistory,
    updateBotLimit,
    
    // Массовые операции
    bulkOperations,
    
    // Утилиты (из useBotOperations)
    stateUtils,
    validateBotData,
    getOperationState,
    
    // Удобные проверки состояний
    isCreating: getOperationState('creating'),
    isTogglingAll: getOperationState('toggling_all'),
    isStartingRegular: getOperationState('starting_regular'),
    
    // Общие утилиты
    refresh: useCallback(async () => {
      await Promise.all([
        fetchBotsList(),
        fetchStats(),
        fetchActiveBetsStats()
      ]);
    }, [fetchBotsList, fetchStats, fetchActiveBetsStats])
  };
};