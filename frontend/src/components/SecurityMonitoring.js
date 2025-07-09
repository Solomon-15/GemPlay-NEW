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
    const interval = setInterval(fetchSecurityData, 30000); // Refresh every 30 seconds
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
      console.error('Error fetching security data:', error);
      setLoading(false);
    }
  };

  const handleResolveAlert = async (alertId) => {
    if (!actionText.trim()) {
      alert('Please enter action taken');
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

      alert('Alert resolved successfully');
      setActionText('');
      fetchSecurityData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error resolving alert');
    } finally {
      setResolvingAlert(null);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL': return 'text-red-500 bg-red-100';
      case 'HIGH': return 'text-red-400 bg-red-50';
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-100';
      case 'LOW': return 'text-blue-500 bg-blue-100';
      default: return 'text-gray-500 bg-gray-100';
    }
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Loading Security Monitoring...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-primary p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-4xl md:text-6xl text-accent-primary mb-4">
          🛡️ Мониторинг Безопасности
        </h1>
        <p className="font-roboto text-xl text-text-secondary">
          Система защиты виртуального баланса
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex space-x-4 bg-surface-card rounded-lg p-2">
          {[
            { id: 'dashboard', name: 'Дашборд', icon: '📊' },
            { id: 'alerts', name: 'Алерты', icon: '🚨' },
            { id: 'stats', name: 'Статистика', icon: '📈' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 px-6 rounded-lg font-rajdhani font-bold transition-colors ${
                activeTab === tab.id
                  ? 'bg-accent-primary text-white'
                  : 'text-text-secondary hover:text-white'
              }`}
            >
              {tab.icon} {tab.name}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && dashboard && (
          <div className="space-y-6">
            {/* Alert Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-surface-card border border-red-500 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-russo text-red-500 mb-2">Критические</h3>
                    <p className="font-rajdhani text-3xl font-bold text-white">
                      {dashboard.alert_counts.critical}
                    </p>
                  </div>
                  <div className="text-4xl">🔴</div>
                </div>
              </div>

              <div className="bg-surface-card border border-orange-500 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-russo text-orange-500 mb-2">Высокие</h3>
                    <p className="font-rajdhani text-3xl font-bold text-white">
                      {dashboard.alert_counts.high}
                    </p>
                  </div>
                  <div className="text-4xl">🟠</div>
                </div>
              </div>

              <div className="bg-surface-card border border-yellow-500 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-russo text-yellow-500 mb-2">Средние</h3>
                    <p className="font-rajdhani text-3xl font-bold text-white">
                      {dashboard.alert_counts.medium}
                    </p>
                  </div>
                  <div className="text-4xl">🟡</div>
                </div>
              </div>

              <div className="bg-surface-card border border-blue-500 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-russo text-blue-500 mb-2">Низкие</h3>
                    <p className="font-rajdhani text-3xl font-bold text-white">
                      {dashboard.alert_counts.low}
                    </p>
                  </div>
                  <div className="text-4xl">🔵</div>
                </div>
              </div>
            </div>

            {/* Recent Activities */}
            <div className="bg-surface-card border border-border-primary rounded-lg p-6">
              <h2 className="font-russo text-2xl text-accent-secondary mb-4">
                🔥 Последние инциденты (1 час)
              </h2>
              <div className="space-y-3">
                {dashboard.recent_activities.length === 0 ? (
                  <p className="text-text-secondary">Нет активности за последний час</p>
                ) : (
                  dashboard.recent_activities.map((activity, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-surface-sidebar rounded-lg">
                      <div>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${getSeverityColor(activity.severity)}`}>
                          {activity.severity}
                        </span>
                        <span className="ml-3 text-white font-roboto">{activity.description}</span>
                      </div>
                      <span className="text-text-secondary text-sm">{formatTime(activity.created_at)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Top Alert Types */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-surface-card border border-border-primary rounded-lg p-6">
                <h2 className="font-russo text-2xl text-accent-secondary mb-4">
                  📊 Топ типов алертов (7 дней)
                </h2>
                <div className="space-y-2">
                  {dashboard.top_alert_types.map((type, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-surface-sidebar rounded">
                      <span className="text-white font-roboto">{type._id}</span>
                      <span className="text-accent-primary font-rajdhani font-bold">{type.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-surface-card border border-border-primary rounded-lg p-6">
                <h2 className="font-russo text-2xl text-accent-secondary mb-4">
                  👥 Проблемные пользователи
                </h2>
                <div className="space-y-2">
                  {dashboard.users_with_most_alerts.map((user, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-surface-sidebar rounded">
                      <div>
                        <span className="text-white font-roboto">{user.username}</span>
                        <span className="text-text-secondary text-sm ml-2">({user.email})</span>
                      </div>
                      <span className="text-red-400 font-rajdhani font-bold">{user.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <div className="bg-surface-card border border-border-primary rounded-lg p-6">
            <h2 className="font-russo text-2xl text-accent-secondary mb-6">
              🚨 Алерты безопасности
            </h2>
            <div className="space-y-4">
              {alerts.map((alert) => (
                <div key={alert.id} className={`p-4 rounded-lg border-l-4 ${
                  alert.resolved ? 'bg-green-50 border-green-500' : 'bg-surface-sidebar border-red-500'
                }`}>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className={`px-2 py-1 rounded text-xs font-bold mr-3 ${getSeverityColor(alert.severity)}`}>
                          {alert.severity}
                        </span>
                        <span className="text-white font-roboto font-bold">{alert.alert_type}</span>
                        {alert.resolved && (
                          <span className="ml-3 px-2 py-1 bg-green-500 text-white text-xs rounded">
                            РЕШЕНО
                          </span>
                        )}
                      </div>
                      <p className="text-text-secondary mb-2">{alert.description}</p>
                      <div className="text-sm text-text-muted">
                        <span>Время: {formatTime(alert.created_at)}</span>
                        {alert.ip_address && <span className="ml-4">IP: {alert.ip_address}</span>}
                      </div>
                      {alert.action_taken && (
                        <div className="mt-2 p-2 bg-green-100 rounded text-sm">
                          <strong>Действие:</strong> {alert.action_taken}
                        </div>
                      )}
                    </div>
                    {!alert.resolved && (
                      <div className="ml-4">
                        <input
                          type="text"
                          placeholder="Действие для решения..."
                          value={resolvingAlert === alert.id ? actionText : ''}
                          onChange={(e) => setActionText(e.target.value)}
                          className="mb-2 px-3 py-1 bg-surface-sidebar border border-border-primary rounded text-white text-sm w-48"
                        />
                        <button
                          onClick={() => handleResolveAlert(alert.id)}
                          disabled={resolvingAlert === alert.id}
                          className="block w-full px-3 py-1 bg-accent-primary text-white rounded text-sm font-rajdhani font-bold hover:bg-accent-secondary transition-colors disabled:opacity-50"
                        >
                          {resolvingAlert === alert.id ? 'РЕШЕНИЕ...' : 'РЕШИТЬ'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stats Tab */}
        {activeTab === 'stats' && stats && (
          <div className="space-y-6">
            {/* Transaction Stats */}
            <div className="bg-surface-card border border-border-primary rounded-lg p-6">
              <h2 className="font-russo text-2xl text-accent-secondary mb-4">
                💰 Статистика транзакций (24 часа)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-text-secondary">Общий объем</p>
                  <p className="font-rajdhani text-2xl font-bold text-accent-primary">
                    ${stats.transaction_stats.total_volume_24h.toFixed(2)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-text-secondary">Покупки</p>
                  <p className="font-rajdhani text-2xl font-bold text-green-400">
                    ${stats.transaction_stats.purchase_volume_24h.toFixed(2)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-text-secondary">Подарки</p>
                  <p className="font-rajdhani text-2xl font-bold text-blue-400">
                    ${stats.transaction_stats.gift_volume_24h.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            {/* User Activity */}
            <div className="bg-surface-card border border-border-primary rounded-lg p-6">
              <h2 className="font-russo text-2xl text-accent-secondary mb-4">
                👥 Активность пользователей
              </h2>
              <div className="text-center">
                <p className="text-text-secondary">Активные пользователи за 24 часа</p>
                <p className="font-rajdhani text-4xl font-bold text-white">
                  {stats.user_activity.active_users_24h}
                </p>
              </div>
            </div>

            {/* Security Stats */}
            <div className="bg-surface-card border border-border-primary rounded-lg p-6">
              <h2 className="font-russo text-2xl text-accent-secondary mb-4">
                🛡️ Статистика безопасности
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="text-center">
                  <p className="text-text-secondary">Заблокированные запросы</p>
                  <p className="font-rajdhani text-3xl font-bold text-red-400">
                    {stats.security_stats.requests_blocked_24h}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-text-secondary">Лимит запросов/мин</p>
                  <p className="font-rajdhani text-3xl font-bold text-yellow-400">
                    {stats.security_stats.rate_limit_threshold}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SecurityMonitoring;