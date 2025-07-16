import { useState, useCallback } from 'react';
import { useApi } from './useApi';
import { useNotifications } from '../components/NotificationContext';

/**
 * Специализированный хук для операций с ботами
 * Предоставляет высокоуровневые операции с обработкой ошибок и уведомлений
 */
export const useBotOperations = () => {
  const { botsApi, errorUtils } = useApi();
  const { showSuccessRU, showErrorRU } = useNotifications();
  
  // Состояния для отслеживания операций
  const [operationStates, setOperationStates] = useState({});
  const [validationErrors, setValidationErrors] = useState({});

  /**
   * Установка состояния операции
   */
  const setOperationState = useCallback((operation, state) => {
    setOperationStates(prev => ({
      ...prev,
      [operation]: state
    }));
  }, []);

  /**
   * Получение состояния операции
   */
  const getOperationState = useCallback((operation) => {
    return operationStates[operation] || false;
  }, [operationStates]);

  /**
   * Валидация данных бота
   */
  const validateBotData = useCallback((botData) => {
    const errors = {};
    
    if (!botData.name || botData.name.trim().length < 3) {
      errors.name = 'Имя бота должно содержать минимум 3 символа';
    }
    
    if (!botData.type_id) {
      errors.type_id = 'Выберите тип бота';
    }
    
    if (!botData.creation_mode) {
      errors.creation_mode = 'Выберите режим создания';
    }
    
    if (botData.pause_timer < 1 || botData.pause_timer > 60) {
      errors.pause_timer = 'Таймер паузы должен быть от 1 до 60 минут';
    }
    
    if (botData.recreate_timer < 1 || botData.recreate_timer > 300) {
      errors.recreate_timer = 'Интервал пересоздания должен быть от 1 до 300 секунд';
    }
    
    if (botData.cycle_games < 1 || botData.cycle_games > 100) {
      errors.cycle_games = 'Количество игр в цикле должно быть от 1 до 100';
    }
    
    if (botData.win_rate < 10 || botData.win_rate > 90) {
      errors.win_rate = 'Win rate должен быть от 10% до 90%';
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, []);

  /**
   * Создание бота с валидацией
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
  }, [botsApi, showSuccessRU, showErrorRU, errorUtils, validateBotData]);

  /**
   * Обновление бота с валидацией
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
  }, [botsApi, showSuccessRU, showErrorRU, errorUtils, validateBotData]);

  /**
   * Удаление бота с подтверждением
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
  }, [botsApi, showSuccessRU, showErrorRU, errorUtils]);

  /**
   * Переключение статуса бота
   */
  const toggleBotStatus = useCallback(async (botId, currentStatus) => {
    try {
      setOperationState(`toggling_${botId}`, true);
      
      const response = await botsApi.toggleStatus(botId);
      
      if (response.success) {
        const newStatus = !currentStatus;
        showSuccessRU(response.message || `Бот ${newStatus ? 'включен' : 'выключен'}`);
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
  }, [botsApi, showSuccessRU, showErrorRU, errorUtils]);

  /**
   * Обновление лимита ставок с валидацией
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
  }, [botsApi, showSuccessRU, showErrorRU, errorUtils]);

  /**
   * Получение активных ставок бота
   */
  const fetchActiveBets = useCallback(async (botId) => {
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
  }, [botsApi, showErrorRU, errorUtils]);

  /**
   * Получение истории циклов бота
   */
  const fetchCycleHistory = useCallback(async (botId) => {
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
  }, [botsApi, showErrorRU, errorUtils]);

  /**
   * Массовые операции
   */
  const bulkOperations = {
    /**
     * Переключение всех ботов
     */
    toggleAllBots: useCallback(async (enabled) => {
      try {
        setOperationState('toggling_all', true);
        
        const response = await botsApi.toggleAll(enabled);
        
        if (response.success) {
          showSuccessRU(response.message || `Все боты ${enabled ? 'включены' : 'выключены'}`);
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
    }, [botsApi, showSuccessRU, showErrorRU, errorUtils]),

    /**
     * Запуск обычных ботов
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
        
        return response;
      } catch (error) {
        const errorMessage = errorUtils.getErrorMessage(error);
        showErrorRU(errorMessage);
        throw error;
      } finally {
        setOperationState('starting_regular', false);
      }
    }, [botsApi, showSuccessRU, showErrorRU, errorUtils])
  };

  /**
   * Утилиты для работы с состоянием
   */
  const stateUtils = {
    /**
     * Проверка, выполняется ли операция
     */
    isOperationInProgress: useCallback((operation) => {
      return getOperationState(operation);
    }, [getOperationState]),

    /**
     * Получение всех активных операций
     */
    getActiveOperations: useCallback(() => {
      return Object.keys(operationStates).filter(key => operationStates[key]);
    }, [operationStates]),

    /**
     * Очистка всех состояний операций
     */
    clearAllOperationStates: useCallback(() => {
      setOperationStates({});
    }, []),

    /**
     * Очистка ошибок валидации
     */
    clearValidationErrors: useCallback(() => {
      setValidationErrors({});
    }, [])
  };

  return {
    // Основные операции
    createBot,
    updateBot,
    deleteBot,
    toggleBotStatus,
    updateBotLimit,
    fetchActiveBets,
    fetchCycleHistory,
    
    // Массовые операции
    bulkOperations,
    
    // Состояния
    operationStates,
    validationErrors,
    
    // Утилиты
    stateUtils,
    validateBotData,
    getOperationState,
    
    // Проверки состояний
    isCreating: getOperationState('creating'),
    isTogglingAll: getOperationState('toggling_all'),
    isStartingRegular: getOperationState('starting_regular')
  };
};