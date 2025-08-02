import { formatAsGems } from '../utils/economy';
import { formatTimeWithOffset } from '../utils/timeUtils';

const HumanBotCommissionModal = ({
  isOpen,
  onClose,
  bot,
  user: currentUser,
  data,
  loading,
  onPageChange
}) => {
  if (!isOpen) return null;

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU');
  };

  const getResultBadge = (result) => {
    switch (result) {
      case 'win':
        return <span className="px-2 py-1 bg-green-600 text-white text-xs rounded-full">Победа</span>;
      case 'loss':
        return <span className="px-2 py-1 bg-red-600 text-white text-xs rounded-full">Поражение</span>;
      case 'draw':
        return <span className="px-2 py-1 bg-gray-600 text-white text-xs rounded-full">Ничья</span>;
      default:
        return <span className="px-2 py-1 bg-gray-600 text-white text-xs rounded-full">—</span>;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-surface-primary border border-border-primary rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-primary">
          <div>
            <h3 className="text-xl font-rajdhani font-bold text-white">
              💰 Детализация комиссий
            </h3>
            <p className="text-text-secondary font-roboto text-sm mt-1">
              {bot?.name} • Общая комиссия: ${(bot?.total_commission_paid || 0).toFixed(2)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex justify-center items-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary"></div>
              <span className="ml-2 text-text-secondary">Загружаем данные о комиссиях...</span>
            </div>
          ) : data && data.commission_entries ? (
            <>
              {/* Summary */}
              <div className="bg-surface-sidebar bg-opacity-50 rounded-lg p-4 mb-6">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-accent-primary">
                      ${(data.total_commission_paid || 0).toFixed(2)}
                    </div>
                    <div className="text-sm text-text-secondary">Общая комиссия</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-white">
                      {data.pagination?.total_items || 0}
                    </div>
                    <div className="text-sm text-text-secondary">Всего транзакций</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-orange-400">
                      {data.commission_entries.length}
                    </div>
                    <div className="text-sm text-text-secondary">На этой странице</div>
                  </div>
                </div>
              </div>

              {/* Commission Entries Table */}
              {data.commission_entries.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-border-primary">
                    <thead className="bg-surface-sidebar bg-opacity-20">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">№</th>
                        <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Дата</th>
                        <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Сумма комиссии</th>
                        <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Ставка</th>
                        <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Результат</th>
                        <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">Соперник</th>
                        <th className="px-4 py-3 text-left text-xs font-roboto font-bold text-text-secondary uppercase">ID Игры</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-primary">
                      {data.commission_entries.map((entry, index) => {
                        const gameDetails = entry.game_details;
                        const pageStart = (data.pagination?.current_page - 1) * (data.pagination?.per_page || 50);
                        
                        return (
                          <tr 
                            key={entry.id || index} 
                            className="hover:bg-gray-900 hover:bg-opacity-20 transition-colors"
                          >
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-white font-bold">
                                {pageStart + index + 1}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-white">
                                {formatDate(entry.created_at)}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto font-bold text-red-400">
                                ${(entry.amount || 0).toFixed(2)}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-accent-primary">
                                {gameDetails ? formatAsGems(gameDetails.bet_amount || 0) : '—'}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              {gameDetails ? getResultBadge(gameDetails.result) : '—'}
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-sm font-roboto text-white">
                                {gameDetails?.opponent?.username || '—'}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="text-xs font-roboto font-mono text-text-secondary">
                                {gameDetails?.game_id ? gameDetails.game_id.substring(0, 8) : '—'}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-text-secondary">
                  <div className="text-4xl mb-4">💰</div>
                  <div className="text-lg font-rajdhani">Комиссии не найдены</div>
                  <div className="text-sm">У этого Human-бота пока нет оплаченных комиссий</div>
                </div>
              )}

              {/* Pagination */}
              {data.pagination && data.pagination.total_pages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-border-primary">
                  <div className="text-sm text-text-secondary">
                    Страница {data.pagination.current_page} из {data.pagination.total_pages}
                    • Всего: {data.pagination.total_items} записей
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onPageChange(data.pagination.current_page - 1)}
                      disabled={!data.pagination.has_prev}
                      className="px-3 py-1 bg-surface-sidebar text-white text-sm rounded hover:bg-opacity-70 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      ← Назад
                    </button>
                    <button
                      onClick={() => onPageChange(data.pagination.current_page + 1)}
                      disabled={!data.pagination.has_next}
                      className="px-3 py-1 bg-surface-sidebar text-white text-sm rounded hover:bg-opacity-70 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Вперед →
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8 text-text-secondary">
              <div className="text-4xl mb-4">⚠️</div>
              <div className="text-lg font-rajdhani">Ошибка загрузки данных</div>
              <div className="text-sm">Не удалось получить информацию о комиссиях</div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-border-primary">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors font-roboto"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
};

export default HumanBotCommissionModal;