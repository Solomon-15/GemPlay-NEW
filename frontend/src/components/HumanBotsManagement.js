import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import useConfirmation from '../hooks/useConfirmation';
import useInput from '../hooks/useInput';
import InputModal from './InputModal';
import ConfirmationModal from './ConfirmationModal';
import HumanBotsList from './HumanBotsList';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Cache configuration
const CACHE_DURATION = 60000; // 1 minute in milliseconds
const AUTO_REFRESH_INTERVAL = 60000; // Auto-refresh every 1 minute

const HumanBotsManagement = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { addNotification } = useNotifications();
  const { confirm, confirmationModal } = useConfirmation();
  const { prompt, inputModal } = useInput();
  const [humanBots, setHumanBots] = useState([]);
  const [stats, setStats] = useState({});
  
  // Enhanced pagination with adjustable page size
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize, setPageSize] = useState(10); // Adjustable page size
  
  // Enhanced filters with search
  const [filters, setFilters] = useState({
    search: '',
    character: '',
    is_active: null,
    min_bet_range: '',
    max_bet_range: '',
    sort_by: 'created_at',
    sort_order: 'desc'
  });
  
  // Search state with debouncing
  const [searchTerm, setSearchTerm] = useState('');
  const [searchDebounceTimeout, setSearchDebounceTimeout] = useState(null);
  
  // Cache state
  const [cache, setCache] = useState({
    data: null,
    timestamp: null,
    key: null
  });
  
  // Auto-refresh state
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(null);
  
  // Performance optimization state
  const [priorityFields, setPriorityFields] = useState(true);
  const [loadingPriority, setLoadingPriority] = useState(false);

  const [activeTab, setActiveTab] = useState('bots'); // 'bots', 'names' или 'settings'

  // Human Bot Names Management State
  const [botNames, setBotNames] = useState([]);
  const [namesLoading, setNamesLoading] = useState(false);
  const [namesSaving, setNamesSaving] = useState(false);
  const [newNameInput, setNewNameInput] = useState('');
  const [bulkNamesInput, setBulkNamesInput] = useState('');
  const [showBulkNamesEditor, setShowBulkNamesEditor] = useState(false);

  const [humanBotSettings, setHumanBotSettings] = useState({
    max_active_bets_human: 100,
    auto_play_enabled: false,
    min_delay_seconds: 1,
    max_delay_seconds: 3600,
    play_with_players_enabled: false,
    max_concurrent_games: 3,
    current_usage: {
      total_individual_limits: 0,
      max_limit: 100,
      available: 100,
      usage_percentage: 0
    }
  });
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);

  // Generate cache key based on current filters and pagination
  const generateCacheKey = useCallback(() => {
    return JSON.stringify({
      page: currentPage,
      limit: pageSize,
      filters,
      priorityFields
    });
  }, [currentPage, pageSize, filters, priorityFields]);

  // Check if cache is valid
  const isCacheValid = useCallback((cacheKey) => {
    if (!cache.data || !cache.timestamp || cache.key !== cacheKey) {
      return false;
    }
    return Date.now() - cache.timestamp < CACHE_DURATION;
  }, [cache]);

  // Update cache
  const updateCache = useCallback((data, cacheKey) => {
    setCache({
      data,
      timestamp: Date.now(),
      key: cacheKey
    });
  }, []);

  // Debounced search handler
  const handleSearchChange = useCallback((value) => {
    setSearchTerm(value);
    
    // Clear existing timeout
    if (searchDebounceTimeout) {
      clearTimeout(searchDebounceTimeout);
    }
    
    // Set new timeout for 500ms debounce
    const timeout = setTimeout(() => {
      setFilters(prev => ({
        ...prev,
        search: value
      }));
      setCurrentPage(1); // Reset to first page on search
    }, 500);
    
    setSearchDebounceTimeout(timeout);
  }, [searchDebounceTimeout]);

  // Enhanced API operation with caching
  const executeOperation = useCallback(async (endpoint, method = 'GET', data = null, useCache = false) => {
    try {
      setLoading(true);
      setError(null);
      
      // Check cache for GET requests
      if (method === 'GET' && useCache) {
        const cacheKey = generateCacheKey();
        if (isCacheValid(cacheKey)) {
          console.log('Using cached data for Human-bots');
          setHumanBots(cache.data.bots || []);
          setTotalPages(cache.data.pagination?.total_pages || 1);
          setLoading(false);
          return cache.data;
        }
      }
      
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
      
      // Update cache for GET requests
      if (method === 'GET' && useCache) {
        const cacheKey = generateCacheKey();
        updateCache(response.data, cacheKey);
      }
      
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
        // Handle standard error with detail
        else if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : 'Validation error';
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
      
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, filters, priorityFields, addNotification]);

  const characters = [
    { value: 'STABLE', label: 'Стабильный', description: 'Ровные небольшие ставки' },
    { value: 'AGGRESSIVE', label: 'Агрессивный', description: 'Крупные ставки, высокий риск' },
    { value: 'CAUTIOUS', label: 'Осторожный', description: 'Мелкие ставки, низкая волатильность' },
    { value: 'BALANCED', label: 'Балансированный', description: 'Средние ставки и стратегия' },
    { value: 'IMPULSIVE', label: 'Импульсивный', description: 'Случайные всплески активности' },
    { value: 'ANALYST', label: 'Аналитик', description: 'Адаптивная стратегия' },
    { value: 'MIMIC', label: 'Мимик', description: 'Копирует поведение оппонентов' }
  ];

  const [createFormData, setCreateFormData] = useState({
    name: '',
    character: 'BALANCED',
    gender: 'male',
    min_bet: 1,
    max_bet: 100,
    bet_limit: 12,
    bet_limit_amount: 300,
    win_percentage: 40,
    loss_percentage: 40,
    draw_percentage: 20,
    min_delay: 30,
    max_delay: 120,
    use_commit_reveal: true,
    logging_level: 'INFO',
    can_play_with_other_bots: true,
    can_play_with_players: true,
    // Individual delay settings for bot-to-bot games
    bot_min_delay_seconds: 30,
    bot_max_delay_seconds: 120,
    // Individual delay settings for bot-to-player games  
    player_min_delay_seconds: 30,
    player_max_delay_seconds: 120,
    // Individual concurrent games limit
    max_concurrent_games: 3
  });

  const [bulkCreateData, setBulkCreateData] = useState({
    count: 10,
    character: 'BALANCED',
    min_bet_range: [1, 50],
    max_bet_range: [50, 200],
    bet_limit_range: [12, 12],
    win_percentage: 40,
    loss_percentage: 40,
    draw_percentage: 20,
    delay_range: [30, 120],
    min_delay: 30,
    max_delay: 120,
    use_commit_reveal: true,
    logging_level: 'INFO',
    // Additional settings for bulk creation
    can_play_with_other_bots: true,
    can_play_with_players: true,
    // Delay ranges for bot-to-bot games
    bot_min_delay_range: [30, 120],
    bot_max_delay_range: [30, 120],
    // Delay ranges for bot-to-player games
    player_min_delay_range: [30, 120], 
    player_max_delay_range: [30, 120],
    bots: []
  });

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showBulkCreateForm, setShowBulkCreateForm] = useState(false);
  const [editingBot, setEditingBot] = useState(null);

  const fetchHumanBots = useCallback(async (useCache = true) => {
    try {
      setLoadingPriority(true);
      
      // Build query parameters with all new filters
      const params = {
        page: currentPage.toString(),
        limit: pageSize.toString(),
        priority_fields: priorityFields.toString()
      };
      
      // Add search parameter
      if (filters.search && filters.search.trim()) {
        params.search = filters.search.trim();
      }
      
      // Add filter parameters
      if (filters.character) {
        params.character = filters.character;
      }
      
      if (filters.is_active !== null) {
        params.is_active = filters.is_active.toString();
      }
      
      if (filters.min_bet_range) {
        params.min_bet_range = filters.min_bet_range;
      }
      
      if (filters.max_bet_range) {
        params.max_bet_range = filters.max_bet_range;
      }
      
      // Add sorting parameters
      if (filters.sort_by) {
        params.sort_by = filters.sort_by;
      }
      
      if (filters.sort_order) {
        params.sort_order = filters.sort_order;
      }
      
      // Build query string
      const queryString = new URLSearchParams(params).toString();
      
      const response = await executeOperation(`/admin/human-bots?${queryString}`, 'GET', null, useCache);
      
      if (response.success !== false) {
        setHumanBots(response.bots || []);
        
        if (response.pagination) {
          setTotalPages(response.pagination.total_pages || 1);
        }
        
        // Log performance information if available
        if (response.metadata) {
          console.log('Human-bots query performance:', response.metadata.query_performance);
          console.log('Cache timestamp:', new Date(response.metadata.cache_timestamp * 1000));
        }
      }
    } catch (error) {
      console.error('Ошибка получения Human-ботов:', error);
      addNotification('Ошибка загрузки списка Human-ботов', 'error');
    } finally {
      setLoadingPriority(false);
    }
  }, [currentPage, pageSize, filters, priorityFields, executeOperation, addNotification]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await executeOperation('/admin/human-bots/stats', 'GET');
      if (response.success !== false) {
        setStats(response);
      }
    } catch (error) {
      console.error('Ошибка получения статистики:', error);
    }
  }, [executeOperation]);

  const fetchGlobalSettings = useCallback(async () => {
    try {
      const response = await executeOperation('/admin/human-bots/settings', 'GET');
      if (response.success !== false) {
        setGlobalSettings(response.settings || {});
      }
    } catch (error) {
      console.error('Ошибка получения глобальных настроек:', error);
    }
  }, [executeOperation]);

  // Add missing state for global settings
  const [globalSettings, setGlobalSettings] = useState({});

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        console.log('Auto-refreshing Human-bots data...');
        fetchHumanBots(false); // Don't use cache for auto-refresh
        fetchStats();
        fetchGlobalSettings(); // Add global settings refresh
      }, AUTO_REFRESH_INTERVAL);
      
      setRefreshInterval(interval);
      
      return () => {
        if (interval) {
          clearInterval(interval);
        }
      };
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh, fetchHumanBots, fetchStats, fetchGlobalSettings]);

  // Fetch data when dependencies change
  useEffect(() => {
    fetchHumanBots();
    fetchStats();
    fetchGlobalSettings(); // Add global settings fetch
  }, [currentPage, pageSize, filters, priorityFields]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (searchDebounceTimeout) {
        clearTimeout(searchDebounceTimeout);
      }
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [searchDebounceTimeout, refreshInterval]);

  // Initialize bot list when bulk create form opens
  useEffect(() => {
    if (showBulkCreateForm) {
      // Load bot names if not already loaded
      if (botNames.length === 0) {
        fetchBotNames();
      }
      
      // Initialize bots if needed
      if (bulkCreateData.bots.length !== bulkCreateData.count) {
        const bots = initializeBots(bulkCreateData.count);
        setBulkCreateData(prev => ({
          ...prev,
          bots: bots
        }));
      }
    }
  }, [showBulkCreateForm, bulkCreateData.count, botNames.length]);

  // Regenerate bot names when botNames list changes (useful when names are updated via names management tab)
  useEffect(() => {
    if (showBulkCreateForm && botNames.length > 0 && bulkCreateData.bots.length > 0) {
      // Regenerate names for existing bots using the new names list
      const updatedBots = bulkCreateData.bots.map(bot => {
        const randomName = generateRandomName();
        return {
          ...bot,
          name: randomName.name,
          gender: randomName.gender
        };
      });
      setBulkCreateData(prev => ({
        ...prev,
        bots: updatedBots
      }));
    }
  }, [botNames]);

  const fetchHumanBotSettings = async () => {
    try {
      setSettingsLoading(true);
      const response = await executeOperation('/admin/human-bots/settings', 'GET');
      if (response.success !== false) {
        setHumanBotSettings(response.settings);
      }
    } catch (error) {
      console.error('Ошибка получения настроек Human-ботов:', error);
    } finally {
      setSettingsLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setSettingsSaving(true);
      const response = await executeOperation('/admin/human-bots/update-settings', 'POST', {
        max_active_bets_human: humanBotSettings.max_active_bets_human,
        auto_play_enabled: humanBotSettings.auto_play_enabled || false,
        min_delay_seconds: humanBotSettings.min_delay_seconds || 1,
        max_delay_seconds: humanBotSettings.max_delay_seconds || 3600,
        play_with_players_enabled: humanBotSettings.play_with_players_enabled || false,
        max_concurrent_games: humanBotSettings.max_concurrent_games || 3
      });
      
      if (response.success !== false) {
        addNotification(response.message || 'Настройки сохранены успешно', 'success');
        await fetchHumanBotSettings();
        if (response.adjusted_bots_count > 0) {
          await fetchHumanBots();
        }
      }
    } catch (error) {
      console.error('Ошибка сохранения настроек:', error);
    } finally {
      setSettingsSaving(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'settings') {
      fetchHumanBotSettings();
    }
  }, [activeTab]);

  const handleCreateBot = async () => {
    if (loading) {
      return;
    }

    if (createFormData.win_percentage + createFormData.loss_percentage + createFormData.draw_percentage !== 100) {
      addNotification('Сумма процентов должна равняться 100%', 'error');
      return;
    }

    if (!editingBot) {
      const existingBot = humanBots.find(bot => 
        bot.name.toLowerCase() === createFormData.name.toLowerCase()
      );
      if (existingBot) {
        addNotification(`Бот с именем "${createFormData.name}" уже существует. Пожалуйста, выберите другое имя.`, 'error');
        return;
      }
    }

    // Validate delay settings
    if (createFormData.can_play_with_other_bots) {
      if (createFormData.bot_min_delay_seconds >= createFormData.bot_max_delay_seconds) {
        addNotification('Минимальная задержка для ботов должна быть меньше максимальной', 'error');
        return;
      }
    }
    
    if (createFormData.can_play_with_players) {  
      if (createFormData.player_min_delay_seconds >= createFormData.player_max_delay_seconds) {
        addNotification('Минимальная задержка для игроков должна быть меньше максимальной', 'error');
        return;
      }
    }

    try {
      let response;
      const isCreating = !editingBot;
      
      if (editingBot) {
        response = await executeOperation(`/admin/human-bots/${editingBot.id}`, 'PUT', createFormData);
      } else {
        response = await executeOperation('/admin/human-bots', 'POST', createFormData);
      }
      
      const botName = createFormData.name || 'Human-бот';
      
      if (isCreating) {
        addNotification(`Human-бот "${botName}" успешно создан`, 'success');
      } else {
        addNotification(`Human-бот "${botName}" успешно отредактирован`, 'success');
      }
      
      setShowCreateForm(false);
      setEditingBot(null);
      
      if (isCreating) {
        setCreateFormData({
          name: '',
          character: 'BALANCED',
          gender: 'male',
          min_bet: 1,
          max_bet: 100,
          bet_limit: 12,
          bet_limit_amount: 300,
          win_percentage: 40,
          loss_percentage: 40,
          draw_percentage: 20,
          min_delay: 30,
          max_delay: 120,
          use_commit_reveal: true,
          logging_level: 'INFO',
          can_play_with_other_bots: true,
          can_play_with_players: true,
          // Reset delay settings
          bot_min_delay_seconds: 30,
          bot_max_delay_seconds: 120,
          player_min_delay_seconds: 30,
          player_max_delay_seconds: 120
        });
      }
      
      const globalRefresh = getGlobalLobbyRefresh();
      globalRefresh.triggerLobbyRefresh();
      
      await fetchHumanBots();
      
    } catch (error) {
      console.error('Ошибка создания/редактирования Human-бота:', error);
      
      if (error.message.includes('Bot name already exists')) {
        addNotification(`Бот с именем "${createFormData.name}" уже существует. Пожалуйста, выберите другое имя.`, 'error');
      } else {
        const operation = editingBot ? 'редактировании' : 'создании';
        addNotification(`Ошибка при ${operation} бота. Попробуйте еще раз.`, 'error');
      }
    }
  };

  const handleBulkCreate = async () => {
    if (bulkCreateData.win_percentage + bulkCreateData.loss_percentage + bulkCreateData.draw_percentage !== 100) {
      addNotification('Сумма процентов должна равняться 100%', 'error');
      return;
    }

    try {
      const payload = {
        ...bulkCreateData,
        delay_range: [bulkCreateData.min_delay || 30, bulkCreateData.max_delay || 120],
        min_delay: bulkCreateData.min_delay || 30,
        max_delay: bulkCreateData.max_delay || 120,
        // Include new delay settings
        can_play_with_other_bots: bulkCreateData.can_play_with_other_bots,
        can_play_with_players: bulkCreateData.can_play_with_players,
        bot_min_delay_range: bulkCreateData.bot_min_delay_range,
        bot_max_delay_range: bulkCreateData.bot_max_delay_range,
        player_min_delay_range: bulkCreateData.player_min_delay_range,
        player_max_delay_range: bulkCreateData.player_max_delay_range,
        bots: bulkCreateData.bots || []
      };

      const response = await executeOperation('/admin/human-bots/bulk-create', 'POST', payload);
      if (response.success !== false) {
        addNotification(`Массовое создание завершено: создано ${response.created_count || bulkCreateData.count} Human-ботов`, 'success');
        setShowBulkCreateForm(false);
        fetchHumanBots();
        fetchStats();
        
        if (response.failed_count && response.failed_count > 0) {
          addNotification(`Создано ${response.created_count} ботов, не удалось создать: ${response.failed_count}`, 'warning');
        } else {
          addNotification(`Успешно создано ${response.created_count} ботов`, 'success');
        }
        
        setBulkCreateData({
          count: 10,
          character: 'BALANCED',
          min_bet_range: [1, 50],
          max_bet_range: [50, 200],
          bet_limit_range: [12, 12],
          win_percentage: 40,
          loss_percentage: 40,
          draw_percentage: 20,
          delay_range: [30, 120],
          min_delay: 30,
          max_delay: 120,
          use_commit_reveal: true,
          logging_level: 'INFO',
          // Reset additional settings
          can_play_with_other_bots: true,
          can_play_with_players: true,
          bot_min_delay_range: [30, 120],
          bot_max_delay_range: [30, 120],
          player_min_delay_range: [30, 120],
          player_max_delay_range: [30, 120],
          bots: []
        });
      }
    } catch (error) {
      console.error('Ошибка массового создания Human-ботов:', error);
    }
  };

  const handleToggleStatus = async (botId) => {
    try {
      const response = await executeOperation(`/admin/human-bots/${botId}/toggle-status`, 'POST');
      if (response.success !== false) {
        const bot = humanBots.find(b => b.id === botId);
        const botName = bot?.name || 'Human-бот';
        const action = bot?.is_active ? 'деактивирован' : 'активирован';
        addNotification(`Human-бот "${botName}" успешно ${action}`, 'success');
        fetchHumanBots();
        fetchStats();
      }
    } catch (error) {
      console.error('Ошибка переключения статуса:', error);
    }
  };

  const handleDeleteBot = async (botId, botName) => {
    confirm({
      title: "Удаление Human-бота",
      message: `Вы уверены, что хотите удалить Human-бота "${botName}"?`,
      type: "danger",
      onConfirm: async () => {
        try {
          const response = await executeOperation(`/admin/human-bots/${botId}`, 'DELETE');
          if (response.success !== false) {
            fetchHumanBots();
            fetchStats();
          }
        } catch (error) {
          console.error('Ошибка удаления Human-бота:', error);
        }
      }
    });
  };

  const handleToggleAll = async (activate) => {
    const confirmed = await confirm({
      title: `${activate ? 'Активация' : 'Деактивация'} всех Human-ботов`,
      message: `Вы уверены, что хотите ${activate ? 'активировать' : 'деактивировать'} всех Human-ботов?`,
      type: activate ? "success" : "warning"
    });
    
    if (confirmed) {
      try {
        const response = await executeOperation('/admin/human-bots/toggle-all', 'POST', { activate });
        if (response.success !== false) {
          const action = activate ? 'активированы' : 'деактивированы';
          const count = response.affected_count || 0;
          addNotification(`Массовая операция завершена: ${count} Human-ботов ${action}`, 'success');
          fetchHumanBots();
          fetchStats();
          addNotification(`${activate ? 'Активировано' : 'Деактивировано'} ${response.affected_count} ботов`, 'success');
        }
      } catch (error) {
        console.error('Ошибка массового переключения статуса:', error);
      }
    }
  };

  const getCharacterLabel = (character) => {
    const found = characters.find(c => c.value === character);
    return found ? found.label : character;
  };

  const getStatusColor = (isActive) => {
    return isActive ? 'green' : 'red';
  };

  const formatCurrency = (amount) => {
    return `$${amount.toFixed(2)}`;
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  const generateRandomName = () => {
    // If bot names are available from the server, use them
    if (botNames.length > 0) {
      const randomName = botNames[Math.floor(Math.random() * botNames.length)];
      const gender = Math.random() > 0.5 ? 'male' : 'female';
      return { 
        name: randomName, 
        gender 
      };
    }
    
    // Fallback to static names if server names are not available
    const maleNames = ['Alikhan', 'Nurzhan', 'Ayan', 'Ruslan', 'Bekzat','Yerlan', 'Zhanibek', 'Omir', 'Azamat', 'Temirlan',   'Aleksandr', 'Dmitriy', 'Maksim', 'Andrey', 'Sergey', 'Aleksey', 'Vladimir', 'Pavel', 'Roman', 'Artem'];
    const femaleNames = ['Aigerim', 'Gulnara', 'Aizhan', 'Sabina', 'Saule', 'Dilnaz', 'Madina', 'Zhanar', 'Aruzhan', 'Gulzhana', 'Anna', 'Mariya', 'Elena', 'Natalya', 'Olga', 'Tatyana', 'Irina', 'Svetlana', 'Ekaterina', 'Viktoriya'];
    
    const gender = Math.random() > 0.5 ? 'male' : 'female';
    const firstName = gender === 'male' ? 
      maleNames[Math.floor(Math.random() * maleNames.length)] : 
      femaleNames[Math.floor(Math.random() * femaleNames.length)];
    
    return { 
      name: firstName, 
      gender 
    };
  };

  const initializeBots = (count) => {
    const bots = [];
    for (let i = 0; i < count; i++) {
      const randomBot = generateRandomName();
      
      // Generate random delay values for each bot
      const botMinDelay = Math.floor(Math.random() * (bulkCreateData.bot_min_delay_range[1] - bulkCreateData.bot_min_delay_range[0] + 1)) + bulkCreateData.bot_min_delay_range[0];
      const botMaxDelay = Math.floor(Math.random() * (bulkCreateData.bot_max_delay_range[1] - bulkCreateData.bot_max_delay_range[0] + 1)) + bulkCreateData.bot_max_delay_range[0];
      const playerMinDelay = Math.floor(Math.random() * (bulkCreateData.player_min_delay_range[1] - bulkCreateData.player_min_delay_range[0] + 1)) + bulkCreateData.player_min_delay_range[0];
      const playerMaxDelay = Math.floor(Math.random() * (bulkCreateData.player_max_delay_range[1] - bulkCreateData.player_max_delay_range[0] + 1)) + bulkCreateData.player_max_delay_range[0];
      
      bots.push({
        id: i,
        name: randomBot.name,
        gender: randomBot.gender,
        can_play_with_other_bots: bulkCreateData.can_play_with_other_bots,
        can_play_with_players: bulkCreateData.can_play_with_players,
        bot_min_delay_seconds: Math.min(botMinDelay, botMaxDelay),
        bot_max_delay_seconds: Math.max(botMinDelay, botMaxDelay),
        player_min_delay_seconds: Math.min(playerMinDelay, playerMaxDelay),
        player_max_delay_seconds: Math.max(playerMinDelay, playerMaxDelay)
      });
    }
    return bots;
  };

  const updateBotCount = (count) => {
    const bots = initializeBots(count);
    setBulkCreateData({
      ...bulkCreateData,
      count: count,
      bots: bots
    });
  };

  const updateBotData = (botId, field, value) => {
    const updatedBots = bulkCreateData.bots.map(bot => 
      bot.id === botId ? { ...bot, [field]: value } : bot
    );
    setBulkCreateData({
      ...bulkCreateData,
      bots: updatedBots
    });
  };

  const handleResetTotalGames = async () => {
    const confirmed = await confirm({
      title: 'Сброс счетчика всего игр',
      message: 'Вы уверены, что хотите сбросить счетчик всего игр Human-ботов? Это действие нельзя отменить.',
      type: 'warning'
    });

    if (confirmed) {
      try {
        await executeOperation('/admin/human-bots/reset-total-games', 'POST');
        addNotification('Счетчик всего игр успешно сброшен', 'success');
        await fetchStats();
      } catch (error) {
        console.error('Ошибка сброса счетчика всего игр:', error);
        addNotification(`Ошибка при сбросе счетчика: ${error.message}`, 'error');
      }
    }
  };

  const handleResetPeriodRevenue = async () => {
    const confirmed = await confirm({
      title: 'Сброс дохода за период',
      message: 'Вы уверены, что хотите сбросить доход за период? Это действие нельзя отменить.',
      type: 'warning'
    });

    if (confirmed) {
      try {
        await executeOperation('/admin/human-bots/reset-period-revenue', 'POST');
        addNotification('Доход за период успешно сброшен', 'success');
        await fetchStats();
      } catch (error) {
        console.error('Ошибка сброса дохода за период:', error);
        addNotification(`Ошибка при сбросе дохода: ${error.message}`, 'error');
      }
    }
  };

  // Human Bot Names Management Functions
  const fetchBotNames = async () => {
    setNamesLoading(true);
    try {
      const response = await executeOperation('/admin/human-bots/names', 'GET');
      setBotNames(response.names || []);
    } catch (error) {
      console.error('Ошибка загрузки имен ботов:', error);
      addNotification(`Ошибка загрузки имен: ${error.message}`, 'error');
    } finally {
      setNamesLoading(false);
    }
  };

  const handleSaveBulkNames = async () => {
    if (!bulkNamesInput.trim()) {
      addNotification('Введите имена ботов', 'error');
      return;
    }

    const confirmed = await confirm({
      title: 'Обновить список имен',
      message: 'Вы уверены, что хотите заменить текущий список имен? Это действие нельзя отменить.',
      type: 'warning'
    });

    if (confirmed) {
      setNamesSaving(true);
      try {
        const names = bulkNamesInput
          .split('\n')
          .map(name => name.trim())
          .filter(name => name);

        await executeOperation('/admin/human-bots/names', 'PUT', { names });
        addNotification('Список имен успешно обновлен', 'success');
        await fetchBotNames();
        setShowBulkNamesEditor(false);
        setBulkNamesInput('');
      } catch (error) {
        console.error('Ошибка обновления имен:', error);
        addNotification(`Ошибка обновления: ${error.message}`, 'error');
      } finally {
        setNamesSaving(false);
      }
    }
  };

  const handleAddName = async () => {
    if (!newNameInput.trim()) {
      addNotification('Введите имя бота', 'error');
      return;
    }

    setNamesSaving(true);
    try {
      await executeOperation('/admin/human-bots/names/add', 'POST', { names: [newNameInput.trim()] });
      addNotification('Имя успешно добавлено', 'success');
      await fetchBotNames();
      setNewNameInput('');
    } catch (error) {
      console.error('Ошибка добавления имени:', error);
      addNotification(`Ошибка добавления: ${error.message}`, 'error');
    } finally {
      setNamesSaving(false);
    }
  };

  const handleRemoveName = async (nameToRemove) => {
    const confirmed = await confirm({
      title: 'Удалить имя',
      message: `Вы уверены, что хотите удалить имя "${nameToRemove}"?`,
      type: 'warning'
    });

    if (confirmed) {
      setNamesSaving(true);
      try {
        await executeOperation(`/admin/human-bots/names/${encodeURIComponent(nameToRemove)}`, 'DELETE');
        addNotification('Имя успешно удалено', 'success');
        await fetchBotNames();
      } catch (error) {
        console.error('Ошибка удаления имени:', error);
        addNotification(`Ошибка удаления: ${error.message}`, 'error');
      } finally {
        setNamesSaving(false);
      }
    }
  };

  const handleOpenBulkEditor = () => {
    setBulkNamesInput(botNames.join('\n'));
    setShowBulkNamesEditor(true);
  };

  // Load bot names when names tab is selected
  useEffect(() => {
    if (activeTab === 'names' && botNames.length === 0) {
      fetchBotNames();
    }
  }, [activeTab]);

  return (
    <div className="human-bots-management">
      <div className="bots-header">
        <h2>Управление Human-ботами</h2>
      </div>

      {/* Табы */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="flex border-b border-border-primary">
          <button
            onClick={() => setActiveTab('bots')}
            className={`flex-1 px-6 py-4 text-center font-rajdhani font-bold transition-colors ${
              activeTab === 'bots'
                ? 'bg-accent-primary text-white border-b-2 border-accent-primary'
                : 'text-text-secondary hover:text-white hover:bg-surface-sidebar'
            }`}
          >
            📋 Список ботов
          </button>
          <button
            onClick={() => setActiveTab('names')}
            className={`flex-1 px-6 py-4 text-center font-rajdhani font-bold transition-colors ${
              activeTab === 'names'
                ? 'bg-accent-primary text-white border-b-2 border-accent-primary'
                : 'text-text-secondary hover:text-white hover:bg-surface-sidebar'
            }`}
          >
            📝 Имена ботов
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`flex-1 px-6 py-4 text-center font-rajdhani font-bold transition-colors ${
              activeTab === 'settings'
                ? 'bg-accent-primary text-white border-b-2 border-accent-primary'
                : 'text-text-secondary hover:text-white hover:bg-surface-sidebar'
            }`}
          >
            ⚙️ Настройки
          </button>
        </div>

        {/* Содержимое табов */}
        <div className="p-6">
          {activeTab === 'bots' && (
            <div className="space-y-6">
              {/* Действия для ботов */}
              <div className="flex flex-wrap gap-3 mb-6">
                <button
                  className="styled-btn btn-primary"
                  onClick={() => setShowCreateForm(true)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Создать бота
                </button>
                <button
                  className="styled-btn btn-secondary"
                  onClick={() => setShowBulkCreateForm(true)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  Массовое создание
                </button>
                <button
                  className="styled-btn btn-success"
                  onClick={() => handleToggleAll(true)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Активировать всех
                </button>
                <button
                  className="styled-btn btn-warning"
                  onClick={() => handleToggleAll(false)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Деактивировать всех
                </button>
              </div>

              {/* Statistics */}
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Количество ботов</h3>
                  <div className="stat-value">{stats.total_bots || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Ожидающие</h3>
                  <div className="stat-value">{stats.total_bets || 0}</div>
                </div>
                <div className="stat-card">
                  <h3>Активные</h3>
                  <div className="stat-value">{stats.active_games || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="flex justify-between items-center">
                    <h3>Всего Игр</h3>
                    <button
                      onClick={() => handleResetTotalGames()}
                      className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                      title="Сбросить счетчик всего игр"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
                  <div className="stat-value">{stats.total_games_played || 0}</div>
                </div>
                <div className="stat-card">
                  <div className="flex justify-between items-center">
                    <h3>Доход за Период</h3>
                    <button
                      onClick={() => handleResetPeriodRevenue()}
                      className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                      title="Сбросить доход за период"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                    </button>
                  </div>
                  <div className="stat-value">{formatCurrency(stats.period_revenue || 0)}</div>
                </div>
              </div>

              {/* Enhanced Search and Filters */}
              <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-rajdhani font-bold text-white">🔍 Поиск и фильтры</h3>
                  <div className="flex items-center space-x-4">
                    {/* Auto-refresh toggle */}
                    <div className="flex items-center space-x-2">
                      <label className="text-sm text-text-secondary">Авто-обновление:</label>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={autoRefresh}
                          onChange={(e) => setAutoRefresh(e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent-primary peer-focus:ring-opacity-25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-accent-primary"></div>
                      </label>
                    </div>
                    
                    {/* Priority fields toggle */}
                    <div className="flex items-center space-x-2">
                      <label className="text-sm text-text-secondary">Приоритетная загрузка:</label>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={priorityFields}
                          onChange={(e) => setPriorityFields(e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 peer-focus:ring-opacity-25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-green-600"></div>
                      </label>
                    </div>

                    {/* Manual refresh button */}
                    <button
                      onClick={() => {
                        fetchHumanBots(false);
                        fetchStats();
                        fetchGlobalSettings(); // Add global settings refresh
                        addNotification('Данные обновлены', 'success');
                      }}
                      disabled={loading || loadingPriority}
                      className="px-3 py-1 bg-accent-primary text-white text-sm rounded hover:bg-accent-primary-dark disabled:opacity-50 transition-colors"
                    >
                      {loading || loadingPriority ? '⏳' : '🔄'} Обновить
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Search by name */}
                  <div className="filter-group">
                    <label className="block text-sm font-medium text-text-secondary mb-2">Поиск по имени:</label>
                    <div className="relative">
                      <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => handleSearchChange(e.target.value)}
                        placeholder="Введите имя бота..."
                        className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                      />
                      {searchTerm && (
                        <button
                          onClick={() => handleSearchChange('')}
                          className="absolute right-2 top-1/2 transform -translate-y-1/2 text-text-secondary hover:text-white"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Character filter */}
                  <div className="filter-group">
                    <label className="block text-sm font-medium text-text-secondary mb-2">Характер:</label>
                    <select 
                      value={filters.character} 
                      onChange={(e) => {
                        setFilters({...filters, character: e.target.value});
                        setCurrentPage(1);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                    >
                      <option value="">Все характеры</option>
                      {characters.map(char => (
                        <option key={char.value} value={char.value}>
                          {char.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Status filter */}
                  <div className="filter-group">
                    <label className="block text-sm font-medium text-text-secondary mb-2">Статус:</label>
                    <select 
                      value={filters.is_active === null ? '' : filters.is_active.toString()} 
                      onChange={(e) => {
                        setFilters({...filters, is_active: e.target.value === '' ? null : e.target.value === 'true'});
                        setCurrentPage(1);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                    >
                      <option value="">Все статусы</option>
                      <option value="true">Активные</option>
                      <option value="false">Неактивные</option>
                    </select>
                  </div>

                  {/* Page size selector */}
                  <div className="filter-group">
                    <label className="block text-sm font-medium text-text-secondary mb-2">Элементов на странице:</label>
                    <select 
                      value={pageSize} 
                      onChange={(e) => {
                        setPageSize(parseInt(e.target.value));
                        setCurrentPage(1);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                    >
                      <option value={5}>5</option>
                      <option value={10}>10</option>
                      <option value={20}>20</option>
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                    </select>
                  </div>
                </div>

                {/* Advanced filters row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  {/* Min bet range filter */}
                  <div className="filter-group">
                    <label className="block text-sm font-medium text-text-secondary mb-2">Диапазон мин. ставок:</label>
                    <input
                      type="text"
                      value={filters.min_bet_range}
                      onChange={(e) => {
                        setFilters({...filters, min_bet_range: e.target.value});
                        setCurrentPage(1);
                      }}
                      placeholder="Например: 1-50"
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                    />
                  </div>

                  {/* Sort by */}
                  <div className="filter-group">
                    <label className="block text-sm font-medium text-text-secondary mb-2">Сортировка:</label>
                    <select 
                      value={filters.sort_by} 
                      onChange={(e) => {
                        setFilters({...filters, sort_by: e.target.value});
                        setCurrentPage(1);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                    >
                      <option value="created_at">По дате создания</option>
                      <option value="name">По имени</option>
                      <option value="character">По характеру</option>
                      <option value="is_active">По статусу</option>
                      <option value="min_bet">По мин. ставке</option>
                      <option value="max_bet">По макс. ставке</option>
                    </select>
                  </div>

                  {/* Sort order */}
                  <div className="filter-group">
                    <label className="block text-sm font-medium text-text-secondary mb-2">Порядок:</label>
                    <select 
                      value={filters.sort_order} 
                      onChange={(e) => {
                        setFilters({...filters, sort_order: e.target.value});
                        setCurrentPage(1);
                      }}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                    >
                      <option value="desc">По убыванию</option>
                      <option value="asc">По возрастанию</option>
                    </select>
                  </div>
                </div>

                {/* Clear filters button */}
                <div className="mt-4 flex justify-end">
                  <button
                    onClick={() => {
                      setFilters({
                        search: '',
                        character: '',
                        is_active: null,
                        min_bet_range: '',
                        max_bet_range: '',
                        sort_by: 'created_at',
                        sort_order: 'desc'
                      });
                      setSearchTerm('');
                      setCurrentPage(1);
                    }}
                    className="px-4 py-2 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition-colors"
                  >
                    🗑️ Очистить фильтры
                  </button>
                </div>
              </div>

              {/* Enhanced Pagination */}
              <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <span className="text-white font-roboto text-sm">
                      Показано {humanBots.length} из {stats.total_bots || 0} ботов
                    </span>
                    {cache.timestamp && (
                      <span className="text-text-secondary text-xs">
                        Последнее обновление: {new Date(cache.timestamp).toLocaleTimeString('ru-RU')}
                      </span>
                    )}
                    {(loading || loadingPriority) && (
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-accent-primary"></div>
                        <span className="text-text-secondary text-sm">
                          {loadingPriority ? 'Загрузка приоритетных данных...' : 'Загрузка...'}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {/* Pagination buttons */}
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                      disabled={currentPage <= 1 || loading}
                      className="px-3 py-1 bg-surface-sidebar text-white text-sm rounded border border-border-primary hover:bg-surface-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      ← Назад
                    </button>
                    
                    <span className="text-white text-sm">
                      Страница {currentPage} из {totalPages}
                    </span>
                    
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                      disabled={currentPage >= totalPages || loading}
                      className="px-3 py-1 bg-surface-sidebar text-white text-sm rounded border border-border-primary hover:bg-surface-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Вперед →
                    </button>
                  </div>
                </div>
              </div>

              {/* Human Bots List */}
              <HumanBotsList 
                humanBots={humanBots}
                loading={loading || loadingPriority}
                currentPage={currentPage}
                totalPages={totalPages}
                pageSize={pageSize}
                priorityFields={priorityFields}
                stats={stats} // Pass stats to child component
                globalSettings={globalSettings} // Pass global settings to child component
                onPageChange={setCurrentPage}
                onEditBot={(bot) => {
                  setEditingBot(bot);
                  setCreateFormData({
                    name: bot.name || '',
                    character: bot.character || 'BALANCED',
                    gender: bot.gender || 'male',
                    min_bet: bot.min_bet || 1,
                    max_bet: bot.max_bet || 100,
                    bet_limit: bot.bet_limit || 12,
                    bet_limit_amount: bot.bet_limit_amount || 300,
                    win_percentage: bot.win_percentage || 40,
                    loss_percentage: bot.loss_percentage || 40,
                    draw_percentage: bot.draw_percentage || 20,
                    min_delay: bot.min_delay || 30,
                    max_delay: bot.max_delay || 120,
                    use_commit_reveal: bot.use_commit_reveal !== undefined ? bot.use_commit_reveal : true,
                    logging_level: bot.logging_level || 'INFO',
                    can_play_with_other_bots: bot.can_play_with_other_bots !== undefined ? bot.can_play_with_other_bots : true,
                    can_play_with_players: bot.can_play_with_players !== undefined ? bot.can_play_with_players : true
                  });
                  setShowCreateForm(true);
                }}
                onCreateBot={() => setShowCreateForm(true)}
                onRefresh={() => {
                  fetchHumanBots(false);
                  fetchStats();
                  fetchGlobalSettings(); // Add global settings refresh
                }}
              />
            </div>
          )}

          {activeTab === 'names' && (
            <div className="space-y-6">
              {/* Управление именами Human-ботов */}
              <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-600 rounded-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="font-rajdhani text-xl font-bold text-white">
                        Управление именами Human-ботов
                      </h3>
                      <p className="text-text-secondary font-roboto">
                        Редактирование списка имен для массового создания ботов
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-text-secondary text-sm">
                      Всего имен: {botNames.length}
                    </span>
                    <button
                      onClick={() => fetchBotNames()}
                      disabled={namesLoading}
                      className="px-3 py-1 bg-accent-primary text-white text-sm rounded hover:bg-accent-primary-dark disabled:opacity-50 transition-colors"
                    >
                      {namesLoading ? '⏳' : '🔄'} Обновить
                    </button>
                  </div>
                </div>

                {namesLoading ? (
                  <div className="text-center py-8">
                    <div className="text-accent-primary text-2xl mb-2">⏳</div>
                    <p className="text-text-secondary">Загрузка имен...</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Быстрое добавление имени */}
                    <div className="bg-surface-sidebar rounded-lg p-4">
                      <h4 className="font-rajdhani font-bold text-white mb-3">➕ Добавить новое имя</h4>
                      <div className="flex items-center space-x-4">
                        <input
                          type="text"
                          value={newNameInput}
                          onChange={(e) => setNewNameInput(e.target.value)}
                          placeholder="Введите имя бота..."
                          maxLength={50}
                          className="flex-1 px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                          disabled={namesSaving}
                          onKeyPress={(e) => e.key === 'Enter' && handleAddName()}
                        />
                        <button
                          onClick={handleAddName}
                          disabled={namesSaving || !newNameInput.trim()}
                          className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-opacity-80 transition-colors disabled:opacity-50"
                        >
                          {namesSaving ? 'Добавление...' : 'Добавить'}
                        </button>
                      </div>
                    </div>

                    {/* Массовое редактирование */}
                    <div className="bg-surface-sidebar rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-rajdhani font-bold text-white">📝 Массовое редактирование</h4>
                        <button
                          onClick={handleOpenBulkEditor}
                          disabled={namesSaving}
                          className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50"
                        >
                          Редактировать все
                        </button>
                      </div>
                      <p className="text-text-secondary text-sm">
                        💡 Используйте массовое редактирование для замены всего списка имен сразу
                      </p>
                    </div>

                    {/* Список текущих имен */}
                    <div className="bg-surface-sidebar rounded-lg p-4">
                      <h4 className="font-rajdhani font-bold text-white mb-3">📋 Текущие имена ({botNames.length})</h4>
                      {botNames.length === 0 ? (
                        <div className="text-center py-4 text-text-secondary">
                          Список имен пуст
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 max-h-96 overflow-y-auto">
                          {botNames.map((name, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between bg-surface-card border border-border-primary rounded-lg px-3 py-2"
                            >
                              <span className="text-white font-roboto text-sm truncate flex-1 mr-2">
                                {name}
                              </span>
                              <button
                                onClick={() => handleRemoveName(name)}
                                disabled={namesSaving}
                                className="text-red-400 hover:text-red-300 disabled:opacity-50 transition-colors"
                                title="Удалить имя"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              {/* Настройки лимитов Human-ботов */}
              <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-green-600 rounded-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="font-rajdhani text-xl font-bold text-white">
                        Глобальные настройки Human-ботов
                      </h3>
                      <p className="text-text-secondary font-roboto">
                        Управление общими лимитами для всех Human-ботов
                      </p>
                    </div>
                  </div>
                </div>

                {settingsLoading ? (
                  <div className="text-center py-8">
                    <div className="text-accent-primary text-2xl mb-2">⏳</div>
                    <p className="text-text-secondary">Загрузка настроек...</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Текущее использование */}
                    <div className="bg-surface-sidebar rounded-lg p-4">
                      <h4 className="font-rajdhani font-bold text-white mb-3">Текущее использование</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="text-accent-primary font-bold text-lg">
                            {stats.total_bets || 0}
                          </div>
                          <div className="text-text-secondary text-sm">Использовано</div>
                        </div>
                        <div className="text-center">
                          <div className="text-white font-bold text-lg">
                            {humanBotSettings.current_usage?.max_limit || 100}
                          </div>
                          <div className="text-text-secondary text-sm">Максимум</div>
                        </div>
                        <div className="text-center">
                          <div className="text-green-400 font-bold text-lg">
                            {Math.max(0, (humanBotSettings.current_usage?.max_limit || 100) - (stats.total_bets || 0))}
                          </div>
                          <div className="text-text-secondary text-sm">Доступно</div>
                        </div>
                        <div className="text-center">
                          <div className="text-orange-400 font-bold text-lg">
                            {Math.round(((stats.total_bets || 0) / (humanBotSettings.current_usage?.max_limit || 100)) * 100)}%
                          </div>
                          <div className="text-text-secondary text-sm">Использование</div>
                        </div>
                      </div>

                      {/* Прогресс бар */}
                      <div className="mt-4">
                        <div className="bg-surface-primary rounded-full h-3 overflow-hidden">
                          <div 
                            className="bg-accent-primary h-full transition-all duration-300"
                            style={{ 
                              width: `${Math.min(Math.round(((stats.total_bets || 0) / (humanBotSettings.current_usage?.max_limit || 100)) * 100), 100)}%` 
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Настройки автоигры между Human-ботами */}
                    <div className="bg-surface-sidebar rounded-lg p-4">
                      <h4 className="font-rajdhani font-bold text-white mb-3">🎮 Автоигра между Human-ботами</h4>
                      <div className="space-y-4">
                        {/* Глобальный переключатель */}
                        <div className="flex items-center justify-between">
                          <div>
                            <label className="font-rajdhani font-bold text-white">
                              Включить автоигру между Human-ботами
                            </label>
                            <p className="text-text-secondary text-sm">
                              Позволяет Human-ботам автоматически присоединяться к ставкам других Human-ботов и игроков
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={humanBotSettings.auto_play_enabled || false}
                              onChange={(e) => setHumanBotSettings({
                                ...humanBotSettings,
                                auto_play_enabled: e.target.checked
                              })}
                              className="sr-only peer"
                              disabled={settingsSaving}
                            />
                            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent-primary peer-focus:ring-opacity-25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-primary"></div>
                          </label>
                        </div>

                        {/* Настройка диапазона задержки */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block font-rajdhani font-bold text-white mb-2">
                              Минимальная задержка (секунды)
                            </label>
                            <input
                              type="number"
                              min="1"
                              max="3600"
                              value={humanBotSettings.min_delay_seconds || 1}
                              onChange={(e) => setHumanBotSettings({
                                ...humanBotSettings,
                                min_delay_seconds: parseInt(e.target.value) || 1
                              })}
                              className="w-full px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                              disabled={settingsSaving}
                            />
                          </div>
                          <div>
                            <label className="block font-rajdhani font-bold text-white mb-2">
                              Максимальная задержка (секунды)
                            </label>
                            <input
                              type="number"
                              min="1"
                              max="3600"
                              value={humanBotSettings.max_delay_seconds || 3600}
                              onChange={(e) => setHumanBotSettings({
                                ...humanBotSettings,
                                max_delay_seconds: parseInt(e.target.value) || 3600
                              })}
                              className="w-full px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                              disabled={settingsSaving}
                            />
                          </div>
                        </div>
                        
                        {/* Новое поле для максимального количества одновременных игр */}
                        <div>
                          <label className="block font-rajdhani font-bold text-white mb-2">
                            Макс. одновременных игр
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="50"
                            value={humanBotSettings.max_concurrent_games || 3}
                            onChange={(e) => setHumanBotSettings({
                              ...humanBotSettings,
                              max_concurrent_games: parseInt(e.target.value) || 3
                            })}
                            className="w-full px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                            disabled={settingsSaving}
                          />
                          <p className="text-text-secondary text-xs mt-1">
                            Максимальное количество игр, в которых Human-бот может участвовать одновременно
                          </p>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                          <div className="flex-1 text-text-secondary text-sm">
                            💡 Human-боты будут присоединяться к доступным ставкам с случайной задержкой от {humanBotSettings.min_delay_seconds || 1} до {humanBotSettings.max_delay_seconds || 3600} секунд ({Math.round((humanBotSettings.max_delay_seconds || 3600) / 60)} минут)
                          </div>
                          <button
                            onClick={handleSaveSettings}
                            disabled={settingsSaving}
                            className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-opacity-80 transition-colors disabled:opacity-50"
                          >
                            {settingsSaving ? 'Сохранение...' : 'Сохранить'}
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Новый переключатель для игры с игроками */}
                    <div className="bg-surface-sidebar rounded-lg p-4">
                      <h4 className="font-rajdhani font-bold text-white mb-3">👥 Игра с живыми игроками</h4>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <label className="font-rajdhani font-bold text-white">
                              Включить игру с Игроками
                            </label>
                            <p className="text-text-secondary text-sm">
                              Позволяет Human-ботам играть с живыми игроками
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={humanBotSettings.play_with_players_enabled || false}
                              onChange={(e) => setHumanBotSettings({
                                ...humanBotSettings,
                                play_with_players_enabled: e.target.checked
                              })}
                              className="sr-only peer"
                              disabled={settingsSaving}
                            />
                            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent-primary peer-focus:ring-opacity-25 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent-primary"></div>
                          </label>
                        </div>
                      </div>
                    </div>

                    {/* Настройка максимального лимита */}
                    <div className="space-y-4">
                      <div>
                        <label className="block font-rajdhani font-bold text-white mb-2">
                          Максимум активных ставок для всех Human-ботов
                        </label>
                        <div className="flex items-center space-x-4">
                          <input
                            type="number"
                            min="1"
                            max="1000000"
                            value={humanBotSettings.max_active_bets_human || 100}
                            onChange={(e) => setHumanBotSettings({
                              ...humanBotSettings,
                              max_active_bets_human: parseInt(e.target.value) || 100
                            })}
                            className="flex-1 max-w-xs px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                            disabled={settingsSaving}
                          />
                          <button
                            onClick={handleSaveSettings}
                            disabled={settingsSaving}
                            className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-opacity-80 transition-colors disabled:opacity-50"
                          >
                            {settingsSaving ? 'Сохранение...' : 'Сохранить'}
                          </button>
                        </div>
                        <p className="text-text-secondary text-sm mt-2">
                          💡 При уменьшении лимита индивидуальные лимиты ботов будут автоматически скорректированы пропорционально
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Bot Form */}
      {showCreateForm && (
        <div className="modal-overlay">
          <div className="modal-content large-modal styled-modal">
            <div className="modal-header">
              <div className="modal-title">
                <svg className="modal-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <h3>{editingBot ? 'Редактировать Human-бота' : 'Создать Human-бота'}</h3>
              </div>
              <button 
                type="button" 
                className="modal-close"
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingBot(null);
                }}
              >
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <form onSubmit={(e) => { e.preventDefault(); handleCreateBot(); }}>
              {/* Основная информация */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4>Основная информация</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                      </svg>
                      Имя бота *
                    </label>
                    <input
                      type="text"
                      value={createFormData.name}
                      onChange={(e) => setCreateFormData({...createFormData, name: e.target.value})}
                      placeholder="Введите имя бота"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      Характер *
                    </label>
                    <select
                      value={createFormData.character}
                      onChange={(e) => setCreateFormData({...createFormData, character: e.target.value})}
                    >
                      {characters.map(char => (
                        <option key={char.value} value={char.value} title={char.description}>
                          {char.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      Пол *
                    </label>
                    <select
                      value={createFormData.gender}
                      onChange={(e) => setCreateFormData({...createFormData, gender: e.target.value})}
                    >
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Настройки ставок */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                  <h4>Настройки ставок</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      Мин. ставка (гемы)
                    </label>
                    <input
                      type="number"
                      step="1"
                      min="1"
                      value={createFormData.min_bet}
                      onChange={(e) => setCreateFormData({...createFormData, min_bet: parseInt(e.target.value) || 1})}
                      placeholder="1"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Макс. ставка (гемы)
                    </label>
                    <input
                      type="number"
                      step="1"
                      min="1"
                      value={createFormData.max_bet}
                      onChange={(e) => setCreateFormData({...createFormData, max_bet: parseInt(e.target.value) || 1})}
                      placeholder="100"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      Лимит ставок
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={createFormData.bet_limit}
                      onChange={(e) => setCreateFormData({...createFormData, bet_limit: parseInt(e.target.value)})}
                      placeholder="12"
                    />
                    <small className="form-help">Макс. количество одновременных ставок (1-100)</small>
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                      </svg>
                      Ограничение суммы ставок
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100000"
                      value={createFormData.bet_limit_amount}
                      onChange={(e) => setCreateFormData({...createFormData, bet_limit_amount: parseFloat(e.target.value) || 300})}
                      placeholder="300"
                    />
                    <small className="form-help">Макс. сумма ставки для участия как оппонент (1-100000)</small>
                  </div>
                </div>
              </div>

              {/* Настройки результатов */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h4>Настройки результатов</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      % Побед
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={createFormData.win_percentage}
                      onChange={(e) => setCreateFormData({...createFormData, win_percentage: parseFloat(e.target.value)})}
                      placeholder="40"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      % Поражений
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={createFormData.loss_percentage}
                      onChange={(e) => setCreateFormData({...createFormData, loss_percentage: parseFloat(e.target.value)})}
                      placeholder="40"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L12 12m6.364 6.364L12 12m0 0L5.636 5.636M12 12l6.364-6.364M12 12l-6.364 6.364" />
                      </svg>
                      % Ничьих
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={createFormData.draw_percentage}
                      onChange={(e) => setCreateFormData({...createFormData, draw_percentage: parseFloat(e.target.value)})}
                      placeholder="20"
                    />
                  </div>
                </div>
                <div className="form-help-block">
                  <svg className="help-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Сумма всех процентов должна равняться 100%
                </div>
              </div>

              {/* Настройки времени */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4>Настройки времени</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      Мин. задержка (сек)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="300"
                      value={createFormData.min_delay}
                      onChange={(e) => setCreateFormData({...createFormData, min_delay: parseInt(e.target.value)})}
                      placeholder="30"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Макс. задержка (сек)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="300"
                      value={createFormData.max_delay}
                      onChange={(e) => setCreateFormData({...createFormData, max_delay: parseInt(e.target.value)})}
                      placeholder="120"
                    />
                  </div>
                </div>
              </div>

              {/* Дополнительные настройки */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  </svg>
                  <h4>Дополнительные настройки</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Уровень логирования
                    </label>
                    <select
                      value={createFormData.logging_level}
                      onChange={(e) => setCreateFormData({...createFormData, logging_level: e.target.value})}
                    >
                      <option value="INFO">INFO</option>
                      <option value="DEBUG">DEBUG</option>
                    </select>
                  </div>
                </div>
                
                <div className="checkbox-group">
                  <div className="checkbox-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={createFormData.use_commit_reveal}
                        onChange={(e) => setCreateFormData({...createFormData, use_commit_reveal: e.target.checked})}
                      />
                      <svg className="checkbox-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      Использовать Commit-Reveal
                    </label>
                  </div>
                  <div className="checkbox-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={createFormData.can_play_with_other_bots || false}
                        onChange={(e) => setCreateFormData({...createFormData, can_play_with_other_bots: e.target.checked})}
                      />
                      <svg className="checkbox-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      Играть с другими Human-ботами
                    </label>
                    <small className="form-help">Разрешить боту автоматически играть с другими Human-ботами</small>
                    
                    {createFormData.can_play_with_other_bots && (
                      <div className="delay-settings mt-3 ml-6 p-3 bg-surface-sidebar rounded border border-border-primary">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Минимальная задержка (секунды) *</label>
                            <input
                              type="number"
                              min="1"
                              max="11000"
                              value={createFormData.bot_min_delay_seconds}
                              onChange={(e) => {
                                const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 30));
                                setCreateFormData({...createFormData, bot_min_delay_seconds: value});
                              }}
                              className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Максимальная задержка (секунды) *</label>
                            <input
                              type="number"
                              min="1"
                              max="11000"
                              value={createFormData.bot_max_delay_seconds}
                              onChange={(e) => {
                                const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 120));
                                setCreateFormData({...createFormData, bot_max_delay_seconds: value});
                              }}
                              className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                              required
                            />
                          </div>
                        </div>
                        {createFormData.bot_min_delay_seconds >= createFormData.bot_max_delay_seconds && (
                          <p className="text-red-400 text-xs mt-1">⚠️ Минимальная задержка должна быть меньше максимальной</p>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="checkbox-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={createFormData.can_play_with_players || false}
                        onChange={(e) => setCreateFormData({...createFormData, can_play_with_players: e.target.checked})}
                      />
                      <svg className="checkbox-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                      </svg>
                      Играть с живыми игроками
                    </label>
                    <small className="form-help">Разрешить боту автоматически играть с живыми игроками</small>
                    
                    {createFormData.can_play_with_players && (
                      <div className="delay-settings mt-3 ml-6 p-3 bg-surface-sidebar rounded border border-border-primary">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Минимальная задержка (секунды) *</label>
                            <input
                              type="number"
                              min="1"
                              max="11000"
                              value={createFormData.player_min_delay_seconds}
                              onChange={(e) => {
                                const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 30));
                                setCreateFormData({...createFormData, player_min_delay_seconds: value});
                              }}
                              className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Максимальная задержка (секунды) *</label>
                            <input
                              type="number"
                              min="1"
                              max="11000"
                              value={createFormData.player_max_delay_seconds}
                              onChange={(e) => {
                                const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 120));
                                setCreateFormData({...createFormData, player_max_delay_seconds: value});
                              }}
                              className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                              required
                            />
                          </div>
                        </div>
                        {createFormData.player_min_delay_seconds >= createFormData.player_max_delay_seconds && (
                          <p className="text-red-400 text-xs mt-1">⚠️ Минимальная задержка должна быть меньше максимальной</p>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                      Максимальное количество одновременных игр
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={createFormData.max_concurrent_games}
                      onChange={(e) => setCreateFormData({...createFormData, max_concurrent_games: Math.max(1, Math.min(100, parseInt(e.target.value) || 3))})}
                      placeholder="3"
                    />
                    <small className="form-help">Максимальное количество игр, в которых бот может участвовать одновременно</small>
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                <button 
                  type="submit" 
                  className="styled-btn btn-primary"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <svg className="w-5 h-5 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {editingBot ? 'Сохранение...' : 'Создание...'}
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {editingBot ? 'Сохранить изменения' : 'Создать бота'}
                    </>
                  )}
                </button>
                <button 
                  type="button" 
                  className="styled-btn btn-secondary"
                  onClick={() => {
                    setShowCreateForm(false);
                    setEditingBot(null);
                  }}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Create Form */}
      {showBulkCreateForm && (
        <div className="modal-overlay">
          <div className="modal-content large-modal styled-modal">
            <div className="modal-header">
              <div className="modal-title">
                <svg className="modal-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <h3>Массовое создание Human-ботов</h3>
              </div>
              <button 
                type="button" 
                className="modal-close"
                onClick={() => setShowBulkCreateForm(false)}
              >
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <form onSubmit={(e) => { e.preventDefault(); handleBulkCreate(); }}>
              {/* Общие настройки */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h4>Общие настройки</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                      </svg>
                      Количество ботов
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={bulkCreateData.count}
                      onChange={(e) => updateBotCount(parseInt(e.target.value) || 1)}
                      placeholder="10"
                    />
                    <small className="form-help">Максимум 50 ботов за раз</small>
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      Характер для всех
                    </label>
                    <select
                      value={bulkCreateData.character}
                      onChange={(e) => setBulkCreateData({...bulkCreateData, character: e.target.value})}
                    >
                      {characters.map(char => (
                        <option key={char.value} value={char.value} title={char.description}>
                          {char.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Диапазоны ставок */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                  <h4>Диапазоны ставок</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      Диапазон мин. ставок (гемы)
                    </label>
                    <div className="range-inputs">
                      <input
                        type="number"
                        step="1"
                        placeholder="От"
                        value={bulkCreateData.min_bet_range[0]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          min_bet_range: [parseInt(e.target.value) || 1, bulkCreateData.min_bet_range[1]]
                        })}
                      />
                      <span className="range-separator">—</span>
                      <input
                        type="number"
                        step="1"
                        placeholder="До"
                        value={bulkCreateData.min_bet_range[1]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          min_bet_range: [bulkCreateData.min_bet_range[0], parseInt(e.target.value) || 1]
                        })}
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Диапазон макс. ставок (гемы)
                    </label>
                    <div className="range-inputs">
                      <input
                        type="number"
                        step="1"
                        placeholder="От"
                        value={bulkCreateData.max_bet_range[0]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          max_bet_range: [parseInt(e.target.value) || 1, bulkCreateData.max_bet_range[1]]
                        })}
                      />
                      <span className="range-separator">—</span>
                      <input
                        type="number"
                        step="1"
                        placeholder="До"
                        value={bulkCreateData.max_bet_range[1]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          max_bet_range: [bulkCreateData.max_bet_range[0], parseInt(e.target.value) || 1]
                        })}
                      />
                    </div>
                  </div>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      Диапазон лимитов ставок
                    </label>
                    <div className="range-inputs">
                      <input
                        type="number"
                        min="1"
                        max="100"
                        placeholder="От"
                        value={bulkCreateData.bet_limit_range[0]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          bet_limit_range: [parseInt(e.target.value), bulkCreateData.bet_limit_range[1]]
                        })}
                      />
                      <span className="range-separator">—</span>
                      <input
                        type="number"
                        min="1"
                        max="100"
                        placeholder="До"
                        value={bulkCreateData.bet_limit_range[1]}
                        onChange={(e) => setBulkCreateData({
                          ...bulkCreateData, 
                          bet_limit_range: [bulkCreateData.bet_limit_range[0], parseInt(e.target.value)]
                        })}
                      />
                    </div>
                    <small className="form-help">Диапазон максимального количества одновременных ставок (1-100)</small>
                  </div>
                </div>
              </div>

              {/* Настройки результатов */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <h4>Настройки результатов для всех ботов</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      % Побед
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={bulkCreateData.win_percentage}
                      onChange={(e) => setBulkCreateData({...bulkCreateData, win_percentage: parseFloat(e.target.value)})}
                      placeholder="40"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      % Поражений
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={bulkCreateData.loss_percentage}
                      onChange={(e) => setBulkCreateData({...bulkCreateData, loss_percentage: parseFloat(e.target.value)})}
                      placeholder="40"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L12 12m6.364 6.364L12 12m0 0L5.636 5.636M12 12l6.364-6.364M12 12l-6.364 6.364" />
                      </svg>
                      % Ничьих
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={bulkCreateData.draw_percentage}
                      onChange={(e) => setBulkCreateData({...bulkCreateData, draw_percentage: parseFloat(e.target.value)})}
                      placeholder="20"
                    />
                  </div>
                </div>
                <div className="form-help-block">
                  <svg className="help-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Сумма всех процентов должна равняться 100%
                </div>
              </div>

              {/* Настройки задержки */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4>Настройки задержки</h4>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      Мин. задержка (сек)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="3600"
                      value={bulkCreateData.min_delay || 30}
                      onChange={(e) => {
                        const value = parseInt(e.target.value) || 30;
                        setBulkCreateData({
                          ...bulkCreateData, 
                          min_delay: value,
                          delay_range: [value, bulkCreateData.max_delay || 120]
                        });
                      }}
                      placeholder="30"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <svg className="label-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Макс. задержка (сек)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="3600"
                      value={bulkCreateData.max_delay || 120}
                      onChange={(e) => {
                        const value = parseInt(e.target.value) || 120;
                        setBulkCreateData({
                          ...bulkCreateData, 
                          max_delay: value,
                          delay_range: [bulkCreateData.min_delay || 30, value]
                        });
                      }}
                      placeholder="120"
                    />
                  </div>
                </div>
                <div className="form-help-block">
                  <svg className="help-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Задержка между действиями Human-ботов (от 1 секунды до 1 часа)
                </div>
              </div>

              {/* Дополнительные настройки */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <h4>Дополнительные настройки</h4>
                </div>

                <div className="form-group checkbox-section">
                  <div className="checkbox-group">
                    <div className="checkbox-item">
                      <label>
                        <input
                          type="checkbox"
                          checked={bulkCreateData.can_play_with_other_bots || false}
                          onChange={(e) => setBulkCreateData({...bulkCreateData, can_play_with_other_bots: e.target.checked})}
                        />
                        <svg className="checkbox-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        Играть с другими Human-ботами
                      </label>
                      <small className="form-help">Разрешить ботам автоматически играть с другими Human-ботами</small>
                      
                      {bulkCreateData.can_play_with_other_bots && (
                        <div className="delay-settings mt-3 ml-6 p-3 bg-surface-sidebar rounded border border-border-primary">
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-sm font-medium text-text-secondary mb-1">Диапазон мин. задержки (секунды) *</label>
                              <div className="flex space-x-2">
                                <input
                                  type="number"
                                  min="1"
                                  max="11000"
                                  value={bulkCreateData.bot_min_delay_range[0]}
                                  onChange={(e) => {
                                    const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 30));
                                    setBulkCreateData({...bulkCreateData, bot_min_delay_range: [value, bulkCreateData.bot_min_delay_range[1]]});
                                  }}
                                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                                  required
                                />
                                <span className="self-center text-text-secondary">-</span>
                                <input
                                  type="number"
                                  min="1"
                                  max="11000"
                                  value={bulkCreateData.bot_min_delay_range[1]}
                                  onChange={(e) => {
                                    const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 120));
                                    setBulkCreateData({...bulkCreateData, bot_min_delay_range: [bulkCreateData.bot_min_delay_range[0], value]});
                                  }}
                                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                                  required
                                />
                              </div>
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-text-secondary mb-1">Диапазон макс. задержки (секунды) *</label>
                              <div className="flex space-x-2">
                                <input
                                  type="number"
                                  min="1"
                                  max="11000"
                                  value={bulkCreateData.bot_max_delay_range[0]}
                                  onChange={(e) => {
                                    const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 30));
                                    setBulkCreateData({...bulkCreateData, bot_max_delay_range: [value, bulkCreateData.bot_max_delay_range[1]]});
                                  }}
                                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                                  required
                                />
                                <span className="self-center text-text-secondary">-</span>
                                <input
                                  type="number"
                                  min="1"
                                  max="11000"
                                  value={bulkCreateData.bot_max_delay_range[1]}
                                  onChange={(e) => {
                                    const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 120));
                                    setBulkCreateData({...bulkCreateData, bot_max_delay_range: [bulkCreateData.bot_max_delay_range[0], value]});
                                  }}
                                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                                  required
                                />
                              </div>
                            </div>
                          </div>
                          <p className="text-xs text-text-secondary mt-2">Каждый бот получит случайные значения из указанного диапазона</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="checkbox-item">
                      <label>
                        <input
                          type="checkbox"
                          checked={bulkCreateData.can_play_with_players || false}
                          onChange={(e) => setBulkCreateData({...bulkCreateData, can_play_with_players: e.target.checked})}
                        />
                        <svg className="checkbox-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                        </svg>
                        Играть с живыми игроками
                      </label>
                      <small className="form-help">Разрешить ботам автоматически играть с живыми игроками</small>
                      
                      {bulkCreateData.can_play_with_players && (
                        <div className="delay-settings mt-3 ml-6 p-3 bg-surface-sidebar rounded border border-border-primary">
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-sm font-medium text-text-secondary mb-1">Диапазон мин. задержки (секунды) *</label>
                              <div className="flex space-x-2">
                                <input
                                  type="number"
                                  min="1"
                                  max="11000"
                                  value={bulkCreateData.player_min_delay_range[0]}
                                  onChange={(e) => {
                                    const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 30));
                                    setBulkCreateData({...bulkCreateData, player_min_delay_range: [value, bulkCreateData.player_min_delay_range[1]]});
                                  }}
                                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                                  required
                                />
                                <span className="self-center text-text-secondary">-</span>
                                <input
                                  type="number"
                                  min="1"
                                  max="11000"
                                  value={bulkCreateData.player_min_delay_range[1]}
                                  onChange={(e) => {
                                    const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 120));
                                    setBulkCreateData({...bulkCreateData, player_min_delay_range: [bulkCreateData.player_min_delay_range[0], value]});
                                  }}
                                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                                  required
                                />
                              </div>
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-text-secondary mb-1">Диапазон макс. задержки (секунды) *</label>
                              <div className="flex space-x-2">
                                <input
                                  type="number"
                                  min="1"
                                  max="11000"
                                  value={bulkCreateData.player_max_delay_range[0]}
                                  onChange={(e) => {
                                    const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 30));
                                    setBulkCreateData({...bulkCreateData, player_max_delay_range: [value, bulkCreateData.player_max_delay_range[1]]});
                                  }}
                                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                                  required
                                />
                                <span className="self-center text-text-secondary">-</span>
                                <input
                                  type="number"
                                  min="1"
                                  max="11000"
                                  value={bulkCreateData.player_max_delay_range[1]}
                                  onChange={(e) => {
                                    const value = Math.max(1, Math.min(11000, parseInt(e.target.value) || 120));
                                    setBulkCreateData({...bulkCreateData, player_max_delay_range: [bulkCreateData.player_max_delay_range[0], value]});
                                  }}
                                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                                  required
                                />
                              </div>
                            </div>
                          </div>
                          <p className="text-xs text-text-secondary mt-2">Каждый бот получит случайные значения из указанного диапазона</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Настройки отдельных ботов */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <h4>Настройки отдельных ботов</h4>
                  <button
                    type="button"
                    onClick={() => {
                      // Regenerate names for all bots
                      const updatedBots = bulkCreateData.bots.map(bot => {
                        const randomName = generateRandomName();
                        return {
                          ...bot,
                          name: randomName.name,
                          gender: randomName.gender
                        };
                      });
                      setBulkCreateData(prev => ({
                        ...prev,
                        bots: updatedBots
                      }));
                    }}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors ml-auto"
                    title="Обновить имена ботов"
                  >
                    🔄 Обновить имена
                  </button>
                </div>
                
                <div className="bot-configuration-container">
                  {bulkCreateData.bots.map((bot, index) => (
                    <div key={bot.id} className="bot-config-item">
                      <div className="bot-config-header">
                        <span className="bot-number">#{index + 1}</span>
                      </div>
                      <div className="bot-config-fields">
                        <div className="form-group">
                          <label>Имя бота</label>
                          <input
                            type="text"
                            value={bot.name}
                            onChange={(e) => updateBotData(bot.id, 'name', e.target.value)}
                            placeholder="Имя бота"
                          />
                        </div>
                        <div className="form-group">
                          <label>Пол</label>
                          <select
                            value={bot.gender}
                            onChange={(e) => updateBotData(bot.id, 'gender', e.target.value)}
                          >
                            <option value="male">Мужчина</option>
                            <option value="female">Женщина</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Предпросмотр */}
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  <h4>Предпросмотр</h4>
                </div>
                
                <div className="bulk-preview">
                  <div className="preview-card">
                    <div className="preview-header">
                      <svg className="preview-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      <span>Будет создано {bulkCreateData.count} ботов</span>
                    </div>
                    <div className="preview-details">
                      <p><strong>Характер:</strong> {characters.find(c => c.value === bulkCreateData.character)?.label}</p>
                      <p><strong>Мин. ставки:</strong> {bulkCreateData.min_bet_range[0]} - {bulkCreateData.min_bet_range[1]} гемов</p>
                      <p><strong>Макс. ставки:</strong> {bulkCreateData.max_bet_range[0]} - {bulkCreateData.max_bet_range[1]} гемов</p>
                      <p><strong>Лимиты:</strong> {bulkCreateData.bet_limit_range[0]} - {bulkCreateData.bet_limit_range[1]} ставок</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                <button type="submit" className="styled-btn btn-primary">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  Создать {bulkCreateData.count} ботов
                </button>
                <button 
                  type="button" 
                  className="styled-btn btn-secondary"
                  onClick={() => setShowBulkCreateForm(false)}
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Names Editor Modal */}
      {showBulkNamesEditor && (
        <div className="modal-overlay">
          <div className="modal-content large-modal styled-modal">
            <div className="modal-header">
              <div className="modal-title">
                <svg className="modal-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                <h3>Массовое редактирование имен</h3>
              </div>
              <button 
                type="button" 
                className="modal-close"
                onClick={() => {
                  setShowBulkNamesEditor(false);
                  setBulkNamesInput('');
                }}
              >
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-section">
                <div className="section-header">
                  <svg className="section-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4>Редактирование списка имен</h4>
                </div>
                
                <div className="space-y-4">
                  <div className="bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-3 rounded-lg">
                    <div className="flex items-center">
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                      <div>
                        <p className="font-bold">Внимание!</p>
                        <p className="text-sm">Это действие заменит весь текущий список имен. Убедитесь, что все имена корректны.</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-white font-rajdhani font-bold mb-2">
                      Список имен (по одному на строку):
                    </label>
                    <textarea
                      value={bulkNamesInput}
                      onChange={(e) => setBulkNamesInput(e.target.value)}
                      placeholder="Введите имена ботов, по одному на строку..."
                      className="w-full h-96 px-4 py-3 bg-surface-card border border-border-primary rounded-lg text-white font-roboto resize-none focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                      disabled={namesSaving}
                    />
                    <div className="flex items-center justify-between mt-2">
                      <p className="text-text-secondary text-sm">
                        Строк: {bulkNamesInput.split('\n').filter(line => line.trim()).length}
                      </p>
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={() => setBulkNamesInput('')}
                          disabled={namesSaving}
                          className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 disabled:opacity-50"
                        >
                          Очистить
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            const lines = bulkNamesInput.split('\n');
                            const uniqueLines = [...new Set(lines.map(line => line.trim()).filter(line => line))];
                            setBulkNamesInput(uniqueLines.join('\n'));
                          }}
                          disabled={namesSaving}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          Удалить дубликаты
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button 
                type="button"
                onClick={handleSaveBulkNames}
                disabled={namesSaving || !bulkNamesInput.trim()}
                className="styled-btn btn-primary"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {namesSaving ? 'Сохранение...' : 'Сохранить список'}
              </button>
              <button 
                type="button" 
                className="styled-btn btn-secondary"
                onClick={() => {
                  setShowBulkNamesEditor(false);
                  setBulkNamesInput('');
                }}
                disabled={namesSaving}
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <ConfirmationModal {...confirmationModal} />
      <InputModal {...inputModal} />
    </div>
  );
};

export default HumanBotsManagement;