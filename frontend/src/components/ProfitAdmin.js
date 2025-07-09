import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { formatCurrencyWithSymbol } from '../utils/economy';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProfitAdmin = ({ user }) => {
  const [stats, setStats] = useState(null);
  const [entries, setEntries] = useState([]);
  const [commissionSettings, setCommissionSettings] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterType, setFilterType] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeTab === 'entries') {
      fetchEntries();
    }
  }, [activeTab, currentPage, filterType]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const [statsResponse, settingsResponse] = await Promise.all([
        axios.get(`${API}/admin/profit/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/profit/commission-settings`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setStats(statsResponse.data);
      setCommissionSettings(settingsResponse.data);
    } catch (error) {
      console.error('Error fetching profit data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEntries = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '20'
      });
      
      if (filterType) {
        params.append('entry_type', filterType);
      }

      const response = await axios.get(`${API}/admin/profit/entries?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setEntries(response.data.entries);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Error fetching profit entries:', error);
    }
  };

  const StatCard = ({ title, value, icon, color, description }) => (
    <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-rajdhani text-lg font-bold text-white">{title}</h3>
          <p className="text-xs text-text-secondary">{description}</p>
        </div>
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
          {icon}
        </div>
      </div>
      <div className="font-rajdhani text-2xl font-bold text-accent-primary">
        {formatCurrencyWithSymbol(value)}
      </div>
    </div>
  );

  const ProfitOverview = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Profit"
          value={stats?.total_profit || 0}
          description="All-time profit"
          color="bg-green-600/20"
          icon={
            <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          }
        />
        <StatCard
          title="Monthly Profit"
          value={stats?.monthly_profit || 0}
          description="Last 30 days"
          color="bg-blue-600/20"
          icon={
            <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
        />
        <StatCard
          title="Weekly Profit"
          value={stats?.weekly_profit || 0}
          description="Last 7 days"
          color="bg-purple-600/20"
          icon={
            <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          }
        />
        <StatCard
          title="Daily Profit"
          value={stats?.recent_profit || 0}
          description="Last 24 hours"
          color="bg-yellow-600/20"
          icon={
            <svg className="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
            </svg>
          }
        />
      </div>

      {/* Profit by Type */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Profit by Type</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-surface-sidebar rounded-lg">
            <h4 className="font-rajdhani text-green-400 font-bold">Bet Commission</h4>
            <p className="text-xs text-text-secondary mb-2">6% from game victories</p>
            <div className="font-rajdhani text-xl font-bold text-white">
              {formatCurrencyWithSymbol(stats?.profit_by_type?.BET_COMMISSION || 0)}
            </div>
          </div>
          <div className="text-center p-4 bg-surface-sidebar rounded-lg">
            <h4 className="font-rajdhani text-purple-400 font-bold">Gift Commission</h4>
            <p className="text-xs text-text-secondary mb-2">3% from gem gifts</p>
            <div className="font-rajdhani text-xl font-bold text-white">
              {formatCurrencyWithSymbol(stats?.profit_by_type?.GIFT_COMMISSION || 0)}
            </div>
          </div>
          <div className="text-center p-4 bg-surface-sidebar rounded-lg">
            <h4 className="font-rajdhani text-blue-400 font-bold">Admin Adjustments</h4>
            <p className="text-xs text-text-secondary mb-2">Manual adjustments</p>
            <div className="font-rajdhani text-xl font-bold text-white">
              {formatCurrencyWithSymbol(stats?.profit_by_type?.ADMIN_ADJUSTMENT || 0)}
            </div>
          </div>
        </div>
      </div>

      {/* Commission Settings */}
      {commissionSettings && (
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-rajdhani text-xl font-bold text-white mb-4">Commission Settings</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="font-roboto text-text-secondary">Bet Commission:</span>
                <span className="font-rajdhani text-green-400 font-bold">{commissionSettings.bet_commission}%</span>
              </div>
              <div className="flex justify-between">
                <span className="font-roboto text-text-secondary">Gift Commission:</span>
                <span className="font-rajdhani text-purple-400 font-bold">{commissionSettings.gift_commission}%</span>
              </div>
              <div className="flex justify-between">
                <span className="font-roboto text-text-secondary">Daily Deposit Limit:</span>
                <span className="font-rajdhani text-blue-400 font-bold">{formatCurrencyWithSymbol(commissionSettings.daily_deposit_limit)}</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="font-roboto text-text-secondary">Minimum Bet:</span>
                <span className="font-rajdhani text-yellow-400 font-bold">{formatCurrencyWithSymbol(commissionSettings.min_bet)}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-roboto text-text-secondary">Maximum Bet:</span>
                <span className="font-rajdhani text-red-400 font-bold">{formatCurrencyWithSymbol(commissionSettings.max_bet)}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const ProfitEntries = () => (
    <div className="space-y-6">
      {/* Filter Controls */}
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center space-x-4">
          <label className="font-roboto text-text-secondary">Filter by type:</label>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-white font-rajdhani"
          >
            <option value="">All Types</option>
            <option value="BET_COMMISSION">Bet Commission</option>
            <option value="GIFT_COMMISSION">Gift Commission</option>
            <option value="ADMIN_ADJUSTMENT">Admin Adjustment</option>
          </select>
        </div>
        
        <button
          onClick={fetchEntries}
          className="px-4 py-2 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity"
        >
          Refresh
        </button>
      </div>

      {/* Entries Table */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-sidebar border-b border-accent-primary border-opacity-30">
              <tr>
                <th className="px-6 py-3 text-left font-rajdhani text-white">Date</th>
                <th className="px-6 py-3 text-left font-rajdhani text-white">Type</th>
                <th className="px-6 py-3 text-left font-rajdhani text-white">Amount</th>
                <th className="px-6 py-3 text-left font-rajdhani text-white">Source User</th>
                <th className="px-6 py-3 text-left font-rajdhani text-white">Description</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, index) => (
                <tr key={index} className="border-b border-accent-primary border-opacity-10 hover:bg-surface-sidebar transition-colors">
                  <td className="px-6 py-4 font-roboto text-text-secondary">
                    {new Date(entry.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-rajdhani font-bold ${
                      entry.entry_type === 'BET_COMMISSION' ? 'bg-green-600/20 text-green-400' :
                      entry.entry_type === 'GIFT_COMMISSION' ? 'bg-purple-600/20 text-purple-400' :
                      'bg-blue-600/20 text-blue-400'
                    }`}>
                      {entry.entry_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-rajdhani text-accent-primary font-bold">
                    {formatCurrencyWithSymbol(entry.amount)}
                  </td>
                  <td className="px-6 py-4 font-roboto text-white">
                    {entry.source_user?.username || 'Unknown'}
                  </td>
                  <td className="px-6 py-4 font-roboto text-text-secondary text-sm">
                    {entry.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center space-x-4 p-4 bg-surface-sidebar border-t border-accent-primary border-opacity-30">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-white font-rajdhani disabled:opacity-50"
            >
              Previous
            </button>
            <span className="font-rajdhani text-white">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-white font-rajdhani disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Loading Profit Data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-primary p-4 sm:p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="font-russo text-3xl sm:text-4xl md:text-6xl text-accent-primary mb-4">
          Profit Dashboard
        </h1>
        <p className="font-roboto text-lg sm:text-xl text-text-secondary">
          Track commissions and virtual economy performance
        </p>
      </div>

      {/* Tabs */}
      <div className="max-w-6xl mx-auto mb-8">
        <div className="flex space-x-1 bg-surface-sidebar rounded-lg p-1">
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'entries', label: 'Entries', icon: '📋' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 px-4 rounded-lg font-rajdhani font-bold transition-all duration-300 ${
                activeTab === tab.id
                  ? 'bg-accent-primary text-white shadow-lg'
                  : 'text-text-secondary hover:text-white hover:bg-surface-card'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        {activeTab === 'overview' && <ProfitOverview />}
        {activeTab === 'entries' && <ProfitEntries />}
      </div>
    </div>
  );
};

export default ProfitAdmin;