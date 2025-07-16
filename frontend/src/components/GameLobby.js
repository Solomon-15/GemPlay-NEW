import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { GAME_MOVES, formatGemsBet, getTimeAgo, canJoinGame } from '../utils/gameUtils';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GameLobby = ({ user, onUpdateUser }) => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [joiningGame, setJoiningGame] = useState(null);
  const [selectedMove, setSelectedMove] = useState({});
  const [showJoinModal, setShowJoinModal] = useState(null);

  // Use shared moves constant
  const moves = GAME_MOVES;

  useEffect(() => {
    fetchGames();
    // Обновляем список игр каждые 5 секунд
    const interval = setInterval(fetchGames, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchGames = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/games/available`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGames(response.data);
      setLoading(false);
    } catch (error) {
      // Если endpoint не существует, создадим заглушку
      console.error('Error fetching games:', error);
      setGames([]);
      setLoading(false);
    }
  };

  const canJoinGameLocal = (game) => {
    return canJoinGame(game, user.id);
  };

  const handleJoinGame = async (gameId) => {
    const move = selectedMove[gameId];
    if (!move) {
      alert('Выберите ваш ход!');
      return;
    }

    setJoiningGame(gameId);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/games/${gameId}/join`, {
        move: move
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert(`Игра завершена!\nРезультат: ${response.data.result}\nВаш ход: ${response.data.opponent_move}\nОппонент: ${response.data.creator_move}\nПобедитель: ${response.data.winner_id ? (response.data.winner_id === user.id ? 'Вы!' : response.data.creator.username) : 'Ничья'}`);
      
      // Обновляем данные
      await fetchGames();
      if (onUpdateUser) {
        onUpdateUser();
      }
      
      setShowJoinModal(null);
      setSelectedMove(prev => ({ ...prev, [gameId]: '' }));
    } catch (error) {
      alert(error.response?.data?.detail || 'Ошибка присоединения к игре');
    } finally {
      setJoiningGame(null);
    }
  };

  const formatGemsBet = (betGems) => {
    return formatGemsBet(betGems);
  };

  const getTimeAgo = (dateString) => {
    return getTimeAgo(dateString);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Загрузка лобби...</div>
      </div>
    );
  }

  const availableGames = games.filter(game => canJoinGameLocal(game));

  return (
    <div className="min-h-screen bg-gradient-primary p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-4xl md:text-6xl text-accent-primary mb-4">
          Лобби игр
        </h1>
        <p className="font-roboto text-xl text-text-secondary">
          Присоединяйтесь к существующим играм
        </p>
      </div>

      {/* Games List */}
      <div className="max-w-6xl mx-auto">
        {availableGames.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🎮</div>
            <h2 className="font-russo text-2xl text-accent-secondary mb-2">
              Нет доступных игр
            </h2>
            <p className="font-roboto text-text-secondary">
              Создайте новую игру или подождите, пока другие игроки создадут игры
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {availableGames.map((game) => (
              <div
                key={game.game_id || game.id}
                className="bg-surface-card border border-border-primary rounded-lg p-6 hover:border-accent-primary transition-all duration-300"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-russo text-xl text-accent-secondary">
                    Игра #{(game.game_id || game.id).substring(0, 8)}
                  </h3>
                  <span className="px-3 py-1 bg-green-600 text-white rounded-full text-sm font-rajdhani">
                    ОЖИДАЕТ
                  </span>
                </div>
                
                <div className="space-y-3 mb-6">
                  <div className="flex justify-between">
                    <span className="font-roboto text-text-secondary">Создатель:</span>
                    <span className="font-rajdhani text-white">{game.creator_username || 'Игрок'}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="font-roboto text-text-secondary">Ставка:</span>
                    <span className="font-rajdhani text-green-400 font-bold">${game.bet_amount}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="font-roboto text-text-secondary">Время:</span>
                    <span className="font-rajdhani text-white">{getTimeAgo(game.created_at)}</span>
                  </div>
                  
                  <div className="pt-2">
                    <span className="font-roboto text-text-secondary text-sm">Гемы:</span>
                    <p className="font-rajdhani text-white text-sm mt-1">
                      {formatGemsBet(game.bet_gems)}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => setShowJoinModal(game.game_id || game.id)}
                  className="w-full py-3 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300"
                >
                  ПРИСОЕДИНИТЬСЯ
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Join Game Modal */}
      {showJoinModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-border-primary rounded-lg p-8 max-w-md w-full mx-4">
            <h2 className="font-russo text-2xl text-accent-secondary mb-6 text-center">
              Выберите ваш ход
            </h2>
            
            <div className="grid grid-cols-1 gap-4 mb-6">
              {moves.map((move) => (
                <button
                  key={move.value}
                  onClick={() => setSelectedMove(prev => ({ ...prev, [showJoinModal]: move.value }))}
                  className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                    selectedMove[showJoinModal] === move.value
                      ? 'border-accent-primary bg-accent-primary/20 text-accent-primary'
                      : 'border-border-primary hover:border-accent-primary/50 text-text-secondary'
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <span className="text-3xl">{move.icon}</span>
                    <span className="font-rajdhani font-bold text-lg">{move.label}</span>
                  </div>
                </button>
              ))}
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={() => setShowJoinModal(null)}
                className="flex-1 py-3 bg-gray-600 text-white font-rajdhani font-bold rounded-lg hover:bg-gray-700 transition-colors"
              >
                ОТМЕНА
              </button>
              <button
                onClick={() => handleJoinGame(showJoinModal)}
                disabled={joiningGame === showJoinModal || !selectedMove[showJoinModal]}
                className={`flex-1 py-3 rounded-lg font-rajdhani font-bold transition-all duration-300 ${
                  joiningGame === showJoinModal || !selectedMove[showJoinModal]
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : 'bg-gradient-accent text-white hover:scale-105'
                }`}
              >
                {joiningGame === showJoinModal ? 'ПРИСОЕДИНЕНИЕ...' : 'ИГРАТЬ'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GameLobby;