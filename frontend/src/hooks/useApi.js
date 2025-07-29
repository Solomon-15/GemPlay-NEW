import { useState, useCallback } from 'react';
import axios from 'axios';
import API, { getApiConfig } from '../utils/api';

/**
 * Централизованный хук для работы с API
 * Предоставляет унифицированные методы для HTTP запросов
 */
export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Базовый метод для выполнения API запросов
   */
  const makeRequest = useCallback(async (method, endpoint, data = null, config = {}) => {
    try {
      setLoading(true);
      setError(null);

      const requestConfig = {
        method,
        url: `${API}${endpoint}`,
        ...getApiConfig(),
        ...config
      };

      if (data) {
        if (method.toLowerCase() === 'get') {
          requestConfig.params = data;
        } else {
          requestConfig.data = data;
        }
      }

      const response = await axios(requestConfig);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Ошибка API запроса';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * GET запрос
   */
  const get = useCallback(async (endpoint, params = null, config = {}) => {
    return makeRequest('GET', endpoint, params, config);
  }, [makeRequest]);

  /**
   * POST запрос
   */
  const post = useCallback(async (endpoint, data = null, config = {}) => {
    return makeRequest('POST', endpoint, data, config);
  }, [makeRequest]);

  /**
   * PUT запрос
   */
  const put = useCallback(async (endpoint, data = null, config = {}) => {
    return makeRequest('PUT', endpoint, data, config);
  }, [makeRequest]);

  /**
   * DELETE запрос
   */
  const del = useCallback(async (endpoint, data = null, config = {}) => {
    return makeRequest('DELETE', endpoint, data, config);
  }, [makeRequest]);

  /**
   * PATCH запрос
   */
  const patch = useCallback(async (endpoint, data = null, config = {}) => {
    return makeRequest('PATCH', endpoint, data, config);
  }, [makeRequest]);

  /**
   * Специализированные методы для работы с ботами
   */
  const botsApi = {
    /**
     * Получение списка ботов
     */
    getList: useCallback(async (params = {}) => {
      return get('/admin/bots/regular/list', params);
    }, [get]),

    /**
     * Получение информации о боте
     */
    getBot: useCallback(async (botId) => {
      return get(`/admin/bots/${botId}`);
    }, [get]),

    /**
     * Создание бота
     */
    create: useCallback(async (botData) => {
      return post('/admin/bots/regular/create', botData);
    }, [post]),

    /**
     * Обновление бота
     */
    update: useCallback(async (botId, botData) => {
      return put(`/admin/bots/regular/${botId}`, botData);
    }, [put]),

    /**
     * Удаление бота
     */
    delete: useCallback(async (botId, reason) => {
      return del(`/admin/bots/regular/${botId}`, { reason });
    }, [del]),

    /**
     * Переключение статуса бота
     */
    toggleStatus: useCallback(async (botId) => {
      return post(`/admin/bots/regular/${botId}/toggle`);
    }, [post]),

    /**
     * Получение активных ставок бота
     */
    getActiveBets: useCallback(async (botId) => {
      return get(`/admin/bots/${botId}/active-bets`);
    }, [get]),

    /**
     * Получение истории циклов бота
     */
    getCycleHistory: useCallback(async (botId) => {
      return get(`/admin/bots/${botId}/cycle-history`);
    }, [get]),

    /**
     * Обновление лимита ставок бота
     */
    updateLimit: useCallback(async (botId, limit) => {
      return put(`/admin/bots/${botId}/limit`, { limit });
    }, [put]),

    /**
     * Получение статистики ботов
     */
    getStats: useCallback(async () => {
      return get('/admin/bots/stats');
    }, [get]),

    /**
     * Получение статистики активных ставок
     */
    getActiveBetsStats: useCallback(async () => {
      return get('/admin/bots/active-bets-stats');
    }, [get]),

    /**
     * Включение/выключение всех ботов
     */
    toggleAll: useCallback(async (enabled) => {
      return post('/admin/bots/toggle-all', { enabled });
    }, [post]),

    /**
     * Запуск обычных ботов
     */
    startRegular: useCallback(async () => {
      return post('/admin/bots/start-regular');
    }, [post]),

    /**
     * Получение настроек ботов
     */
    getSettings: useCallback(async () => {
      return get('/admin/bots/settings');
    }, [get]),

    /**
     * Обновление настроек ботов
     */
    updateSettings: useCallback(async (settings) => {
      return post('/admin/bots/settings', settings);
    }, [post])
  };

  /**
   * Специализированные методы для работы с отчетами
   */
  const reportsApi = {
    /**
     * Генерация отчета
     */
    generate: useCallback(async (reportType, params = {}) => {
      return post('/admin/bots/reports/generate', { 
        type: reportType, 
        ...params 
      });
    }, [post]),

    /**
     * Экспорт отчета
     */
    export: useCallback(async (reportId, format) => {
      return post('/admin/bots/reports/export', { 
        reportId, 
        format 
      });
    }, [post]),

    /**
     * Получение списка отчетов
     */
    getList: useCallback(async (params = {}) => {
      return get('/admin/bots/reports', params);
    }, [get])
  };

  /**
   * Специализированные методы для работы с аналитикой
   */
  const analyticsApi = {
    /**
     * Получение данных аналитики
     */
    getData: useCallback(async (params = {}) => {
      return get('/admin/bots/analytics', params);
    }, [get]),

    /**
     * Получение статистики очереди
     */
    getQueueStats: useCallback(async () => {
      return get('/admin/bot-queue-stats');
    }, [get])
  };

  /**
   * Утилиты для работы с ошибками
   */
  const errorUtils = {
    /**
     * Получение человекочитаемого сообщения об ошибке
     */
    getErrorMessage: useCallback((error) => {
      if (error?.response?.data?.detail) {
        return error.response.data.detail;
      }
      if (error?.response?.data?.message) {
        return error.response.data.message;
      }
      if (error?.message) {
        return error.message;
      }
      return 'Неизвестная ошибка';
    }, []),

    /**
     * Проверка типа ошибки
     */
    isNetworkError: useCallback((error) => {
      return error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network Error');
    }, []),

    /**
     * Проверка ошибки авторизации
     */
    isAuthError: useCallback((error) => {
      return error?.response?.status === 401;
    }, []),

    /**
     * Проверка ошибки валидации
     */
    isValidationError: useCallback((error) => {
      return error?.response?.status === 422;
    }, [])
  };

  return {
    loading,
    error,
    
    makeRequest,
    get,
    post,
    put,
    delete: del,
    patch,
    
    botsApi,
    reportsApi,
    analyticsApi,
    
    errorUtils,
    
    clearError: useCallback(() => setError(null), [])
  };
};