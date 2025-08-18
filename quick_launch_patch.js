// Патч для добавления быстрого запуска ботов в RegularBotsManagement.js

// 1. Добавить состояния после строки 121 (после currentPreset):

  // Состояния для быстрого запуска ботов
  const [isQuickLaunchModalOpen, setIsQuickLaunchModalOpen] = useState(false);
  const [quickLaunchPresets, setQuickLaunchPresets] = useState([]);
  const [isCreatingPreset, setIsCreatingPreset] = useState(false);
  const [currentPreset, setCurrentPreset] = useState({
    name: '',
    buttonName: '',
    buttonColor: 'blue',
    min_bet_amount: 1.0,
    max_bet_amount: 50.0,
    wins_percentage: 44.0,
    losses_percentage: 36.0,
    draws_percentage: 20.0,
    cycle_games: 16,
    pause_between_cycles: 5,
    pause_on_draw: 5
  });

// 2. Добавить useEffect для загрузки пресетов:

  useEffect(() => {
    try {
      const saved = localStorage.getItem('quickLaunchPresets');
      if (saved) {
        const presets = JSON.parse(saved);
        setQuickLaunchPresets(presets);
      }
    } catch (error) {
      console.error('Ошибка загрузки пресетов:', error);
    }
  }, []);

// 3. Заменить заголовок таблицы (строка 2017):
// С:
<h3 className="text-lg font-rajdhani font-bold text-white">Список обычных ботов</h3>

// На:
<div className="flex justify-between items-center">
  <h3 className="text-lg font-rajdhani font-bold text-white">Список обычных ботов</h3>
  <button
    onClick={() => setIsQuickLaunchModalOpen(true)}
    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors flex items-center space-x-2"
    title="Быстрый запуск ботов по пресетам"
  >
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
    <span>⚡ Быстрый запуск</span>
  </button>
</div>

// 4. Добавить модальное окно перед последней закрывающей скобкой компонента (перед {inputModal}):

{/* Модальное окно быстрого запуска ботов */}
{isQuickLaunchModalOpen && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-surface-card border border-accent-primary border-opacity-50 rounded-lg w-full max-w-5xl mx-4 max-h-[85vh] overflow-hidden">
      {/* Заголовок */}
      <div className="flex justify-between items-center p-4 border-b border-border-primary bg-surface-sidebar">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-600 rounded-lg">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h3 className="font-rajdhani text-xl font-bold text-white">⚡ Быстрый запуск ботов</h3>
            <p className="text-text-secondary text-sm">Запуск ботов по готовым пресетам</p>
          </div>
        </div>
        <button
          onClick={() => setIsQuickLaunchModalOpen(false)}
          className="text-text-secondary hover:text-white transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="p-6 overflow-y-auto max-h-[calc(85vh-120px)]">
        {/* Быстрые кнопки пресетов */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-rajdhani text-lg font-bold text-white">Готовые пресеты</h4>
            <button
              onClick={() => setIsCreatingPreset(!isCreatingPreset)}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span>Создать пресет</span>
            </button>
          </div>

          {/* Сетка кнопок пресетов */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {quickLaunchPresets.map((preset) => (
              <div key={preset.id} className="relative group">
                <button
                  onClick={async () => {
                    try {
                      const token = localStorage.getItem('token');
                      
                      const botData = {
                        name: `${preset.name}-${Date.now()}`,
                        min_bet_amount: preset.min_bet_amount,
                        max_bet_amount: preset.max_bet_amount,
                        wins_percentage: preset.wins_percentage,
                        losses_percentage: preset.losses_percentage,
                        draws_percentage: preset.draws_percentage,
                        cycle_games: preset.cycle_games,
                        pause_between_cycles: preset.pause_between_cycles,
                        pause_on_draw: preset.pause_on_draw,
                        wins_count: Math.round(preset.cycle_games * preset.wins_percentage / 100),
                        losses_count: Math.round(preset.cycle_games * preset.losses_percentage / 100),
                        draws_count: Math.round(preset.cycle_games * preset.draws_percentage / 100)
                      };
                      
                      const response = await axios.post(`${API}/admin/bots/create-regular`, botData, {
                        headers: { Authorization: `Bearer ${token}` }
                      });
                      
                      showSuccessRU(`Бот "${botData.name}" создан из пресета "${preset.name}"`);
                      await fetchBotsList();
                      
                    } catch (error) {
                      console.error('Ошибка создания бота из пресета:', error);
                      showErrorRU(error.response?.data?.detail || 'Ошибка при создании бота из пресета');
                    }
                  }}
                  className={`w-full px-3 py-2 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors border ${
                    preset.buttonColor === 'green' ? 'bg-green-600 hover:bg-green-700 border-green-500' :
                    preset.buttonColor === 'red' ? 'bg-red-600 hover:bg-red-700 border-red-500' :
                    preset.buttonColor === 'yellow' ? 'bg-yellow-600 hover:bg-yellow-700 border-yellow-500' :
                    preset.buttonColor === 'purple' ? 'bg-purple-600 hover:bg-purple-700 border-purple-500' :
                    preset.buttonColor === 'orange' ? 'bg-orange-600 hover:bg-orange-700 border-orange-500' :
                    'bg-blue-600 hover:bg-blue-700 border-blue-500'
                  }`}
                  title={`Запустить бота: ${preset.name}`}
                >
                  {preset.buttonName}
                </button>
                <button
                  onClick={() => {
                    const updatedPresets = quickLaunchPresets.filter(p => p.id !== preset.id);
                    localStorage.setItem('quickLaunchPresets', JSON.stringify(updatedPresets));
                    setQuickLaunchPresets(updatedPresets);
                    showSuccessRU('Пресет удален');
                  }}
                  className="absolute -top-1 -right-1 w-5 h-5 bg-red-600 hover:bg-red-700 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Удалить пресет"
                >
                  ×
                </button>
              </div>
            ))}
            
            {quickLaunchPresets.length === 0 && (
              <div className="col-span-full text-center text-text-secondary py-8">
                <div className="text-4xl mb-2">🎯</div>
                <p>Нет сохраненных пресетов</p>
                <p className="text-sm">Создайте первый пресет для быстрого запуска ботов</p>
              </div>
            )}
          </div>
        </div>

        {/* Конструктор пресетов */}
        {isCreatingPreset && (
          <div className="bg-surface-sidebar rounded-lg p-6">
            <h4 className="font-rajdhani text-lg font-bold text-white mb-4">🛠️ Конструктор пресетов</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Основная информация */}
              <div>
                <label className="block text-text-secondary text-sm mb-2">Название пресета</label>
                <input
                  type="text"
                  value={currentPreset.name}
                  onChange={(e) => setCurrentPreset(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                  placeholder="Например: Агрессивный"
                />
              </div>

              <div>
                <label className="block text-text-secondary text-sm mb-2">Название кнопки</label>
                <input
                  type="text"
                  value={currentPreset.buttonName}
                  onChange={(e) => setCurrentPreset(prev => ({ ...prev, buttonName: e.target.value }))}
                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                  placeholder="Например: 🔥 Агрессивный"
                />
              </div>

              <div>
                <label className="block text-text-secondary text-sm mb-2">Цвет кнопки</label>
                <select
                  value={currentPreset.buttonColor}
                  onChange={(e) => setCurrentPreset(prev => ({ ...prev, buttonColor: e.target.value }))}
                  className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white font-roboto text-sm focus:outline-none focus:border-accent-primary"
                >
                  <option value="blue">🔵 Синий</option>
                  <option value="green">🟢 Зеленый</option>
                  <option value="red">🔴 Красный</option>
                  <option value="yellow">🟡 Желтый</option>
                  <option value="purple">🟣 Фиолетовый</option>
                  <option value="orange">🟠 Оранжевый</option>
                </select>
              </div>

              {/* Остальные поля... */}
            </div>

            {/* Кнопки управления */}
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setIsCreatingPreset(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors"
              >
                Отмена
              </button>
              <button
                onClick={() => {
                  // Логика сохранения пресета
                }}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-rajdhani font-bold text-sm transition-colors"
              >
                Сохранить пресет
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Подвал */}
      <div className="flex justify-between items-center p-4 border-t border-border-primary bg-surface-sidebar">
        <div className="text-text-secondary text-sm">
          💡 <strong>Совет:</strong> Можно создавать несколько ботов с одинаковыми параметрами, кликая по кнопке пресета многократно
        </div>
        <button
          onClick={() => setIsQuickLaunchModalOpen(false)}
          className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-rajdhani font-bold transition-colors"
        >
          Закрыть
        </button>
      </div>
    </div>
  </div>
)}