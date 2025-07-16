import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import API, { getApiConfig } from '../utils/api';
import { useNotifications } from '../components/NotificationContext';

/**
 * Централизованный хук для управления ботами
 * Объединяет все операции CRUD с ботами и их состоянием
 */
export const useBotsManagement = () => {
  const { showSuccessRU, showErrorRU } = useNotifications();
  
  // Основные состояния
  const [botsList, setBotsList] = useState([]);
  const [stats, setStats] = useState({});
  const [activeBetsStats, setActiveBetsStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Состояния для операций
  const [operationLoading, setOperationLoading] = useState({});
  const [bulkOperationLoading, setBulkOperationLoading] = useState(false);

  /**
   * Получение списка ботов
   */
  const fetchBotsList = useCallback(async (page = 1, limit = 50) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get(`${API}/admin/bots/regular/list`, {
        ...getApiConfig(),
        params: { page, limit }
      });
      
      if (response.data.success) {
        setBotsList(response.data.bots || []);
        return response.data;
      } else {
        throw new Error(response.data.message || 'Ошибка получения списка ботов');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка загрузки ботов';
      setError(errorMessage);
      showErrorRU(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, [showErrorRU]);

  /**
   * Получение статистики ботов
   */
  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/admin/bots/stats`, getApiConfig());
      if (response.data.success) {
        setStats(response.data.stats || {});
        return response.data.stats;
      }
    } catch (err) {
      console.error('Ошибка загрузки статистики:', err);
    }
  }, []);

  /**
   * Получение статистики активных ставок
   */
  const fetchActiveBetsStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/admin/bots/active-bets-stats`, getApiConfig());
      if (response.data.success) {
        setActiveBetsStats(response.data.stats || {});
        return response.data.stats;
      }
    } catch (err) {
      console.error('Ошибка загрузки статистики активных ставок:', err);
    }
  }, []);

  /**
   * Создание нового бота
   */
  const createBot = useCallback(async (botData) => {
    try {
      setOperationLoading(prev => ({ ...prev, create: true }));
      
      const response = await axios.post(`${API}/admin/bots/regular/create`, botData, getApiConfig());
      
      if (response.data.success) {
        showSuccessRU(response.data.message || 'Бот успешно создан');
        
        // Обновляем список ботов
        await fetchBotsList();
        await fetchStats();
        
        return response.data;
      } else {
        throw new Error(response.data.message || 'Ошибка создания бота');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка при создании бота';
      showErrorRU(errorMessage);
      throw err;
    } finally {
      setOperationLoading(prev => ({ ...prev, create: false }));
    }
  }, [showSuccessRU, showErrorRU, fetchBotsList, fetchStats]);

  /**
   * Обновление бота
   */
  const updateBot = useCallback(async (botId, botData) => {
    try {
      setOperationLoading(prev => ({ ...prev, [`update_${botId}`]: true }));
      
      const response = await axios.put(`${API}/admin/bots/regular/${botId}`, botData, getApiConfig());
      
      if (response.data.success) {
        showSuccessRU(response.data.message || 'Бот успешно обновлен');
        
        // Обновляем список ботов
        await fetchBotsList();
        
        return response.data;
      } else {
        throw new Error(response.data.message || 'Ошибка обновления бота');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка при обновлении бота';
      showErrorRU(errorMessage);
      throw err;
    } finally {
      setOperationLoading(prev => ({ ...prev, [`update_${botId}`]: false }));
    }
  }, [showSuccessRU, showErrorRU, fetchBotsList]);

  /**
   * Удаление бота
   */
  const deleteBot = useCallback(async (botId, reason) => {
    try {
      setOperationLoading(prev => ({ ...prev, [`delete_${botId}`]: true }));
      
      const response = await axios.delete(`${API}/admin/bots/regular/${botId}`, {
        ...getApiConfig(),
        data: { reason }
      });
      
      if (response.data.success) {
        showSuccessRU(response.data.message || 'Бот успешно удален');
        
        // Обновляем список ботов
        await fetchBotsList();
        await fetchStats();
        
        return response.data;
      } else {
        throw new Error(response.data.message || 'Ошибка удаления бота');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка при удалении бота';
      showErrorRU(errorMessage);
      throw err;
    } finally {
      setOperationLoading(prev => ({ ...prev, [`delete_${botId}`]: false }));
    }
  }, [showSuccessRU, showErrorRU, fetchBotsList, fetchStats]);

  /**
   * Переключение статуса бота
   */
  const toggleBotStatus = useCallback(async (botId) => {
    try {
      setOperationLoading(prev => ({ ...prev, [`toggle_${botId}`]: true }));
      
      const response = await axios.post(`${API}/admin/bots/regular/${botId}/toggle`, {}, getApiConfig());
      
      if (response.data.success) {
        showSuccessRU(response.data.message || 'Статус бота изменен');
        
        // Обновляем список ботов
        await fetchBotsList();
        await fetchStats();
        
        return response.data;
      } else {
        throw new Error(response.data.message || 'Ошибка изменения статуса бота');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка при изменении статуса бота';
      showErrorRU(errorMessage);
      throw err;
    } finally {
      setOperationLoading(prev => ({ ...prev, [`toggle_${botId}`]: false }));
    }
  }, [showSuccessRU, showErrorRU, fetchBotsList, fetchStats]);

  /**
   * Получение активных ставок бота
   */
  const fetchBotActiveBets = useCallback(async (botId) => {
    try {
      setOperationLoading(prev => ({ ...prev, [`active_bets_${botId}`]: true }));
      
      const response = await axios.get(`${API}/admin/bots/${botId}/active-bets`, getApiConfig());
      
      if (response.data.success) {
        return response.data;
      } else {
        throw new Error(response.data.message || 'Ошибка получения активных ставок');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка загрузки активных ставок';
      showErrorRU(errorMessage);
      throw err;
    } finally {
      setOperationLoading(prev => ({ ...prev, [`active_bets_${botId}`]: false }));
    }
  }, [showErrorRU]);

  /**
   * Получение истории циклов бота
   */
  const fetchBotCycleHistory = useCallback(async (botId) => {
    try {
      setOperationLoading(prev => ({ ...prev, [`cycle_history_${botId}`]: true }));
      
      const response = await axios.get(`${API}/admin/bots/${botId}/cycle-history`, getApiConfig());
      
      if (response.data.success) {
        return response.data;
      } else {
        throw new Error(response.data.message || 'Ошибка получения истории циклов');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка загрузки истории циклов';
      showErrorRU(errorMessage);
      throw err;
    } finally {
      setOperationLoading(prev => ({ ...prev, [`cycle_history_${botId}`]: false }));
    }
  }, [showErrorRU]);

  /**
   * Обновление лимита ставок бота
   */
  const updateBotLimit = useCallback(async (botId, newLimit) => {
    try {
      setOperationLoading(prev => ({ ...prev, [`limit_${botId}`]: true }));
      
      const response = await axios.put(`${API}/admin/bots/${botId}/limit`, {
        limit: newLimit
      }, getApiConfig());
      
      if (response.data.success) {
        showSuccessRU(response.data.message || 'Лимит бота обновлен');
        
        // Обновляем список ботов
        await fetchBotsList();
        
        return response.data;
      } else {
        throw new Error(response.data.message || 'Ошибка обновления лимита');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка при обновлении лимита';
      showErrorRU(errorMessage);
      throw err;
    } finally {
      setOperationLoading(prev => ({ ...prev, [`limit_${botId}`]: false }));
    }
  }, [showSuccessRU, showErrorRU, fetchBotsList]);

  /**
   * Массовые операции
   */
  const bulkOperations = {
    /**
     * Включить/выключить всех ботов
     */
    toggleAllBots: useCallback(async (enabled) => {
      try {
        setBulkOperationLoading(true);
        
        const response = await axios.post(`${API}/admin/bots/toggle-all`, {
          enabled
        }, getApiConfig());
        
        if (response.data.success) {
          showSuccessRU(response.data.message || `Все боты ${enabled ? 'включены' : 'выключены'}`);
          
          // Обновляем данные
          await fetchBotsList();
          await fetchStats();
          
          return response.data;
        } else {
          throw new Error(response.data.message || 'Ошибка массовой операции');
        }
      } catch (err) {
        const errorMessage = err.response?.data?.detail || err.message || 'Ошибка массовой операции';
        showErrorRU(errorMessage);
        throw err;
      } finally {
        setBulkOperationLoading(false);
      }
    }, [showSuccessRU, showErrorRU, fetchBotsList, fetchStats]),

    /**
     * Запуск обычных ботов
     */
    startRegularBots: useCallback(async () => {
      try {
        setBulkOperationLoading(true);
        
        const response = await axios.post(`${API}/admin/bots/start-regular`, {}, getApiConfig());
        
        if (response.data.limit_reached) {
          showErrorRU(`Лимит активных ставок достигнут: ${response.data.current_active_bets}/${response.data.max_active_bets}`);
        } else {
          showSuccessRU(response.data.message || 'Обычные боты запущены');
        }
        
        // Обновляем данные
        await fetchStats();
        await fetchActiveBetsStats();
        
        return response.data;
      } catch (err) {
        const errorMessage = err.response?.data?.detail || err.message || 'Ошибка при запуске ботов';
        showErrorRU(errorMessage);
        throw err;
      } finally {
        setBulkOperationLoading(false);
      }
    }, [showSuccessRU, showErrorRU, fetchStats, fetchActiveBetsStats])
  };

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
    
    // Состояния операций
    operationLoading,
    bulkOperationLoading,
    
    // Основные операции
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
    
    // Утилиты
    refresh: useCallback(async () => {
      await Promise.all([
        fetchBotsList(),
        fetchStats(),
        fetchActiveBetsStats()
      ]);
    }, [fetchBotsList, fetchStats, fetchActiveBetsStats])
  };
};