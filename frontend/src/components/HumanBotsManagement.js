import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import { useBotOperations } from '../hooks/useBotOperations';

const HumanBotsManagement = () => {
  const { botsApi } = useApi();
  const { bulkOperations } = useBotOperations();
  const [stats, setStats] = useState({
    active_bots: 0,
    bets_24h: 0,
    wins_24h: 0,
    win_percentage: 0,
    total_bet_value: 0,
    errors: 0,
    most_active: []
  });
  const [allBotsEnabled, setAllBotsEnabled] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await botsApi.getStats();
      setStats(response || {});
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки статистики Human ботов:', error);
      setLoading(false);
    }
  };

  const toggleAllBots = async () => {
    try {
      const newState = !allBotsEnabled;
      
      await bulkOperations.toggleAllBots(newState);
      
      setAllBotsEnabled(newState);
      await fetchStats(); // Refresh stats
    } catch (error) {
      console.error('Ошибка переключения ботов:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Кнопка управления всеми ботами */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-rajdhani font-bold text-white">Human Боты</h2>
        <button
          onClick={toggleAllBots}
          className={`px-6 py-3 rounded-lg font-rajdhani font-bold text-white transition-colors ${
            allBotsEnabled 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-green-600 hover:bg-green-700'
          }`}
        >
          {allBotsEnabled ? 'Отключить всех ботов' : 'Включить всех ботов'}
        </button>
      </div>

      {/* Информационные блоки */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7 gap-4">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Активных ботов</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.active_bots}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Ставок за 24ч</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.bets_24h}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Побед за 24ч</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.wins_24h}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-purple-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">% побед</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.win_percentage}%</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-orange-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Сумма ставок</p>
              <p className="text-white text-lg font-rajdhani font-bold">${stats.total_bet_value.toFixed(2)}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${stats.errors > 0 ? 'bg-red-600' : 'bg-gray-600'}`}>
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Ошибки/Сбои</p>
              <p className={`text-lg font-rajdhani font-bold ${stats.errors > 0 ? 'text-red-400' : 'text-white'}`}>
                {stats.errors}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-indigo-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Топ активных</p>
              <div className="text-white text-sm">
                {stats.most_active.length > 0 ? (
                  stats.most_active.slice(0, 3).map((bot, index) => (
                    <div key={bot.id} className="text-xs">
                      {bot.name || `Bot-${bot.id.substring(0, 6)}`}: {bot.games}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-text-secondary">Нет данных</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Таблица ботов */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border-primary">
          <h3 className="text-lg font-rajdhani font-bold text-white">Список Human ботов</h3>
          <p className="text-text-secondary text-sm">Пока оставлено пустым, добавлю позже</p>
        </div>
        <div className="p-8 text-center">
          <div className="text-text-secondary">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="font-rajdhani">Таблица будет добавлена позже</p>
            <p className="text-sm">Раздел находится в разработке</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HumanBotsManagement;