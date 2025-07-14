import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/bots/reports/generate`, {
        type: reportType,
        timeRange: '7d'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
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
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/admin/bots/reports/export`, {
        reportId: selectedReport.id,
        format: format
      }, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      // Создаем ссылку для скачивания
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `bot_report_${selectedReport.id}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      showSuccessRU(`Отчет экспортирован в ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Error exporting report:', error);
      showErrorRU('Ошибка при экспорте отчета');
    }
  };

  return (
    <div className="space-y-6">
      {/* Типы отчетов */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <h3 className="font-rajdhani text-xl font-bold text-white mb-4">📊 Генерация отчетов</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reportTypes.map(report => (
            <div key={report.id} className="bg-surface-sidebar rounded-lg p-4 border border-border-primary">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{report.icon}</span>
                  <div>
                    <h4 className="font-rajdhani font-bold text-white">{report.name}</h4>
                    <p className="text-sm text-text-secondary">{report.description}</p>
                  </div>
                </div>
              </div>
              
              <button
                onClick={() => generateReport(report.id)}
                disabled={generating}
                className={`w-full px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
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
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-rajdhani text-xl font-bold text-white">
              📋 {selectedReport.name}
            </h3>
            
            <div className="flex space-x-2">
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
                  {selectedReport.timeRange || 'Последние 7 дней'}
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
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="bg-surface-card rounded-lg p-3">
                    <div className="text-sm text-text-secondary">Среднее время ожидания</div>
                    <div className="text-xl font-bold text-yellow-400">2.3 мин</div>
                  </div>
                  <div className="bg-surface-card rounded-lg p-3">
                    <div className="text-sm text-text-secondary">Успешность активации</div>
                    <div className="text-xl font-bold text-green-400">94.2%</div>
                  </div>
                  <div className="bg-surface-card rounded-lg p-3">
                    <div className="text-sm text-text-secondary">Загрузка системы</div>
                    <div className="text-xl font-bold text-blue-400">78.5%</div>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-rajdhani font-bold text-accent-primary mb-2">🏆 Топ рекомендации</h4>
                <ul className="space-y-2">
                  <li className="flex items-start space-x-2">
                    <span className="text-green-400 mt-1">✓</span>
                    <span className="text-text-secondary">Система работает стабильно, приоритеты распределены эффективно</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-yellow-400 mt-1">⚠</span>
                    <span className="text-text-secondary">Рекомендуется увеличить лимит Bot #3 для оптимизации загрузки</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-blue-400 mt-1">ℹ</span>
                    <span className="text-text-secondary">Время ожидания в очереди в пределах нормы (< 5 минут)</span>
                  </li>
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