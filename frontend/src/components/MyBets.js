import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MyBets = ({ user }) => {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('active'); // active, completed, cancelled
  const [currentPage, setCurrentPage] = useState(1);
  
  const itemsPerPage = 10;

  useEffect(() => {
    fetchMyBets();
  }, []);

  const fetchMyBets = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/games/my-bets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBets(response.data || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching my bets:', error);
      setBets([]);
      setLoading(false);
    }
  };

  const getFilteredBets = () => {
    switch (activeTab) {
      case 'active':
        return bets.filter(bet => bet.status === 'WAITING' || bet.status === 'ACTIVE');
      case 'completed':
        return bets.filter(bet => bet.status === 'COMPLETED');
      case 'cancelled':
        return bets.filter(bet => bet.status === 'CANCELLED');
      default:
        return bets;
    }
  };

  const getPaginatedBets = () => {
    const filtered = getFilteredBets();
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filtered.slice(startIndex, endIndex);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'WAITING': return 'bg-yellow-600 text-yellow-100';
      case 'ACTIVE': return 'bg-blue-600 text-blue-100';
      case 'COMPLETED': return 'bg-green-600 text-green-100';
      case 'CANCELLED': return 'bg-red-600 text-red-100';
      default: return 'bg-gray-600 text-gray-100';
    }
  };

  const BetCard = ({ bet }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 hover:border-accent-primary hover:border-opacity-100 transition-all duration-300">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-accent rounded-full flex items-center justify-center">
            <span className="font-russo text-white">#{bet.id.slice(-4)}</span>
          </div>
          <div>
            <h4 className="font-rajdhani font-bold text-white">Game #{bet.id.substring(0, 8)}</h4>
            <p className="font-roboto text-xs text-text-secondary">
              {new Date(bet.created_at).toLocaleString()}
            </p>
          </div>
        </div>
        <span className={`px-3 py-1 text-xs rounded-full font-rajdhani font-bold ${getStatusColor(bet.status)}`}>
          {bet.status}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <span className="font-roboto text-text-secondary text-sm">Bet Amount:</span>
          <p className="font-rajdhani text-green-400 font-bold">${bet.bet_amount}</p>
        </div>
        <div>
          <span className="font-roboto text-text-secondary text-sm">Opponent:</span>
          <p className="font-rajdhani text-white">{bet.opponent_username || 'Waiting...'}</p>
        </div>
      </div>
      
      <div className="mb-4">
        <span className="font-roboto text-text-secondary text-sm">Gems:</span>
        <p className="font-rajdhani text-white text-sm">
          {Object.entries(bet.bet_gems || {}).map(([type, qty]) => `${type}: ${qty}`).join(', ')}
        </p>
      </div>
      
      {bet.status === 'COMPLETED' && (
        <div className="pt-3 border-t border-accent-primary border-opacity-30">
          <div className="flex justify-between items-center">
            <span className="font-roboto text-text-secondary">Result:</span>
            <span className={`font-rajdhani font-bold ${
              bet.winner_id === user.id ? 'text-green-400' : 'text-red-400'
            }`}>
              {bet.winner_id === user.id ? 'WON' : 'LOST'}
            </span>
          </div>
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Loading My Bets...</div>
      </div>
    );
  }

  const filteredBets = getFilteredBets();
  const paginatedBets = getPaginatedBets();
  const totalPages = Math.ceil(filteredBets.length / itemsPerPage);

  return (
    <div className="min-h-screen bg-gradient-primary p-4 sm:p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-3xl sm:text-4xl md:text-6xl text-accent-primary mb-4">
          My Bets
        </h1>
        <p className="font-roboto text-lg sm:text-xl text-text-secondary">
          Track your betting history and active games
        </p>
      </div>

      {/* Tabs */}
      <div className="max-w-4xl mx-auto mb-8">
        <div className="flex space-x-1 bg-surface-sidebar rounded-lg p-1">
          {[
            { id: 'active', label: 'Active Bets', count: bets.filter(b => b.status === 'WAITING' || b.status === 'ACTIVE').length },
            { id: 'completed', label: 'Completed', count: bets.filter(b => b.status === 'COMPLETED').length },
            { id: 'cancelled', label: 'Cancelled', count: bets.filter(b => b.status === 'CANCELLED').length }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setCurrentPage(1);
              }}
              className={`flex-1 py-3 px-4 rounded-lg font-rajdhani font-bold transition-all duration-300 ${
                activeTab === tab.id
                  ? 'bg-accent-primary text-white shadow-lg'
                  : 'text-text-secondary hover:text-white hover:bg-surface-card'
              }`}
            >
              {tab.label}
              <span className="ml-2 px-2 py-1 bg-white/20 rounded-full text-xs">
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 max-w-4xl mx-auto">
        <div className="bg-surface-card border border-border-primary rounded-lg p-4 text-center">
          <h3 className="font-rajdhani font-bold text-lg text-white">Total Bets</h3>
          <p className="font-roboto text-2xl font-bold text-accent-primary">{bets.length}</p>
        </div>
        <div className="bg-surface-card border border-border-primary rounded-lg p-4 text-center">
          <h3 className="font-rajdhani font-bold text-lg text-white">Won</h3>
          <p className="font-roboto text-2xl font-bold text-green-400">
            {bets.filter(b => b.status === 'COMPLETED' && b.winner_id === user.id).length}
          </p>
        </div>
        <div className="bg-surface-card border border-border-primary rounded-lg p-4 text-center">
          <h3 className="font-rajdhani font-bold text-lg text-white">Lost</h3>
          <p className="font-roboto text-2xl font-bold text-red-400">
            {bets.filter(b => b.status === 'COMPLETED' && b.winner_id && b.winner_id !== user.id).length}
          </p>
        </div>
      </div>

      {/* Bets List */}
      <div className="max-w-4xl mx-auto">
        {paginatedBets.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {paginatedBets.map((bet) => (
              <BetCard key={bet.id} bet={bet} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🎯</div>
            <h2 className="font-russo text-2xl text-accent-secondary mb-2">
              No {activeTab} bets
            </h2>
            <p className="font-roboto text-text-secondary">
              {activeTab === 'active' 
                ? 'Create your first bet to get started!' 
                : `You don't have any ${activeTab} bets yet.`
              }
            </p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2 mt-8">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-text-secondary hover:text-white disabled:opacity-50 transition-colors"
          >
            Previous
          </button>
          
          <div className="flex space-x-1">
            {[...Array(totalPages)].map((_, index) => (
              <button
                key={index + 1}
                onClick={() => setCurrentPage(index + 1)}
                className={`px-3 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
                  currentPage === index + 1
                    ? 'bg-accent-primary text-white'
                    : 'bg-surface-card border border-border-primary text-text-secondary hover:text-white'
                }`}
              >
                {index + 1}
              </button>
            ))}
          </div>
          
          <button
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="px-4 py-2 bg-surface-card border border-border-primary rounded-lg text-text-secondary hover:text-white disabled:opacity-50 transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default MyBets;