import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SecurityMonitoring = ({ user }) => {
  const [dashboard, setDashboard] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [resolvingAlert, setResolvingAlert] = useState(null);
  const [actionText, setActionText] = useState('');

  useEffect(() => {
    fetchSecurityData();
    const interval = setInterval(fetchSecurityData, 30000); // Обновление каждые 30 секунд
    return () => clearInterval(interval);
  }, []);

  const fetchSecurityData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [dashboardRes, alertsRes, statsRes] = await Promise.all([
        axios.get(`${API}/admin/security/dashboard`, { headers }),
        axios.get(`${API}/admin/security/alerts?limit=20`, { headers }),
        axios.get(`${API}/admin/security/monitoring-stats`, { headers })
      ]);

      setDashboard(dashboardRes.data);
      setAlerts(alertsRes.data);
      setStats(statsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки данных безопасности:', error);
      setLoading(false);
    }
  };

  const handleResolveAlert = async (alertId) => {
    if (!actionText.trim()) {
      alert('Пожалуйста, введите предпринятые действия');
      return;
    }

    setResolvingAlert(alertId);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/security/alerts/${alertId}/resolve`, {
        action_taken: actionText
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setActionText('');
      setResolvingAlert(null);
      fetchSecurityData(); // Обновляем данные
      alert('Предупреждение успешно разрешено');
    } catch (error) {
      console.error('Ошибка разрешения предупреждения:', error);
      alert('Ошибка разрешения предупреждения');
      setResolvingAlert(null);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'LOW': 'text-green-400',
      'MEDIUM': 'text-yellow-400',
      'HIGH': 'text-orange-400',
      'CRITICAL': 'text-red-400'
    };
    return colors[severity] || 'text-gray-400';
  };

  const getSeverityBg = (severity) => {
    const backgrounds = {
      'LOW': 'bg-green-900 bg-opacity-20 border-green-500',
      'MEDIUM': 'bg-yellow-900 bg-opacity-20 border-yellow-500',
      'HIGH': 'bg-orange-900 bg-opacity-20 border-orange-500',
      'CRITICAL': 'bg-red-900 bg-opacity-20 border-red-500'
    };
    return backgrounds[severity] || 'bg-gray-900 bg-opacity-20 border-gray-500';
  };

  const getSeverityName = (severity) => {
    const names = {
      'LOW': 'Низкий',
      'MEDIUM': 'Средний',
      'HIGH': 'Высокий',
      'CRITICAL': 'Критический'
    };
    return names[severity] || severity;
  };

  const getAlertTypeName = (type) => {
    const types = {
      'SUSPICIOUS_LOGIN': 'Подозрительный вход',
      'MULTIPLE_FAILED_LOGINS': 'Множественные неудачные входы',
      'UNUSUAL_BETTING_PATTERN': 'Необычная схема ставок',
      'HIGH_VALUE_TRANSACTION': 'Транзакция высокой стоимости',
      'ACCOUNT_MANIPULATION': 'Манипуляции с аккаунтом',
      'POTENTIAL_BOT_ACTIVITY': 'Возможная активность бота',
      'SYSTEM_ANOMALY': 'Системная аномалия'
    };
    return types[type] || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-white text-xl font-roboto">Загружается мониторинг безопасности...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="font-russo text-2xl text-white">Мониторинг безопасности</h2>
        <div className="flex items-center space-x-2 text-sm text-text-secondary">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Обновляется каждые 30 секунд</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 border-b border-border-primary">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2 font-rajdhani font-medium transition-colors ${
            activeTab === 'dashboard'
              ? 'text-accent-primary border-b-2 border-accent-primary'
              : 'text-text-secondary hover:text-white'
          }`}
        >
          Панель управления
        </button>
        <button
          onClick={() => setActiveTab('alerts')}
          className={`px-4 py-2 font-rajdhani font-medium transition-colors ${
            activeTab === 'alerts'
              ? 'text-accent-primary border-b-2 border-accent-primary'
              : 'text-text-secondary hover:text-white'
          }`}
        >
          Предупреждения безопасности
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          className={`px-4 py-2 font-rajdhani font-medium transition-colors ${
            activeTab === 'stats'
              ? 'text-accent-primary border-b-2 border-accent-primary'
              : 'text-text-secondary hover:text-white'
          }`}
        >
          Статистика
        </button>
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && dashboard && (
        <div className="space-y-6">
          {/* Security Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-roboto text-text-secondary text-sm">Активные предупреждения</p>
                  <p className="font-rajdhani text-3xl font-bold text-red-400">{dashboard.active_alerts || 0}</p>
                </div>
                <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>

            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-roboto text-text-secondary text-sm">Заблокированные IP</p>
                  <p className="font-rajdhani text-3xl font-bold text-orange-400">{dashboard.blocked_ips || 0}</p>
                </div>
                <svg className="w-8 h-8 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364L18.364 5.636" />
                </svg>
              </div>
            </div>

            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-roboto text-text-secondary text-sm">Подозрительные аккаунты</p>
                  <p className="font-rajdhani text-3xl font-bold text-yellow-400">{dashboard.suspicious_accounts || 0}</p>
                </div>
                <svg className="w-8 h-8 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>

            <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-roboto text-text-secondary text-sm">Системное здоровье</p>
                  <p className="font-rajdhani text-3xl font-bold text-green-400">{dashboard.system_health || 'OK'}</p>
                </div>
                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Последняя активность</h3>
            <div className="space-y-3">
              {dashboard.recent_activity && dashboard.recent_activity.length > 0 ? (
                dashboard.recent_activity.map((activity, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-border-primary last:border-b-0">
                    <div className="flex items-center space-x-3">
                      <div className={`w-2 h-2 rounded-full ${getSeverityColor(activity.severity)}`}></div>
                      <div>
                        <p className="text-white text-sm">{activity.description}</p>
                        <p className="text-text-secondary text-xs">{new Date(activity.timestamp).toLocaleString('ru-RU')}</p>
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${getSeverityBg(activity.severity)}`}>
                      {getSeverityName(activity.severity)}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-text-secondary">Недавней активности нет</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-4">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Предупреждения безопасности</h3>
            
            {alerts.length > 0 ? (
              <div className="space-y-4">
                {alerts.map((alert) => (
                  <div key={alert.id} className={`p-4 rounded-lg border ${getSeverityBg(alert.severity)}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className={`font-medium ${getSeverityColor(alert.severity)}`}>
                            {getSeverityName(alert.severity)}
                          </span>
                          <span className="text-text-secondary">•</span>
                          <span className="text-text-secondary text-sm">
                            {getAlertTypeName(alert.alert_type)}
                          </span>
                        </div>
                        <h4 className="font-rajdhani font-bold text-white mb-2">{alert.title}</h4>
                        <p className="text-text-secondary text-sm mb-2">{alert.description}</p>
                        <div className="text-xs text-text-secondary">
                          <span>Пользователь: {alert.user_info?.username || 'Неизвестен'}</span>
                          <span className="mx-2">•</span>
                          <span>IP: {alert.user_info?.ip_address || 'Неизвестен'}</span>
                          <span className="mx-2">•</span>
                          <span>{new Date(alert.created_at).toLocaleString('ru-RU')}</span>
                        </div>
                      </div>
                      
                      {alert.status === 'OPEN' && (
                        <div className="ml-4 space-y-2">
                          <div>
                            <input
                              type="text"
                              placeholder="Предпринятые действия..."
                              value={resolvingAlert === alert.id ? actionText : ''}
                              onChange={(e) => {
                                if (resolvingAlert === alert.id) {
                                  setActionText(e.target.value);
                                }
                              }}
                              onFocus={() => setResolvingAlert(alert.id)}
                              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded text-white text-sm"
                            />
                          </div>
                          <button
                            onClick={() => handleResolveAlert(alert.id)}
                            disabled={resolvingAlert !== alert.id || !actionText.trim()}
                            className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:opacity-50 text-white text-sm rounded font-medium transition-colors"
                          >
                            Разрешить
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-text-secondary">Активных предупреждений нет</p>
            )}
          </div>
        </div>
      )}

      {/* Stats Tab */}
      {activeTab === 'stats' && stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Статистика предупреждений</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-text-secondary">Всего предупреждений:</span>
                <span className="text-white font-bold">{stats.total_alerts || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Разрешённых:</span>
                <span className="text-green-400 font-bold">{stats.resolved_alerts || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Открытых:</span>
                <span className="text-red-400 font-bold">{stats.open_alerts || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Критических:</span>
                <span className="text-red-400 font-bold">{stats.critical_alerts || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Системная статистика</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-text-secondary">Активные сессии:</span>
                <span className="text-white font-bold">{stats.active_sessions || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Неудачные входы (24ч):</span>
                <span className="text-orange-400 font-bold">{stats.failed_logins_24h || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Заблокированные IP:</span>
                <span className="text-red-400 font-bold">{stats.blocked_ips || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Подозрительные аккаунты:</span>
                <span className="text-yellow-400 font-bold">{stats.suspicious_accounts || 0}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SecurityMonitoring;