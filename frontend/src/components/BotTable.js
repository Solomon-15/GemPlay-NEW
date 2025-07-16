import React from 'react';

/**
 * Компонент таблицы ботов
 * Отображает список ботов с их статистикой и действиями
 */
const BotTable = ({ 
  bots, 
  loadingStates, 
  editingBotLimits, 
  botLimitsValidation,
  onToggleBot,
  onEditBot,
  onDeleteBot,
  onViewActiveBets,
  onViewCycle,
  onEditBotLimit,
  onSaveBotLimit,
  onCancelBotLimit,
  onBotLimitChange
}) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ru-RU').format(amount);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border-primary">
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">ID</th>
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">Имя</th>
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">Статус</th>
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">Тип</th>
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">Активные ставки</th>
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">Лимит ставок</th>
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">Win Rate</th>
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">Прибыль</th>
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">Создан</th>
            <th className="text-left py-4 px-4 font-rajdhani font-bold text-white">Действия</th>
          </tr>
        </thead>
        <tbody>
          {bots.map((bot) => (
            <tr key={bot.id} className="border-b border-border-primary hover:bg-surface-sidebar hover:bg-opacity-30">
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="text-text-secondary font-roboto text-sm">{bot.id}</div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="text-white font-roboto font-medium">{bot.name}</div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <span className={`inline-flex px-2 py-1 text-xs font-roboto font-medium rounded-full ${
                  bot.is_active 
                    ? 'bg-green-600 text-white' 
                    : 'bg-red-600 text-white'
                }`}>
                  {bot.is_active ? 'Активен' : 'Неактивен'}
                </span>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="text-accent-primary font-roboto text-sm">{bot.type_name}</div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-center">
                <button
                  onClick={() => onViewActiveBets(bot)}
                  className="text-accent-primary font-roboto text-sm hover:text-accent-secondary transition-colors underline cursor-pointer"
                >
                  {bot.active_bets || 0}
                </button>
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-center">
                {editingBotLimits[bot.id] ? (
                  <div className="flex items-center space-x-2">
                    <input
                      type="number"
                      value={editingBotLimits[bot.id].limit}
                      onChange={(e) => onBotLimitChange(bot.id, e.target.value)}
                      className="w-16 px-2 py-1 bg-surface-sidebar border border-border-primary rounded text-white text-sm"
                      min="1"
                      max="100"
                    />
                    <button
                      onClick={() => onSaveBotLimit(bot.id)}
                      disabled={editingBotLimits[bot.id].saving}
                      className="p-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                    >
                      {editingBotLimits[bot.id].saving ? (
                        <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </button>
                    <button
                      onClick={() => onCancelBotLimit(bot.id)}
                      className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => onEditBotLimit(bot.id, bot.current_limit)}
                    className="text-accent-primary font-roboto text-sm hover:text-accent-secondary transition-colors underline cursor-pointer"
                  >
                    {bot.current_limit || 10}
                  </button>
                )}
                {botLimitsValidation[bot.id] && (
                  <div className="text-red-400 text-xs mt-1">{botLimitsValidation[bot.id]}</div>
                )}
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-center">
                <div className="text-accent-primary font-roboto text-sm">
                  {bot.win_percentage || 60}% win rate
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-center">
                <div className="text-orange-400 font-roboto text-sm">
                  {formatCurrency(bot.profit || 0)}₽
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="text-text-secondary font-roboto text-sm">
                  {formatDate(bot.created_at)}
                </div>
              </td>
              <td className="px-4 py-4 whitespace-nowrap">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onToggleBot(bot.id)}
                    className={`p-1 rounded ${
                      bot.is_active 
                        ? 'bg-red-600 hover:bg-red-700' 
                        : 'bg-green-600 hover:bg-green-700'
                    } text-white`}
                    title={bot.is_active ? 'Деактивировать' : 'Активировать'}
                  >
                    {bot.is_active ? (
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6" />
                      </svg>
                    ) : (
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.586a1 1 0 00.707-.293l2.414-2.414a1 1 0 01.707-.293H15a2 2 0 012 2v.586a1 1 0 00.293.707l2.414 2.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293H9a2 2 0 01-2-2v-.586a1 1 0 00-.293-.707l-2.414-2.414A1 1 0 014 13.586V9a2 2 0 012-2h4.586a1 1 0 00.707-.293l2.414-2.414A1 1 0 0114.586 4H15a2 2 0 012 2v.586a1 1 0 00.293.707l2.414 2.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293H9a2 2 0 01-2-2v-2z" />
                      </svg>
                    )}
                  </button>
                  <button
                    onClick={() => onEditBot(bot)}
                    className="p-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                    title="Редактировать"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onViewCycle(bot)}
                    className="p-1 bg-purple-600 text-white rounded hover:bg-purple-700"
                    title="История цикла"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onDeleteBot(bot)}
                    className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                    title="Удалить"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default BotTable;