import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LivePlayers = ({ user, onGameJoined }) => {
  const [liveGames, setLiveGames] = useState([]);
  const [myBets, setMyBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [joiningGame, setJoiningGame] = useState(null);
  const [selectedMove, setSelectedMove] = useState('');
  const [showJoinModal, setShowJoinModal] = useState(null);

  const moves = [
    { id: 'rock', name: 'Rock', icon: '🪨' },
    { id: 'paper', name: 'Paper', icon: '📄' },
    { id: 'scissors', name: 'Scissors', icon: '✂️' }
  ];

  useEffect(() => {
    fetchLiveGames();
    fetchMyBets();
    const interval = setInterval(() => {
      fetchLiveGames();
      fetchMyBets();
    }, 5000); // Refresh every 5 seconds
    
    return () => clearInterval(interval);
  }, []);

  const fetchLiveGames = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/games/live`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLiveGames(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching live games:', error);
      setLoading(false);
    }
  };

  const fetchMyBets = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/games/my-bets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyBets(response.data);
    } catch (error) {
      console.error('Error fetching my bets:', error);
    }
  };

  const handleJoinGame = async (gameId) => {
    if (!selectedMove) {
      alert('Please select your move first');
      return;
    }

    setJoiningGame(gameId);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/games/${gameId}/join`, {
        move: selectedMove
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Show game result
      showGameResult(response.data);
      setShowJoinModal(null);
      setSelectedMove('');
      
      if (onGameJoined) onGameJoined();
      fetchLiveGames();
      fetchMyBets();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error joining game');
    } finally {
      setJoiningGame(null);
    }
  };

  const handleCancelGame = async (gameId) => {
    if (!confirm('Are you sure you want to cancel this game?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await axios.delete(`${API}/games/${gameId}/cancel`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert(response.data.message);
      fetchLiveGames();
      fetchMyBets();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error cancelling game');
    }
  };

  const showGameResult = (result) => {
    const resultEmojis = {
      'creator_wins': result.creator.username === user.username ? '🎉' : '😢',
      'opponent_wins': result.creator.username !== user.username ? '🎉' : '😢',
      'draw': '🤝'
    };

    const resultTexts = {
      'creator_wins': result.creator.username === user.username ? 'YOU WON!' : 'YOU LOST!',
      'opponent_wins': result.creator.username !== user.username ? 'YOU WON!' : 'YOU LOST!',
      'draw': 'DRAW!'
    };

    const resultColors = {
      'creator_wins': result.creator.username === user.username ? 'text-green-400' : 'text-red-400',
      'opponent_wins': result.creator.username !== user.username ? 'text-green-400' : 'text-red-400',
      'draw': 'text-yellow-400'
    };

    // Create modal for result
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50';
    modal.innerHTML = `
      <div class="bg-surface-card border border-border-primary rounded-xl p-8 max-w-md w-full mx-4 text-center">
        <div class="text-6xl mb-4">${resultEmojis[result.result]}</div>
        <h2 class="font-russo text-3xl ${resultColors[result.result]} mb-4">${resultTexts[result.result]}</h2>
        
        <div class="mb-6">
          <div class="flex justify-center items-center space-x-8 mb-4">
            <div class="text-center">
              <div class="text-3xl mb-2">${moves.find(m => m.id === result.creator_move)?.icon || '❓'}</div>
              <p class="text-text-secondary text-sm">${result.creator.username}</p>
            </div>
            <div class="text-2xl text-text-secondary">VS</div>
            <div class="text-center">
              <div class="text-3xl mb-2">${moves.find(m => m.id === result.opponent_move)?.icon || '❓'}</div>
              <p class="text-text-secondary text-sm">${result.opponent.username}</p>
            </div>
          </div>
          
          <div class="space-y-2 text-sm">
            <p class="text-text-secondary">Bet Amount: <span class="text-accent-primary">$${result.bet_amount}</span></p>
            <p class="text-text-secondary">Total Pot: <span class="text-accent-primary">$${result.total_pot}</span></p>
            <p class="text-text-secondary">Commission: <span class="text-yellow-400">$${result.commission.toFixed(2)}</span></p>
          </div>
        </div>
        
        <button onclick="this.parentElement.parentElement.remove()" 
                class="px-6 py-3 bg-accent-primary text-white rounded-lg font-rajdhani font-bold hover:bg-accent-secondary transition-colors">
          CLOSE
        </button>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Auto close after 10 seconds
    setTimeout(() => {
      if (modal.parentElement) {
        modal.remove();
      }
    }, 10000);
  };

  const formatTimeRemaining = (hours) => {
    if (hours >= 1) {
      return `${Math.floor(hours)}h ${Math.floor((hours % 1) * 60)}m`;
    } else {
      return `${Math.floor(hours * 60)}m`;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'WAITING': return 'text-yellow-400';
      case 'ACTIVE': return 'text-blue-400';
      case 'COMPLETED': return 'text-green-400';
      case 'CANCELLED': return 'text-red-400';
      default: return 'text-text-secondary';
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="text-white text-lg font-roboto">Loading live games...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* My Bets Section */}
      <div className="bg-surface-card border border-border-primary rounded-lg p-6">
        <h3 className="font-russo text-xl text-accent-secondary mb-4">My Bets</h3>
        
        {myBets.length === 0 ? (
          <p className="text-text-secondary text-center py-4">No active bets</p>
        ) : (
          <div className="space-y-3">
            {myBets.slice(0, 5).map((bet) => (
              <div
                key={bet.game_id}
                className="bg-surface-sidebar border border-border-primary rounded-lg p-4"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <div className="flex items-center space-x-3">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${getStatusColor(bet.status)}`}>
                        {bet.status}
                      </span>
                      <span className="text-white font-rajdhani font-bold">
                        ${bet.bet_amount}
                      </span>
                      {bet.opponent && (
                        <span className="text-text-secondary text-sm">
                          vs {bet.opponent.username}
                        </span>
                      )}
                    </div>
                    
                    {bet.status === 'COMPLETED' && (
                      <div className="mt-2 text-sm">
                        <span className={bet.winner_id === user.id ? 'text-green-400' : 'text-red-400'}>
                          {bet.winner_id === user.id ? 'WON' : bet.winner_id ? 'LOST' : 'DRAW'}
                        </span>
                        {bet.commission > 0 && (
                          <span className="text-yellow-400 ml-2">
                            Commission: ${bet.commission.toFixed(2)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {bet.status === 'WAITING' && bet.is_creator && (
                    <button
                      onClick={() => handleCancelGame(bet.game_id)}
                      className="px-3 py-1 bg-red-600 text-white rounded text-sm font-rajdhani font-bold hover:bg-red-700 transition-colors"
                    >
                      CANCEL
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Available Bets Section */}
      <div className="bg-surface-card border border-border-primary rounded-lg p-6">
        <h3 className="font-russo text-xl text-accent-secondary mb-4">Available Bets</h3>
        
        {liveGames.length === 0 ? (
          <p className="text-text-secondary text-center py-8">No available games</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {liveGames.map((game) => (
              <div
                key={game.game_id}
                className="bg-surface-sidebar border border-border-primary rounded-lg p-4 hover:border-accent-primary transition-colors"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <img
                      src={`/icons/${game.creator.gender === 'male' ? 'men' : 'women'}.svg`}
                      alt="Avatar"
                      className="w-8 h-8"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                    <div>
                      <p className="text-white font-roboto font-bold text-sm">
                        {game.creator.username}
                      </p>
                      <p className="text-text-secondary text-xs">
                        {formatTimeRemaining(game.time_remaining_hours)} left
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <p className="text-accent-primary font-rajdhani font-bold text-lg">
                      ${game.bet_amount}
                    </p>
                  </div>
                </div>
                
                {/* Gem Display */}
                <div className="flex flex-wrap gap-1 mb-3">
                  {Object.entries(game.bet_gems).map(([gemType, quantity]) => (
                    <div key={gemType} className="flex items-center space-x-1 text-xs">
                      <img
                        src={`/gems/gem-${gemType.toLowerCase()}.svg`}
                        alt={gemType}
                        className="w-4 h-4"
                      />
                      <span className="text-text-secondary">{quantity}</span>
                    </div>
                  ))}
                </div>
                
                <button
                  onClick={() => setShowJoinModal(game)}
                  className="w-full py-2 px-4 bg-gradient-accent text-white rounded-lg font-rajdhani font-bold hover:opacity-90 transition-opacity"
                >
                  ACCEPT
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Join Game Modal */}
      {showJoinModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-surface-card border border-border-primary rounded-xl p-6 max-w-md w-full">
            <h3 className="font-russo text-2xl text-accent-primary mb-4 text-center">
              Join Battle
            </h3>
            
            <div className="text-center mb-6">
              <p className="text-text-secondary mb-2">vs {showJoinModal.creator.username}</p>
              <p className="font-rajdhani text-2xl font-bold text-accent-primary">
                ${showJoinModal.bet_amount}
              </p>
            </div>
            
            <div className="mb-6">
              <h4 className="font-russo text-lg text-white mb-4 text-center">Choose Your Move</h4>
              <div className="grid grid-cols-3 gap-3">
                {moves.map((move) => (
                  <button
                    key={move.id}
                    onClick={() => setSelectedMove(move.id)}
                    className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                      selectedMove === move.id
                        ? 'border-accent-primary bg-accent-primary bg-opacity-20'
                        : 'border-border-primary hover:border-accent-secondary'
                    }`}
                  >
                    <div className="text-3xl mb-1">{move.icon}</div>
                    <div className="font-rajdhani font-bold text-white text-sm">{move.name}</div>
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowJoinModal(null);
                  setSelectedMove('');
                }}
                className="flex-1 py-3 px-4 bg-gray-600 text-white rounded-lg font-rajdhani font-bold hover:bg-gray-700 transition-colors"
              >
                CANCEL
              </button>
              <button
                onClick={() => handleJoinGame(showJoinModal.game_id)}
                disabled={!selectedMove || joiningGame === showJoinModal.game_id}
                className={`flex-1 py-3 px-4 rounded-lg font-rajdhani font-bold transition-colors ${
                  selectedMove && joiningGame !== showJoinModal.game_id
                    ? 'bg-gradient-accent text-white hover:opacity-90'
                    : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                }`}
              >
                {joiningGame === showJoinModal.game_id ? 'JOINING...' : 'BATTLE!'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LivePlayers;