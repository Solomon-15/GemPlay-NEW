import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NotificationAdmin = ({ user }) => {
  const [activeTab, setActiveTab] = useState('send');
  const [loading, setLoading] = useState(false);
  const [analytics, setAnalytics] = useState({});
  const { showSuccessRU, showErrorRU } = useNotifications();

  // Состояние для отправки уведомлений
  const [notification, setNotification] = useState({
    type: 'admin_notification',
    title: '',
    message: '',
    priority: 'info',
    target_users: null, // null = всем пользователям
    expires_at: null
  });

  // Состояние для целевых пользователей
  const [targetUsers, setTargetUsers] = useState('all'); // 'all' или 'specific'
  const [specificUsers, setSpecificUsers] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [foundUsers, setFoundUsers] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);

  // Состояние для детальной аналитики отправок
  const [detailedAnalytics, setDetailedAnalytics] = useState([]);
  const [detailedLoading, setDetailedLoading] = useState(false);
  const [detailedPagination, setDetailedPagination] = useState({
    current_page: 1,
    per_page: 50,
    total_items: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false
  });
  const [filters, setFilters] = useState({
    type_filter: '',
    date_from: '',
    date_to: ''
  });
  const [expandedNotification, setExpandedNotification] = useState(null);
  const [resendingId, setResendingId] = useState(null);
  const [showResendModal, setShowResendModal] = useState(null);
  const [resendOption, setResendOption] = useState('unread'); // 'unread' or 'all'

  // Типы уведомлений
  const notificationTypes = [
    { value: 'admin_notification', label: 'Админское уведомление', icon: '👑' },
    { value: 'system_message', label: 'Системное сообщение', icon: '⚙️' },
    { value: 'gem_gift', label: 'Подарок гемов', icon: '💎' },
    { value: 'commission_freeze', label: 'Заморозка комиссии', icon: '❄️' },
    { value: 'match_result', label: 'Результат игры', icon: '🎯' },
    { value: 'bet_accepted', label: 'Ставка принята', icon: '✅' }
  ];

  // Приоритеты уведомлений
  const priorities = [
    { value: 'info', label: 'Информация', color: 'text-blue-400', bgColor: 'bg-blue-500' },
    { value: 'warning', label: 'Предупреждение', color: 'text-yellow-400', bgColor: 'bg-yellow-500' },
    { value: 'error', label: 'Критическое', color: 'text-red-400', bgColor: 'bg-red-500' }
  ];

  // Загрузка аналитики
  const fetchAnalytics = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/notifications/analytics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.data.success) {
        setAnalytics(response.data);
      }
    } catch (error) {
      console.error('Error fetching notification analytics:', error);
      showErrorRU('Ошибка загрузки аналитики уведомлений');
    }
  }, [showErrorRU]);

  // Поиск пользователей
  const searchUsers = useCallback(async (query) => {
    if (!query.trim()) {
      setFoundUsers([]);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` },
        params: { search: query, limit: 10 }
      });

      if (response.data.success) {
        setFoundUsers(response.data.users || []);
      }
    } catch (error) {
      console.error('Error searching users:', error);
    }
  }, []);

  // Добавить пользователя в список получателей
  const addUserToSelection = (user) => {
    if (!selectedUsers.find(u => u.id === user.id)) {
      setSelectedUsers([...selectedUsers, user]);
    }
    setUserSearch('');
    setFoundUsers([]);
  };

  // Удалить пользователя из списка получателей
  const removeUserFromSelection = (userId) => {
    setSelectedUsers(selectedUsers.filter(u => u.id !== userId));
  };

  // Отправка уведомления
  const sendNotification = async () => {
    if (!notification.title.trim() || !notification.message.trim()) {
      showErrorRU('Заполните заголовок и сообщение');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // Подготовка данных для отправки
      const payload = {
        type: notification.type,
        title: notification.title.trim(),
        message: notification.message.trim(),
        priority: notification.priority,
        target_users: targetUsers === 'all' ? null : selectedUsers.map(u => u.id),
        expires_at: notification.expires_at || null
      };

      const response = await axios.post(`${API}/admin/notifications/broadcast`, payload, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.data.success) {
        showSuccessRU(`Уведомление отправлено ${response.data.sent_count} пользователям`);
        
        // Очистка формы
        setNotification({
          type: 'admin_notification',
          title: '',
          message: '',
          priority: 'info',
          target_users: null,
          expires_at: null
        });
        setSelectedUsers([]);
        setTargetUsers('all');
        
        // Обновление аналитики
        fetchAnalytics();
      }
    } catch (error) {
      console.error('Error sending notification:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка отправки уведомления';
      showErrorRU(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка аналитики при монтировании
  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  // Поиск пользователей с задержкой
  useEffect(() => {
    const timeoutId = setTimeout(() => searchUsers(userSearch), 300);
    return () => clearTimeout(timeoutId);
  }, [userSearch, searchUsers]);

  // Функции для детальной аналитики
  const fetchDetailedAnalytics = useCallback(async (page = 1) => {
    try {
      console.log('fetchDetailedAnalytics called:', { page, filters });
      setDetailedLoading(true);
      const token = localStorage.getItem('token');
      
      if (!token) {
        console.error('No auth token found');
        showErrorRU('Необходима авторизация');
        return;
      }
      
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '50'
      });
      
      if (filters.type_filter) params.append('type_filter', filters.type_filter);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      
      console.log('Making API request to:', `${API}/admin/notifications/detailed-analytics?${params}`);
      
      const response = await axios.get(`${API}/admin/notifications/detailed-analytics?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      console.log('API response:', response.data);

      if (response.data.success) {
        setDetailedAnalytics(response.data.data);
        setDetailedPagination(response.data.pagination);
        console.log('Data set:', response.data.data.length, 'notifications');
      } else {
        console.error('API returned success: false');
        showErrorRU('Ошибка получения данных');
      }
    } catch (error) {
      console.error('Error fetching detailed analytics:', error);
      showErrorRU('Ошибка загрузки детальной аналитики: ' + (error.response?.data?.detail || error.message));
    } finally {
      setDetailedLoading(false);
    }
  }, [filters, showErrorRU]);

  const handleResendToUnread = async (notificationId) => {
    try {
      setResendingId(notificationId);
      const token = localStorage.getItem('token');
      
      const response = await axios.post(`${API}/admin/notifications/resend-to-unread`, 
        { notification_id: notificationId },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (response.data.success) {
        showSuccessRU(`Повторно отправлено ${response.data.resent_count} пользователям`);
        fetchDetailedAnalytics(detailedPagination.current_page);
      }
    } catch (error) {
      console.error('Error resending notification:', error);
      showErrorRU('Ошибка повторной отправки уведомления');
    } finally {
      setResendingId(null);
    }
  };

  const handleResendClick = (notificationId) => {
    setShowResendModal(notificationId);
    setResendOption('unread');
  };

  const handleResendConfirm = async () => {
    if (!showResendModal) return;
    
    try {
      setResendingId(showResendModal);
      const token = localStorage.getItem('token');
      
      let endpoint, payload;
      if (resendOption === 'unread') {
        endpoint = `${API}/admin/notifications/resend-to-unread`;
        payload = { notification_id: showResendModal };
      } else {
        // Найти оригинальное уведомление для повторной отправки всем
        const originalNotification = detailedAnalytics.find(n => n.notification_id === showResendModal);
        if (!originalNotification) {
          showErrorRU('Уведомление не найдено');
          return;
        }
        
        endpoint = `${API}/admin/notifications/broadcast`;
        payload = {
          type: originalNotification.type,
          title: originalNotification.title,
          message: originalNotification.message,
          priority: 'info', // Устанавливаем дефолтный приоритет
          target_users: null // Отправить всем пользователям
        };
      }
      
      const response = await axios.post(endpoint, payload, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.data.success) {
        const count = response.data.resent_count || response.data.sent_count;
        if (resendOption === 'unread') {
          showSuccessRU(`Повторно отправлено ${count} непрочитавшим пользователям`);
        } else {
          showSuccessRU(`Отправлено ${count} пользователям`);
        }
        fetchDetailedAnalytics(detailedPagination.current_page);
      }
    } catch (error) {
      console.error('Error resending notification:', error);
      showErrorRU('Ошибка повторной отправки уведомления');
    } finally {
      setResendingId(null);
      setShowResendModal(null);
    }
  };

  const getReadPercentageColor = (percentage) => {
    if (percentage >= 80) return 'text-green-400';
    if (percentage >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getReadPercentageBgColor = (percentage) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Загрузка детальной аналитики при смене фильтров
  useEffect(() => {
    console.log('useEffect triggered:', { activeTab, filters });
    if (activeTab === 'detailed') {
      console.log('Fetching detailed analytics...');
      fetchDetailedAnalytics(1);
    }
  }, [activeTab, fetchDetailedAnalytics]);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="font-russo text-3xl text-white mb-2">Управление уведомлениями</h1>
        <p className="text-text-secondary">Отправка уведомлений игрокам и аналитика</p>
      </div>

      {/* Табы */}
      <div className="flex space-x-1 mb-6 bg-surface-sidebar rounded-lg p-1">
        <button
          onClick={() => setActiveTab('send')}
          className={`flex-1 py-3 px-4 font-rajdhani font-bold rounded-lg transition-all duration-200 ${
            activeTab === 'send'
              ? 'bg-accent-primary text-white shadow-lg'
              : 'text-text-secondary hover:text-white hover:bg-surface-card'
          }`}
        >
          📤 Отправить уведомление
        </button>
        <button
          onClick={() => setActiveTab('detailed')}
          className={`flex-1 py-3 px-4 font-rajdhani font-bold rounded-lg transition-all duration-200 ${
            activeTab === 'detailed'
              ? 'bg-accent-primary text-white shadow-lg'
              : 'text-text-secondary hover:text-white hover:bg-surface-card'
          }`}
        >
          📋 Аналитика отправок
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex-1 py-3 px-4 font-rajdhani font-bold rounded-lg transition-all duration-200 ${
            activeTab === 'analytics'
              ? 'bg-accent-primary text-white shadow-lg'
              : 'text-text-secondary hover:text-white hover:bg-surface-card'
          }`}
        >
          📊 Аналитика
        </button>
      </div>

      {/* Содержимое табов */}
      {activeTab === 'send' && (
        <div className="space-y-6">
          {/* Форма отправки уведомления */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h2 className="font-rajdhani text-xl font-bold text-white mb-4">Создать уведомление</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Левая колонка */}
              <div className="space-y-4">
                {/* Тип уведомления */}
                <div>
                  <label className="block text-text-secondary text-sm font-medium mb-2">
                    Тип уведомления
                  </label>
                  <select
                    value={notification.type}
                    onChange={(e) => setNotification({ ...notification, type: e.target.value })}
                    className="w-full bg-surface-sidebar border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                  >
                    {notificationTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.icon} {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Приоритет */}
                <div>
                  <label className="block text-text-secondary text-sm font-medium mb-2">
                    Приоритет
                  </label>
                  <div className="flex space-x-2">
                    {priorities.map(priority => (
                      <button
                        key={priority.value}
                        onClick={() => setNotification({ ...notification, priority: priority.value })}
                        className={`flex-1 py-2 px-3 rounded-lg font-rajdhani font-bold transition-all duration-200 ${
                          notification.priority === priority.value
                            ? `${priority.bgColor} text-white shadow-lg`
                            : `bg-surface-sidebar ${priority.color} hover:${priority.bgColor} hover:text-white`
                        }`}
                      >
                        {priority.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Заголовок */}
                <div>
                  <label className="block text-text-secondary text-sm font-medium mb-2">
                    Заголовок уведомления *
                  </label>
                  <input
                    type="text"
                    value={notification.title}
                    onChange={(e) => setNotification({ ...notification, title: e.target.value })}
                    placeholder="Введите заголовок уведомления"
                    className="w-full bg-surface-sidebar border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-accent-primary"
                    maxLength={100}
                  />
                  <div className="text-xs text-gray-400 mt-1">{notification.title.length}/100</div>
                </div>
              </div>

              {/* Правая колонка */}
              <div className="space-y-4">
                {/* Сообщение */}
                <div>
                  <label className="block text-text-secondary text-sm font-medium mb-2">
                    Текст сообщения *
                  </label>
                  <textarea
                    value={notification.message}
                    onChange={(e) => setNotification({ ...notification, message: e.target.value })}
                    placeholder="Введите текст уведомления"
                    rows={6}
                    className="w-full bg-surface-sidebar border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-accent-primary resize-none"
                    maxLength={500}
                  />
                  <div className="text-xs text-gray-400 mt-1">{notification.message.length}/500</div>
                </div>

                {/* Получатели */}
                <div>
                  <label className="block text-text-secondary text-sm font-medium mb-2">
                    Получатели
                  </label>
                  <div className="space-y-3">
                    <div className="flex space-x-4">
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="radio"
                          name="targetUsers"
                          value="all"
                          checked={targetUsers === 'all'}
                          onChange={(e) => setTargetUsers(e.target.value)}
                          className="text-accent-primary focus:ring-accent-primary"
                        />
                        <span className="text-white">Всем пользователям</span>
                      </label>
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="radio"
                          name="targetUsers"
                          value="specific"
                          checked={targetUsers === 'specific'}
                          onChange={(e) => setTargetUsers(e.target.value)}
                          className="text-accent-primary focus:ring-accent-primary"
                        />
                        <span className="text-white">Конкретным пользователям</span>
                      </label>
                    </div>

                    {/* Поиск пользователей */}
                    {targetUsers === 'specific' && (
                      <div className="space-y-2">
                        <div className="relative">
                          <input
                            type="text"
                            value={userSearch}
                            onChange={(e) => setUserSearch(e.target.value)}
                            placeholder="Поиск пользователей по имени или email"
                            className="w-full bg-surface-sidebar border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-accent-primary"
                          />
                          
                          {/* Результаты поиска */}
                          {foundUsers.length > 0 && (
                            <div className="absolute top-full left-0 right-0 bg-surface-sidebar border border-gray-600 rounded-lg mt-1 max-h-40 overflow-y-auto z-10">
                              {foundUsers.map(user => (
                                <button
                                  key={user.id}
                                  onClick={() => addUserToSelection(user)}
                                  className="w-full text-left px-3 py-2 hover:bg-surface-card text-white text-sm"
                                >
                                  {user.username} ({user.email})
                                </button>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Выбранные пользователи */}
                        {selectedUsers.length > 0 && (
                          <div className="space-y-1">
                            <div className="text-sm text-text-secondary">
                              Выбрано пользователей: {selectedUsers.length}
                            </div>
                            <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
                              {selectedUsers.map(user => (
                                <div
                                  key={user.id}
                                  className="flex items-center space-x-2 bg-accent-primary bg-opacity-20 border border-accent-primary border-opacity-30 rounded px-2 py-1"
                                >
                                  <span className="text-xs text-white">{user.username}</span>
                                  <button
                                    onClick={() => removeUserFromSelection(user.id)}
                                    className="text-red-400 hover:text-red-300 text-xs"
                                  >
                                    ×
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Кнопка отправки */}
            <div className="mt-6 pt-6 border-t border-gray-700">
              <button
                onClick={sendNotification}
                disabled={loading || !notification.title.trim() || !notification.message.trim()}
                className={`w-full py-3 px-6 font-rajdhani font-bold text-lg rounded-lg transition-all duration-200 ${
                  loading || !notification.title.trim() || !notification.message.trim()
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : 'bg-accent-primary hover:bg-accent-primary-dark text-white shadow-lg hover:shadow-xl'
                }`}
              >
                {loading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <span>Отправляется...</span>
                  </div>
                ) : (
                  `📤 Отправить уведомление${targetUsers === 'all' ? ' всем' : ` (${selectedUsers.length} получателей)`}`
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Таб детальной аналитики отправок */}
      {activeTab === 'detailed' && (
        <div className="space-y-6">
          {/* Фильтры */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h2 className="font-rajdhani text-xl font-bold text-white mb-4">Фильтры аналитики</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Тип уведомления */}
              <div>
                <label className="block text-text-secondary text-sm font-medium mb-2">
                  Тип уведомления
                </label>
                <select
                  value={filters.type_filter}
                  onChange={(e) => setFilters({ ...filters, type_filter: e.target.value })}
                  className="w-full bg-surface-sidebar border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                >
                  <option value="">Все типы</option>
                  <option value="admin_notification">Админские</option>
                  <option value="bet_accepted">Ставка принята</option>
                  <option value="match_result">Результат матча</option>
                  <option value="gem_gift">Подарок гемов</option>
                  <option value="system_message">Системные</option>
                </select>
              </div>

              {/* Дата от */}
              <div>
                <label className="block text-text-secondary text-sm font-medium mb-2">
                  Дата от
                </label>
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
                  className="w-full bg-surface-sidebar border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                />
              </div>

              {/* Дата до */}
              <div>
                <label className="block text-text-secondary text-sm font-medium mb-2">
                  Дата до
                </label>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
                  className="w-full bg-surface-sidebar border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-accent-primary"
                />
              </div>
            </div>

            <div className="mt-4">
              <button
                onClick={() => fetchDetailedAnalytics(1)}
                className="px-4 py-2 bg-accent-primary hover:bg-accent-primary-dark text-white font-rajdhani font-bold rounded-lg transition-all duration-200"
              >
                🔍 Применить фильтры
              </button>
            </div>
          </div>

          {/* Список уведомлений с аналитикой */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-rajdhani text-xl font-bold text-white">Детальная аналитика отправок</h2>
              <div className="text-text-secondary text-sm">
                Показано {detailedAnalytics.length} из {detailedPagination.total_items}
              </div>
            </div>

            {detailedLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {detailedAnalytics.map((item) => (
                  <div key={item.notification_id} className="bg-surface-sidebar rounded-lg p-4 border border-gray-700">
                    {/* Компактный вид уведомления */}
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-2xl">
                            {item.type === 'admin_notification' ? '🛡️' : 
                             item.type === 'bet_accepted' ? '🎯' :
                             item.type === 'match_result' ? '🏆' :
                             item.type === 'gem_gift' ? '💎' : '📬'}
                          </span>
                          <div>
                            <h3 className="text-white font-bold text-lg">{item.title}</h3>
                            <p className="text-text-secondary text-sm">
                              {new Date(item.created_at).toLocaleString('ru-RU')} • {item.type}
                            </p>
                          </div>
                        </div>
                        <p className="text-gray-300 text-sm mb-3 line-clamp-2">{item.message}</p>
                        
                        {/* Прогресс-бар */}
                        <div className="flex items-center space-x-4">
                          <div className="flex-1">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-gray-400">Прочитано</span>
                              <span className={`font-bold ${getReadPercentageColor(item.read_percentage)}`}>
                                {item.read_count}/{item.total_recipients} ({item.read_percentage}%)
                              </span>
                            </div>
                            <div className="w-full bg-gray-700 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full transition-all duration-300 ${getReadPercentageBgColor(item.read_percentage)}`}
                                style={{ width: `${item.read_percentage}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 ml-4">
                        {/* Кнопка повторной отправки */}
                        {item.unread_count > 0 && (
                          <button
                            onClick={() => handleResendToUnread(item.notification_id)}
                            disabled={resendingId === item.notification_id}
                            className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white text-xs font-bold rounded transition-all duration-200 disabled:opacity-50"
                          >
                            {resendingId === item.notification_id ? '⏳' : '🔄'} Повторить
                          </button>
                        )}
                        
                        {/* Кнопка показать детали */}
                        <button
                          onClick={() => setExpandedNotification(
                            expandedNotification === item.notification_id ? null : item.notification_id
                          )}
                          className="px-3 py-1 bg-accent-primary hover:bg-accent-primary-dark text-white text-xs font-bold rounded transition-all duration-200"
                        >
                          {expandedNotification === item.notification_id ? '▲ Скрыть' : '▼ Детали'}
                        </button>
                      </div>
                    </div>

                    {/* Развернутые детали */}
                    {expandedNotification === item.notification_id && (
                      <div className="mt-4 pt-4 border-t border-gray-600">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          {/* Прочитавшие пользователи - ЗЕЛЕНЫЙ ФОН И ТЕКСТ */}
                          <div>
                            <h4 className="text-green-400 font-bold mb-3">
                              ✅ Прочитали ({item.read_count})
                            </h4>
                            <div className="max-h-64 overflow-y-auto space-y-2">
                              {item.read_users.map((user) => (
                                <div key={user.user_id} className="bg-green-900 bg-opacity-20 rounded p-2">
                                  <div className="text-white text-sm font-medium">{user.username}</div>
                                  <div className="text-gray-400 text-xs">{user.email}</div>
                                  {user.read_at && (
                                    <div className="text-green-400 text-xs">
                                      Прочитано: {new Date(user.read_at).toLocaleString('ru-RU')}
                                    </div>
                                  )}
                                  {/* ЗЕЛЕНЫЙ СТАТУС "ПРОЧИТАНО" */}
                                  <div className="mt-1">
                                    <span className="inline-block px-2 py-1 text-xs font-bold bg-green-600 text-white rounded">
                                      Прочитано
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Не прочитавшие пользователи */}
                          <div>
                            <h4 className="text-red-400 font-bold mb-3">
                              ❌ Не прочитали ({item.unread_count})
                            </h4>
                            <div className="max-h-64 overflow-y-auto space-y-2">
                              {item.unread_users.map((user) => (
                                <div key={user.user_id} className="bg-red-900 bg-opacity-20 rounded p-2">
                                  <div className="text-white text-sm font-medium">{user.username}</div>
                                  <div className="text-gray-400 text-xs">{user.email}</div>
                                  <div className="text-red-400 text-xs">Не прочитано</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {detailedAnalytics.length === 0 && (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-3 opacity-50">📭</div>
                    <div className="text-gray-400">Нет данных для отображения</div>
                    <div className="text-gray-500 text-sm mt-1">Попробуйте изменить фильтры</div>
                  </div>
                )}
              </div>
            )}

            {/* Пагинация */}
            {detailedPagination.total_pages > 1 && (
              <div className="flex justify-center items-center space-x-4 mt-6 pt-6 border-t border-gray-700">
                <button
                  onClick={() => fetchDetailedAnalytics(detailedPagination.current_page - 1)}
                  disabled={!detailedPagination.has_prev}
                  className="px-4 py-2 bg-surface-sidebar border border-gray-600 rounded text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-card transition-colors"
                >
                  ← Предыдущая
                </button>
                
                <span className="text-text-secondary">
                  Страница {detailedPagination.current_page} из {detailedPagination.total_pages}
                </span>
                
                <button
                  onClick={() => fetchDetailedAnalytics(detailedPagination.current_page + 1)}
                  disabled={!detailedPagination.has_next}
                  className="px-4 py-2 bg-surface-sidebar border border-gray-600 rounded text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-card transition-colors"
                >
                  Следующая →
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Таб аналитики */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          {/* Общая статистика */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-blue-500 bg-opacity-20 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📨</span>
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">
                    {analytics.total_sent?.toLocaleString() || '0'}
                  </div>
                  <div className="text-text-secondary text-sm">Всего отправлено</div>
                </div>
              </div>
            </div>

            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-green-500 bg-opacity-20 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📖</span>
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">
                    {analytics.total_read?.toLocaleString() || '0'}
                  </div>
                  <div className="text-text-secondary text-sm">Прочитано</div>
                </div>
              </div>
            </div>

            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-yellow-500 bg-opacity-20 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📊</span>
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">
                    {analytics.read_rate ? `${analytics.read_rate.toFixed(1)}%` : '0%'}
                  </div>
                  <div className="text-text-secondary text-sm">Процент прочтения</div>
                </div>
              </div>
            </div>
          </div>

          {/* Статистика по типам */}
          {analytics.by_type && Object.keys(analytics.by_type).length > 0 && (
            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Статистика по типам уведомлений</h3>
              <div className="space-y-3">
                {Object.entries(analytics.by_type).map(([type, stats]) => {
                  const typeInfo = notificationTypes.find(t => t.value === type) || { label: type, icon: '📝' };
                  const readRate = stats.sent > 0 ? (stats.read / stats.sent * 100).toFixed(1) : '0';
                  
                  return (
                    <div key={type} className="flex items-center justify-between p-3 bg-surface-sidebar rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-xl">{typeInfo.icon}</span>
                        <div>
                          <div className="text-white font-medium">{typeInfo.label}</div>
                          <div className="text-text-secondary text-sm">
                            Отправлено: {stats.sent} • Прочитано: {stats.read}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-bold">{readRate}%</div>
                        <div className="text-text-secondary text-xs">прочтения</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Кнопка обновления */}
          <div className="flex justify-center">
            <button
              onClick={fetchAnalytics}
              className="px-6 py-2 bg-accent-primary hover:bg-accent-primary-dark text-white font-rajdhani font-bold rounded-lg transition-all duration-200"
            >
              🔄 Обновить аналитику
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationAdmin;