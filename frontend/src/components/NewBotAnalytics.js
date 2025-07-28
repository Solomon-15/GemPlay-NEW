import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationContext';
import { useApi } from '../hooks/useApi';
import ProfitChart from './ProfitChart';

const NewBotAnalytics = () => {
  const [activeTab, setActiveTab] = useState('human'); // 'human' or 'regular'
  const [timeRange, setTimeRange] = useState('24h'); // 24h, 7d, 30d
  const [loading, setLoading] = useState(true);
  const [humanBotsData, setHumanBotsData] = useState({});
  const [regularBotsData, setRegularBotsData] = useState({});
  const [humanBotsList, setHumanBotsList] = useState([]);
  const [regularBotsList, setRegularBotsList] = useState([]);
  const { showErrorRU, showSuccessRU } = useNotifications();
  const { get } = useApi();

  // Получение списка Human-ботов
  const fetchHumanBots = async () => {
    try {
      const response = await get('/admin/human-bots');
      setHumanBotsList(response.bots || []);
    } catch (error) {
      console.error('Error fetching human bots:', error);
    }
  };

  // Получение списка обычных ботов
  const fetchRegularBots = async () => {
    try {
      const response = await get('/admin/bots');
      setRegularBotsList(response.bots || []);
    } catch (error) {
      console.error('Error fetching regular bots:', error);
    }
  };

  // Получение данных аналитики для Human-ботов
  const fetchHumanBotsAnalytics = async () => {
    try {
      setLoading(true);
      
      // Получаем игры Human-ботов
      const gamesResponse = await get('/admin/games', {
        page: 1,
        limit: 1000,
        human_bot_only: true
      });
      
      const games = gamesResponse.games || [];
      
      // Вычисляем аналитику
      const analytics = calculateAnalytics(games, humanBotsList, 'human');
      setHumanBotsData(analytics);
      
    } catch (error) {
      console.error('Error fetching human bots analytics:', error);
      showErrorRU('Ошибка загрузки аналитики Human-ботов');
    } finally {
      setLoading(false);
    }
  };

  // Получение данных аналитики для обычных ботов
  const fetchRegularBotsAnalytics = async () => {
    try {
      setLoading(true);
      
      // Получаем игры обычных ботов
      const gamesResponse = await get('/admin/games', {
        page: 1,
        limit: 1000,
        regular_bot_only: true
      });
      
      const games = gamesResponse.games || [];
      
      // Вычисляем аналитику
      const analytics = calculateAnalytics(games, regularBotsList, 'regular');
      setRegularBotsData(analytics);
      
    } catch (error) {
      console.error('Error fetching regular bots analytics:', error);
      showErrorRU('Ошибка загрузки аналитики обычных ботов');
    } finally {
      setLoading(false);
    }
  };

  // Функция для вычисления аналитики
  const calculateAnalytics = (games, bots, botType) => {
    const now = new Date();
    let startTime;
    
    // Определяем временной диапазон
    switch (timeRange) {
      case '24h':
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    }

    // Фильтруем игры по времени
    const filteredGames = games.filter(game => {
      const gameDate = new Date(game.created_at);
      return gameDate >= startTime;
    });

    // Общая статистика
    const totalGames = filteredGames.length;
    const completedGames = filteredGames.filter(game => game.status === 'completed');
    const activeGames = filteredGames.filter(game => game.status === 'active');
    const activeBots = bots.filter(bot => bot.is_active || bot.active);
    const inactiveBots = bots.filter(bot => !bot.is_active && !bot.active);

    // Статистика по каждому боту
    const botStats = bots.map(bot => {
      const botGames = filteredGames.filter(game => game.creator_id === bot.id);
      const botCompletedGames = botGames.filter(game => game.status === 'completed');
      const botWins = botCompletedGames.filter(game => game.winner_id === bot.id);
      
      const totalBetAmount = botGames.reduce((sum, game) => sum + (game.bet_amount || 0), 0);
      const avgBetSize = botGames.length > 0 ? totalBetAmount / botGames.length : 0;
      const winRate = botCompletedGames.length > 0 ? (botWins.length / botCompletedGames.length) * 100 : 0;
      
      // Вычисляем чистую прибыль/убыток
      let netProfit = 0;
      botCompletedGames.forEach(game => {
        if (game.winner_id === bot.id) {
          netProfit += game.bet_amount || 0; // Выигрыш
        } else {
          netProfit -= game.bet_amount || 0; // Проигрыш
        }
      });

      return {
        id: bot.id,
        name: bot.name,
        character: bot.character,
        totalGames: botGames.length,
        wins: botWins.length,
        losses: botCompletedGames.length - botWins.length,
        winRate: winRate.toFixed(1),
        avgBetSize: avgBetSize.toFixed(0),
        netProfit: netProfit.toFixed(0),
        isActive: bot.is_active || bot.active
      };
    });

    // Топ-5 самых успешных ботов
    const topBots = botStats
      .sort((a, b) => parseFloat(b.winRate) - parseFloat(a.winRate))
      .slice(0, 5);

    // Генерация данных для графиков
    const chartData = generateChartData(filteredGames, startTime, timeRange);

    return {
      overview: {
        totalBots: bots.length,
        activeBots: activeBots.length,
        inactiveBots: inactiveBots.length,
        totalGames,
        completedGames: completedGames.length,
        activeGames: activeGames.length,
        avgBetSize: completedGames.length > 0 ? 
          (completedGames.reduce((sum, game) => sum + (game.bet_amount || 0), 0) / completedGames.length).toFixed(0) : 0,
        totalVolume: completedGames.reduce((sum, game) => sum + (game.bet_amount || 0), 0).toFixed(0)
      },
      botStats,
      topBots,
      chartData
    };
  };

  // Генерация данных для графиков
  const generateChartData = (games, startTime, timeRange) => {
    const now = new Date();
    const intervals = timeRange === '24h' ? 24 : timeRange === '7d' ? 7 : 30;
    const intervalDuration = timeRange === '24h' ? 60 * 60 * 1000 : 24 * 60 * 60 * 1000;
    
    const labels = [];
    const gameVolume = [];
    const winRate = [];
    const avgBetSize = [];

    for (let i = 0; i < intervals; i++) {
      const intervalStart = new Date(startTime.getTime() + i * intervalDuration);
      const intervalEnd = new Date(startTime.getTime() + (i + 1) * intervalDuration);
      
      // Генерация лейблов
      if (timeRange === '24h') {
        labels.push(intervalStart.getHours().toString().padStart(2, '0') + ':00');
      } else if (timeRange === '7d') {
        labels.push(intervalStart.toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric' }));
      } else {
        labels.push(intervalStart.getDate().toString());
      }

      // Фильтрация игр для данного интервала
      const intervalGames = games.filter(game => {
        const gameDate = new Date(game.created_at);
        return gameDate >= intervalStart && gameDate < intervalEnd;
      });

      const completedIntervalGames = intervalGames.filter(game => game.status === 'completed');
      
      gameVolume.push(intervalGames.length);
      
      if (completedIntervalGames.length > 0) {
        const wins = completedIntervalGames.filter(game => game.winner_id).length;
        winRate.push(((wins / completedIntervalGames.length) * 100).toFixed(1));
        
        const totalBetAmount = completedIntervalGames.reduce((sum, game) => sum + (game.bet_amount || 0), 0);
        avgBetSize.push((totalBetAmount / completedIntervalGames.length).toFixed(0));
      } else {
        winRate.push(0);
        avgBetSize.push(0);
      }
    }

    return {
      labels,
      gameVolume,
      winRate,
      avgBetSize
    };
  };

  // Получение данных для графиков
  const getGameVolumeChartData = () => {
    const data = activeTab === 'human' ? humanBotsData : regularBotsData;
    if (!data.chartData) return { labels: [], datasets: [] };

    return {
      labels: data.chartData.labels,
      datasets: [{
        label: 'Количество игр',
        data: data.chartData.gameVolume,
        borderColor: 'rgba(64, 224, 208, 1)',
        backgroundColor: 'rgba(64, 224, 208, 0.2)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    };
  };

  const getWinRateChartData = () => {
    const data = activeTab === 'human' ? humanBotsData : regularBotsData;
    if (!data.chartData) return { labels: [], datasets: [] };

    return {
      labels: data.chartData.labels,
      datasets: [{
        label: 'Win Rate (%)',
        data: data.chartData.winRate,
        borderColor: 'rgba(34, 197, 94, 1)',
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    };
  };

  const getAvgBetSizeChartData = () => {
    const data = activeTab === 'human' ? humanBotsData : regularBotsData;
    if (!data.chartData) return { labels: [], datasets: [] };

    return {
      labels: data.chartData.labels,
      datasets: [{
        label: 'Средний размер ставки (гемы)',
        data: data.chartData.avgBetSize,
        borderColor: 'rgba(251, 191, 36, 1)',
        backgroundColor: 'rgba(251, 191, 36, 0.2)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    };
  };

  // Эффекты для загрузки данных
  useEffect(() => {
    fetchHumanBots();
    fetchRegularBots();
  }, []);

  useEffect(() => {
    if (activeTab === 'human' && humanBotsList.length > 0) {
      fetchHumanBotsAnalytics();
    } else if (activeTab === 'regular' && regularBotsList.length > 0) {
      fetchRegularBotsAnalytics();
    }
  }, [activeTab, timeRange, humanBotsList, regularBotsList]);

  const handleRefresh = () => {
    if (activeTab === 'human') {
      fetchHumanBotsAnalytics();
    } else {
      fetchRegularBotsAnalytics();
    }
  };

  const currentData = activeTab === 'human' ? humanBotsData : regularBotsData;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto mb-4"></div>
          <p className="font-rajdhani text-text-secondary">Загрузка аналитики...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="font-russo text-2xl text-white mb-6">📊 Аналитика ботов</h2>
        
        {/* Переключатель табов */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setActiveTab('human')}
                className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-all duration-200 ${
                  activeTab === 'human' 
                    ? 'bg-accent-primary text-white shadow-lg' 
                    : 'bg-surface-sidebar text-text-secondary hover:text-white hover:bg-surface-card'
                }`}
              >
                👤 Human-боты
              </button>
              <button
                onClick={() => setActiveTab('regular')}
                className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-all duration-200 ${
                  activeTab === 'regular' 
                    ? 'bg-accent-primary text-white shadow-lg' 
                    : 'bg-surface-sidebar text-text-secondary hover:text-white hover:bg-surface-card'
                }`}
              >
                🤖 Обычные боты
              </button>
            </div>
            
            <div className="flex items-center space-x-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                  Временной период
                </label>
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                >
                  <option value="24h">Последние 24 часа</option>
                  <option value="7d">Последние 7 дней</option>
                  <option value="30d">Последние 30 дней</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleRefresh}
                  className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-blue-600 transition-colors font-rajdhani font-bold"
                >
                  🔄 Обновить
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Общая статистика */}
        {currentData.overview && (
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">
              📈 Общая статистика {activeTab === 'human' ? 'Human-ботов' : 'обычных ботов'}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-sm">Всего ботов</div>
                <div className="text-2xl font-bold text-white">{currentData.overview.totalBots}</div>
                <div className="text-xs text-green-400 mt-1">
                  Активных: {currentData.overview.activeBots} | Неактивных: {currentData.overview.inactiveBots}
                </div>
              </div>
              
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-sm">Всего игр</div>
                <div className="text-2xl font-bold text-blue-400">{currentData.overview.totalGames}</div>
                <div className="text-xs text-blue-300 mt-1">
                  Завершено: {currentData.overview.completedGames} | Активных: {currentData.overview.activeGames}
                </div>
              </div>
              
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-sm">Средний размер ставки</div>
                <div className="text-2xl font-bold text-yellow-400">{currentData.overview.avgBetSize}</div>
                <div className="text-xs text-yellow-300 mt-1">гемов</div>
              </div>
              
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-text-secondary text-sm">Общий объем</div>
                <div className="text-2xl font-bold text-purple-400">{currentData.overview.totalVolume}</div>
                <div className="text-xs text-purple-300 mt-1">гемов</div>
              </div>
            </div>
          </div>
        )}

        {/* Графики */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">🎮 Объем игр</h3>
            <ProfitChart
              type="line"
              data={getGameVolumeChartData()}
              title="Количество игр по времени"
            />
          </div>

          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">🏆 Win Rate</h3>
            <ProfitChart
              type="line"
              data={getWinRateChartData()}
              title="Процент побед по времени"
            />
          </div>

          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">💰 Средний размер ставки</h3>
            <ProfitChart
              type="line"
              data={getAvgBetSizeChartData()}
              title="Средний размер ставки по времени"
            />
          </div>
        </div>

        {/* Топ-5 самых успешных ботов */}
        {currentData.topBots && currentData.topBots.length > 0 && (
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 mb-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">🏅 Топ-5 самых успешных ботов</h3>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {currentData.topBots.map((bot, index) => (
                <div key={bot.id} className="bg-surface-sidebar rounded-lg p-4">
                  <div className="text-center">
                    <div className="text-2xl mb-2">
                      {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏆'}
                    </div>
                    <div className="font-bold text-white text-sm truncate">{bot.name}</div>
                    <div className="text-green-400 font-bold text-lg">{bot.winRate}%</div>
                    <div className="text-text-secondary text-xs">{bot.totalGames} игр</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Детальная статистика по ботам */}
        {currentData.botStats && (
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
            <h3 className="font-rajdhani text-xl font-bold text-white mb-4">📋 Детальная статистика по ботам</h3>
            
            <div className="hidden lg:block overflow-x-auto">
              <table className="w-full text-sm text-left text-text-secondary">
                <thead className="text-xs text-text-secondary uppercase bg-surface-sidebar">
                  <tr>
                    <th scope="col" className="px-4 py-3">№</th>
                    <th scope="col" className="px-4 py-3">Имя бота</th>
                    <th scope="col" className="px-4 py-3">Статус</th>
                    <th scope="col" className="px-4 py-3">Игр</th>
                    <th scope="col" className="px-4 py-3">Побед</th>
                    <th scope="col" className="px-4 py-3">Поражений</th>
                    <th scope="col" className="px-4 py-3">Win Rate</th>
                    <th scope="col" className="px-4 py-3">Ср. ставка</th>
                    <th scope="col" className="px-4 py-3">Чистая прибыль</th>
                    {activeTab === 'human' && <th scope="col" className="px-4 py-3">Характер</th>}
                  </tr>
                </thead>
                <tbody>
                  {currentData.botStats.map((bot, index) => (
                    <tr key={bot.id} className="bg-surface-card border-b border-border-primary hover:bg-surface-sidebar">
                      <td className="px-4 py-4 font-medium text-text-secondary">{index + 1}</td>
                      <td className="px-4 py-4 font-medium text-white whitespace-nowrap">{bot.name}</td>
                      <td className="px-4 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                          bot.isActive ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
                        }`}>
                          {bot.isActive ? 'Активен' : 'Неактивен'}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-blue-400">{bot.totalGames}</td>
                      <td className="px-4 py-4 text-green-400">{bot.wins}</td>
                      <td className="px-4 py-4 text-red-400">{bot.losses}</td>
                      <td className="px-4 py-4 text-yellow-400 font-bold">{bot.winRate}%</td>
                      <td className="px-4 py-4 text-purple-400">{bot.avgBetSize}</td>
                      <td className="px-4 py-4">
                        <span className={`font-bold ${
                          parseFloat(bot.netProfit) >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {parseFloat(bot.netProfit) >= 0 ? '+' : ''}{bot.netProfit}
                        </span>
                      </td>
                      {activeTab === 'human' && (
                        <td className="px-4 py-4 text-text-secondary">{bot.character || 'Не указан'}</td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Мобильные карточки */}
            <div className="lg:hidden space-y-4">
              {currentData.botStats.map((bot, index) => (
                <div key={bot.id} className="bg-surface-sidebar rounded-lg p-4 border border-border-primary">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-text-secondary text-sm">#{index + 1}</span>
                      <h4 className="font-rajdhani font-bold text-white text-sm">{bot.name}</h4>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                      bot.isActive ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
                    }`}>
                      {bot.isActive ? 'Активен' : 'Неактивен'}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-text-secondary text-xs mb-1">Игр</div>
                      <div className="text-blue-400 font-bold">{bot.totalGames}</div>
                    </div>
                    <div>
                      <div className="text-text-secondary text-xs mb-1">Win Rate</div>
                      <div className="text-yellow-400 font-bold">{bot.winRate}%</div>
                    </div>
                    <div>
                      <div className="text-text-secondary text-xs mb-1">Ср. ставка</div>
                      <div className="text-purple-400 font-bold">{bot.avgBetSize}</div>
                    </div>
                    <div>
                      <div className="text-text-secondary text-xs mb-1">Чистая прибыль</div>
                      <div className={`font-bold ${
                        parseFloat(bot.netProfit) >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {parseFloat(bot.netProfit) >= 0 ? '+' : ''}{bot.netProfit}
                      </div>
                    </div>
                  </div>
                  
                  {activeTab === 'human' && bot.character && (
                    <div className="mt-3 pt-3 border-t border-border-primary">
                      <div className="text-text-secondary text-xs mb-1">Характер</div>
                      <div className="text-text-secondary text-sm">{bot.character}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NewBotAnalytics;