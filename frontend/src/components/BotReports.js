import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationContext';
import { useApi } from '../hooks/useApi';

const BotReports = () => {
  const [reports, setReports] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const { showSuccessRU, showErrorRU } = useNotifications();

  const reportTypes = [
    {
      id: 'queue_performance',
      name: 'Производительность очереди',
      description: 'Анализ времени ожидания и эффективности очереди',
      icon: '⏱️'
    },
    {
      id: 'priority_effectiveness',
      name: 'Эффективность приоритетов',
      description: 'Сравнение результативности разных приоритетов',
      icon: '🏆'
    },
    {
      id: 'bot_utilization',
      name: 'Использование ботов',
      description: 'Статистика загрузки и активности ботов',
      icon: '🤖'
    },
    {
      id: 'system_health',
      name: 'Здоровье системы',
      description: 'Общие показатели стабильности системы',
      icon: '💚'
    }
  ];

  const generateReport = async (reportType) => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/admin/bots/reports/generate`, {
        type: reportType,
        timeRange: '7d'
      }, getApiConfig());
      
      if (response.data.success) {
        showSuccessRU('Отчет успешно сгенерирован');
        setSelectedReport(response.data.report);
      }
    } catch (error) {
      console.error('Error generating report:', error);
      showErrorRU('Ошибка при генерации отчета');
    } finally {
      setGenerating(false);
    }
  };

  const exportReport = async (format) => {
    if (!selectedReport) return;
    
    try {
      const response = await axios.post(`${API}/admin/bots/reports/export`, {
        reportId: selectedReport.id,
        format: format
      }, getApiConfig());
      
      if (response.data.success) {
        showSuccessRU(`Отчет экспортирован в ${format.toUpperCase()}`);
      }
    } catch (error) {
      console.error('Error exporting report:', error);
      showErrorRU('Ошибка при экспорте отчета');
    }
  };

  return (
    <div className="space-y-6">
      {/* Типы отчетов */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 sm:p-6">
        <h3 className="font-rajdhani text-lg sm:text-xl font-bold text-white mb-4">📊 Генерация отчетов</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reportTypes.map(report => (
            <div key={report.id} className="bg-surface-sidebar rounded-lg p-4 border border-border-primary">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start space-x-3">
                  <span className="text-2xl flex-shrink-0">{report.icon}</span>
                  <div className="min-w-0 flex-1">
                    <h4 className="font-rajdhani font-bold text-white text-sm sm:text-base">{report.name}</h4>
                    <p className="text-xs sm:text-sm text-text-secondary break-words">{report.description}</p>
                  </div>
                </div>
              </div>
              
              <button
                onClick={() => generateReport(report.id)}
                disabled={generating}
                className={`w-full px-3 py-2 rounded-lg font-rajdhani font-bold text-sm transition-colors ${
                  generating 
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                    : 'bg-accent-primary text-white hover:bg-blue-600'
                }`}
              >
                {generating ? 'Генерация...' : 'Сгенерировать отчет'}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Просмотр отчета */}
      {selectedReport && (
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 space-y-3 sm:space-y-0">
            <h3 className="font-rajdhani text-lg sm:text-xl font-bold text-white">
              📋 {selectedReport.name}
            </h3>
            
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => exportReport('pdf')}
                className="px-3 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-rajdhani font-bold text-sm"
              >
                PDF
              </button>
              <button
                onClick={() => exportReport('csv')}
                className="px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-rajdhani font-bold text-sm"
              >
                CSV
              </button>
              <button
                onClick={() => exportReport('xlsx')}
                className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-rajdhani font-bold text-sm"
              >
                Excel
              </button>
            </div>
          </div>
          
          <div className="bg-surface-sidebar rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-sm text-text-secondary">Период анализа</div>
                <div className="text-lg font-rajdhani font-bold text-white">
                  {selectedReport.timeRange === '7d' ? 'Последние 7 дней' : 
                   selectedReport.timeRange === '24h' ? 'Последние 24 часа' : 
                   selectedReport.timeRange === '30d' ? 'Последние 30 дней' : 'Неизвестно'}
                </div>
              </div>
              <div>
                <div className="text-sm text-text-secondary">Дата генерации</div>
                <div className="text-lg font-rajdhani font-bold text-white">
                  {new Date().toLocaleDateString('ru-RU')}
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <h4 className="font-rajdhani font-bold text-accent-primary mb-2">📊 Ключевые показатели</h4>
                
                {/* Отображение метрик в зависимости от типа отчета */}
                {selectedReport.metrics && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {selectedReport.metrics.avg_wait_time && (
                      <div className="bg-surface-card rounded-lg p-3">
                        <div className="text-sm text-text-secondary">Среднее время ожидания</div>
                        <div className="text-xl font-bold text-yellow-400">{selectedReport.metrics.avg_wait_time} мин</div>
                      </div>
                    )}
                    {selectedReport.metrics.queue_efficiency && (
                      <div className="bg-surface-card rounded-lg p-3">
                        <div className="text-sm text-text-secondary">Эффективность очереди</div>
                        <div className="text-xl font-bold text-green-400">{selectedReport.metrics.queue_efficiency}%</div>
                      </div>
                    )}
                    {selectedReport.metrics.total_games && (
                      <div className="bg-surface-card rounded-lg p-3">
                        <div className="text-sm text-text-secondary">Всего игр</div>
                        <div className="text-xl font-bold text-blue-400">{selectedReport.metrics.total_games}</div>
                      </div>
                    )}
                  </div>
                )}

                {/* Отображение утилизации ботов */}
                {selectedReport.utilization && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    <div className="bg-surface-card rounded-lg p-3">
                      <div className="text-sm text-text-secondary">Активных ботов</div>
                      <div className="text-xl font-bold text-green-400">{selectedReport.utilization.active_bots}</div>
                    </div>
                    <div className="bg-surface-card rounded-lg p-3">
                      <div className="text-sm text-text-secondary">Загрузка системы</div>
                      <div className="text-xl font-bold text-blue-400">{selectedReport.utilization.utilization_rate}%</div>
                    </div>
                    <div className="bg-surface-card rounded-lg p-3">
                      <div className="text-sm text-text-secondary">Текущее использование</div>
                      <div className="text-xl font-bold text-purple-400">{selectedReport.utilization.current_usage}/{selectedReport.utilization.total_capacity}</div>
                    </div>
                  </div>
                )}

                {/* Отображение здоровья системы */}
                {selectedReport.health_metrics && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    <div className="bg-surface-card rounded-lg p-3">
                      <div className="text-sm text-text-secondary">Успешность операций</div>
                      <div className="text-xl font-bold text-green-400">{selectedReport.health_metrics.success_rate}%</div>
                    </div>
                    <div className="bg-surface-card rounded-lg p-3">
                      <div className="text-sm text-text-secondary">Время безотказной работы</div>
                      <div className="text-xl font-bold text-blue-400">{selectedReport.health_metrics.system_uptime}%</div>
                    </div>
                    <div className="bg-surface-card rounded-lg p-3">
                      <div className="text-sm text-text-secondary">Время отклика</div>
                      <div className="text-xl font-bold text-purple-400">{selectedReport.health_metrics.avg_response_time}с</div>
                    </div>
                  </div>
                )}

                {/* Отображение статистики приоритетов */}
                {selectedReport.priority_stats && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left text-text-secondary">
                      <thead className="text-xs text-text-secondary uppercase bg-surface-card">
                        <tr>
                          <th className="px-3 py-2">Приоритет</th>
                          <th className="px-3 py-2">Ботов</th>
                          <th className="px-3 py-2">Всего игр</th>
                          <th className="px-3 py-2">Успешность</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedReport.priority_stats.map((stat, index) => (
                          <tr key={index} className="border-b border-border-primary">
                            <td className="px-3 py-2 font-bold text-white">{stat.priority}</td>
                            <td className="px-3 py-2 text-blue-400">{stat.bots_count}</td>
                            <td className="px-3 py-2 text-yellow-400">{stat.total_games}</td>
                            <td className="px-3 py-2 text-green-400">{stat.success_rate}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
              
              <div>
                <h4 className="font-rajdhani font-bold text-accent-primary mb-2">🏆 Ключевые рекомендации</h4>
                <ul className="space-y-2">
                  {selectedReport.insights?.map((insight, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="text-blue-400 mt-1 flex-shrink-0">ℹ</span>
                      <span className="text-text-secondary text-sm">{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BotReports;