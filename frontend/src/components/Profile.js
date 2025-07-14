import React, { useState } from 'react';
import axios from 'axios';
import { formatCurrencyWithSymbol, formatDollarAmount, validateDailyLimit, ECONOMY_CONFIG } from '../utils/economy';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';
import HeaderPortfolio from './HeaderPortfolio';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Profile = ({ user, onUpdateUser, setCurrentView }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [depositAmount, setDepositAmount] = useState('');
  const [depositing, setDepositing] = useState(false);
  
  const handleAddBalance = async () => {
    const amount = parseFloat(depositAmount);
    if (!amount || amount <= 0) {
      alert('Please enter a valid amount');
      return;
    }
    
    const remainingLimit = user.daily_limit_max - user.daily_limit_used;
    if (amount > remainingLimit) {
      alert(`You can only add up to ${formatDollarAmount(remainingLimit).replace('$', '$')} more today`);
      return;
    }
    
    setDepositing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/auth/add-balance`, {
        amount: amount
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setDepositAmount('');
      
      // 🔄 АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ LOBBY ПОСЛЕ ДОБАВЛЕНИЯ БАЛАНСА
      const globalRefresh = getGlobalLobbyRefresh();
      globalRefresh.triggerLobbyRefresh();
      console.log(`💵 Added $${amount} balance - triggering lobby refresh`);
      
      if (onUpdateUser) {
        onUpdateUser();
      }
      alert(response.data.message);
    } catch (error) {
      alert(error.response?.data?.detail || 'Error adding balance');
    } finally {
      setDepositing(false);
    }
  };
  
  const ProfileOverview = () => (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <div className="flex items-center space-x-6">
          <div className="w-20 h-20 bg-gradient-accent rounded-full flex items-center justify-center">
            <span className="font-russo text-white text-2xl">
              {user.username.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1">
            <h2 className="font-russo text-2xl text-white mb-2">{user.username}</h2>
            <p className="font-roboto text-text-secondary mb-1">{user.email}</p>
            <div className="flex items-center space-x-4">
              <span className={`px-3 py-1 rounded-full text-xs font-rajdhani font-bold ${
                user.role === 'ADMIN' || user.role === 'SUPER_ADMIN' 
                  ? 'bg-red-600 text-red-100' 
                  : 'bg-blue-600 text-blue-100'
              }`}>
                {user.role}
              </span>
              <span className="px-3 py-1 bg-green-600 text-green-100 rounded-full text-xs font-rajdhani font-bold">
                {user.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <div className="w-10 h-10 bg-green-600/20 rounded-lg flex items-center justify-center mx-auto mb-2">
            <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          </div>
          <h3 className="font-rajdhani font-bold text-lg text-white">Balance</h3>
          <p className="font-roboto text-xl font-bold text-green-400">
            {formatDollarAmount(user.virtual_balance || 0)}
          </p>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center mx-auto mb-2">
            <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h3 className="font-rajdhani font-bold text-lg text-white">Games Played</h3>
          <p className="font-roboto text-xl font-bold text-blue-400">
            {user.total_games_played || 0}
          </p>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <div className="w-10 h-10 bg-accent-primary/20 rounded-lg flex items-center justify-center mx-auto mb-2">
            <svg className="w-6 h-6 text-accent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
            </svg>
          </div>
          <h3 className="font-rajdhani font-bold text-lg text-white">Games Won</h3>
          <p className="font-roboto text-xl font-bold text-accent-primary">
            {user.total_games_won || 0}
          </p>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 text-center">
          <div className="w-10 h-10 bg-purple-600/20 rounded-lg flex items-center justify-center mx-auto mb-2">
            <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <h3 className="font-rajdhani font-bold text-lg text-white">Win Rate</h3>
          <p className="font-roboto text-xl font-bold text-purple-400">
            {user.total_games_played > 0 
              ? Math.round((user.total_games_won / user.total_games_played) * 100) 
              : 0
            }%
          </p>
        </div>
      </div>

      {/* Account Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-russo text-xl text-accent-secondary mb-4">Account Information</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Member Since:</span>
              <span className="font-rajdhani text-white">
                {new Date(user.created_at).toLocaleDateString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Last Login:</span>
              <span className="font-rajdhani text-white">
                {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Email Verified:</span>
              <span className={`font-rajdhani font-bold ${
                user.email_verified ? 'text-green-400' : 'text-red-400'
              }`}>
                {user.email_verified ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Gender:</span>
              <span className="font-rajdhani text-white capitalize">
                {user.gender}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-russo text-xl text-accent-secondary mb-4">Gaming Statistics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Total Wagered:</span>
              <span className="font-rajdhani text-white">
                {formatDollarAmount(user.total_amount_wagered || 0)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Total Won:</span>
              <span className="font-rajdhani text-green-400">
                ${user.total_amount_won?.toFixed(2) || '0.00'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Net Profit:</span>
              <span className={`font-rajdhani font-bold ${
                (user.total_amount_won || 0) - (user.total_amount_wagered || 0) >= 0 
                  ? 'text-green-400' 
                  : 'text-red-400'
              }`}>
                ${((user.total_amount_won || 0) - (user.total_amount_wagered || 0)).toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Daily Limit Used:</span>
              <span className="font-rajdhani text-white">
                {formatCurrencyWithSymbol(user.daily_limit_used || 0)} / {formatCurrencyWithSymbol(user.daily_limit_max || 1000)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const ProfileSettings = () => {
    const remainingLimit = user.daily_limit_max - user.daily_limit_used;
    const canDeposit = remainingLimit > 0;
    
    return (
      <div className="space-y-6">
        {/* Balance Management */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-russo text-xl text-accent-secondary mb-4">Balance Management</h3>
          
          {/* Daily Limit Info */}
          <div className="mb-6 p-4 bg-surface-sidebar rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <span className="font-roboto text-text-secondary">Daily Deposit Limit:</span>
              <span className="font-rajdhani text-white font-bold">
                {formatCurrencyWithSymbol(user.daily_limit_max)}
              </span>
            </div>
            <div className="flex justify-between items-center mb-2">
              <span className="font-roboto text-text-secondary">Used Today:</span>
              <span className="font-rajdhani text-warning font-bold">
                {formatCurrencyWithSymbol(user.daily_limit_used)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-roboto text-text-secondary">Remaining:</span>
              <span className={`font-rajdhani font-bold ${canDeposit ? 'text-green-400' : 'text-red-400'}`}>
                {formatCurrencyWithSymbol(remainingLimit)}
              </span>
            </div>
            
            {/* Progress Bar */}
            <div className="mt-3">
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-500 to-yellow-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(100, (user.daily_limit_used / user.daily_limit_max) * 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
          
          {/* Deposit Form */}
          <div className="space-y-4">
            <div>
              <label className="block font-roboto text-text-secondary text-sm mb-2">
                Add Virtual Dollars to Balance
              </label>
              <div className="flex space-x-3">
                <input
                  type="number"
                  min="1"
                  max={remainingLimit}
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  placeholder="Enter amount"
                  className="flex-1 px-4 py-3 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-white font-rajdhani text-center focus:outline-none focus:border-accent-primary"
                  disabled={!canDeposit}
                />
                <button
                  onClick={handleAddBalance}
                  disabled={!canDeposit || depositing || !depositAmount}
                  className={`px-6 py-3 rounded-lg font-rajdhani font-bold transition-all duration-300 ${
                    canDeposit && !depositing && depositAmount
                      ? 'bg-gradient-accent text-white hover:scale-105 hover:shadow-lg'
                      : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {depositing ? 'ADDING...' : 'ADD BALANCE'}
                </button>
              </div>
            </div>
            
            {!canDeposit && (
              <p className="font-roboto text-red-400 text-sm">
                Daily limit reached. Limit resets at 00:00 server time.
              </p>
            )}
            
            <div className="grid grid-cols-3 gap-2">
              {[100, 500, remainingLimit].map((amount) => (
                <button
                  key={amount}
                  onClick={() => setDepositAmount(amount.toString())}
                  disabled={!canDeposit || amount <= 0}
                  className={`py-2 px-4 rounded-lg font-rajdhani font-bold text-sm transition-all duration-300 ${
                    canDeposit && amount > 0
                      ? 'bg-surface-sidebar border border-accent-primary border-opacity-30 text-white hover:bg-accent-primary hover:text-white'
                      : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {formatCurrencyWithSymbol(amount > 0 ? amount : 0, false)}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        {/* Other Settings */}
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
          <h3 className="font-russo text-xl text-accent-secondary mb-4">Other Settings</h3>
          <p className="font-roboto text-text-secondary text-center py-8">
            Additional profile settings will be available in future updates.
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-primary">
      {/* Mobile: Balance Display at top */}
      <div className="md:hidden sticky top-0 z-30 bg-surface-sidebar border-b border-border-primary p-4">
        <HeaderPortfolio user={user} />
      </div>
      
      <div className="p-4 sm:p-6">
        {/* Mobile Navigation Menu */}
        <div className="md:hidden mb-6">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
            <h3 className="font-russo text-lg text-accent-primary mb-4">Additional Sections</h3>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setCurrentView && setCurrentView('history')}
                className="flex items-center justify-center space-x-2 p-3 bg-surface-sidebar border border-border-primary rounded-lg hover:bg-surface-card transition-colors"
              >
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-rajdhani text-white text-sm">History</span>
              </button>
              
              <button
                onClick={() => setCurrentView && setCurrentView('notification-demo')}
                className="flex items-center justify-center space-x-2 p-3 bg-surface-sidebar border border-border-primary rounded-lg hover:bg-surface-card transition-colors"
              >
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  <span className="font-rajdhani text-white text-sm">Notifications</span>
                </button>
            </div>
          </div>
        </div>

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-russo text-2xl sm:text-3xl md:text-6xl text-accent-primary mb-4">
            Profile
          </h1>
          <p className="font-roboto text-base sm:text-lg md:text-xl text-text-secondary px-4">
            Manage your account and view your gaming statistics
          </p>
        </div>

      {/* Tabs */}
      <div className="max-w-4xl mx-auto mb-8">
        <div className="flex space-x-1 bg-surface-sidebar rounded-lg p-1">
          {[
            { id: 'overview', label: 'Overview', icon: '👤' },
            { id: 'settings', label: 'Settings', icon: '⚙️' }
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
      <div className="max-w-6xl mx-auto">
        {activeTab === 'overview' && <ProfileOverview />}
        {activeTab === 'settings' && <ProfileSettings />}
      </div>
      </div>
    </div>
  );
};

export default Profile;