import React, { memo } from 'react';

/**
 * Мемоизированный компонент отображения статистических карточек ботов
 * Отображает общую статистику активных ботов, ставок и доходов
 * Оптимизирован для предотвращения лишних ререндеров при неизменных данных
 */
const BotStatsCards = memo(({ activeBetsStats, stats }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      {/* Активные ставки */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-rajdhani text-lg font-bold text-white">Активные ставки</h3>
          <div className="w-10 h-10 bg-accent-primary bg-opacity-20 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-accent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>
        <div className="text-2xl font-rajdhani font-bold text-white mb-2">
          {activeBetsStats?.active_bets || 0}
        </div>
        <div className="text-sm text-text-secondary">
          Лимит: {activeBetsStats?.limit || 0}
        </div>
      </div>

      {/* Активные боты */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-rajdhani text-lg font-bold text-white">Активные боты</h3>
          <div className="w-10 h-10 bg-green-600 bg-opacity-20 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
        </div>
        <div className="text-2xl font-rajdhani font-bold text-white mb-2">
          {stats?.active_bots || 0}
        </div>
        <div className="text-sm text-text-secondary">
          Всего: {stats?.total_bots || 0}
        </div>
      </div>

      {/* Доходы */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-rajdhani text-lg font-bold text-white">Доходы</h3>
          <div className="w-10 h-10 bg-yellow-600 bg-opacity-20 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          </div>
        </div>
        <div className="text-2xl font-rajdhani font-bold text-white mb-2">
          {stats?.total_profit || 0}₽
        </div>
        <div className="text-sm text-text-secondary">
          За период
        </div>
      </div>
    </div>
  );
};

export default BotStatsCards;