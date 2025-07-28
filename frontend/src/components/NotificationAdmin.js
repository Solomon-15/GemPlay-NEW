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
      setDetailedLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '50'
      });
      
      if (filters.type_filter) params.append('type_filter', filters.type_filter);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      
      const response = await axios.get(`${API}/admin/notifications/detailed-analytics?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.data.success) {
        setDetailedAnalytics(response.data.data);
        setDetailedPagination(response.data.pagination);
      }
    } catch (error) {
      console.error('Error fetching detailed analytics:', error);
      showErrorRU('Ошибка загрузки детальной аналитики');
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
    if (activeTab === 'detailed') {
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