import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { formatCurrencyWithSymbol, formatDollarAmount, validateDailyLimit, ECONOMY_CONFIG } from '../utils/economy';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';
import { useNotifications } from './NotificationContext';
import HeaderPortfolio from './HeaderPortfolio';
import NotificationSettings from './NotificationSettings';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Utility function to format time with user's timezone offset
const formatTimeWithOffset = (dateString, timezoneOffset = 0) => {
  const date = new Date(dateString);
  // Assume the dateString is in UTC, apply user's timezone offset directly
  const adjustedTime = new Date(date.getTime() + (timezoneOffset * 3600000));
  return adjustedTime.toLocaleString();
};

// Utility function to format short ID
const formatShortId = (id) => {
  if (!id || id.length < 6) return id;
  return `${id.substring(0, 3)}...${id.substring(id.length - 3)}`;
};

const Profile = ({ user, onUpdateUser, setCurrentView, onOpenAdminPanel, onLogout }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [depositAmount, setDepositAmount] = useState('');
  const [depositing, setDepositing] = useState(false);
  
  // Edit profile states
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    username: '',
    gender: 'male',
    timezone_offset: 0
  });
  const [updating, setUpdating] = useState(false);
  const [showFullId, setShowFullId] = useState(false);
  
  // Sync editForm with user data
  useEffect(() => {
    if (user) {
      setEditForm({
        username: user.username || '',
        gender: user.gender || 'male',
        timezone_offset: user.timezone_offset || 0
      });
    }
  }, [user.username, user.gender, user.timezone_offset]);
  
  // Notification system
  const { showSuccess, showError, showSuccessRU, showErrorRU } = useNotifications();
  
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
      
      const globalRefresh = getGlobalLobbyRefresh();
      globalRefresh.triggerLobbyRefresh();
      console.log(`💵 Added $${amount} balance - triggering lobby refresh`);
      
      if (onUpdateUser) {
        onUpdateUser();
      }
      showSuccess(response.data.message);
    } catch (error) {
      showError(error.response?.data?.detail || 'Error adding balance');
    } finally {
      setDepositing(false);
    }
  };
  
  // Handle profile update
  const handleUpdateProfile = useCallback(async () => {
    if (!editForm.username.trim()) {
      showError('Username cannot be empty');
      return;
    }
    
    setUpdating(true);
    try {
      const token = localStorage.getItem('token');
      
      // Log the request data for debugging
      console.log('🔄 Updating profile with data:', editForm);
      
      const response = await axios.put(`${API}/auth/profile`, editForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('✅ Profile update response:', response.data);
      
      if (onUpdateUser) {
        onUpdateUser();
      }
      
      setIsEditing(false);
      showSuccessRU('Профиль успешно обновлен');
    } catch (error) {
      console.error('❌ Profile update error:', error);
      console.error('Error response:', error.response?.data);
      showErrorRU(error.response?.data?.detail || 'Ошибка при обновлении профиля');
    } finally {
      setUpdating(false);
    }
  }, [editForm, onUpdateUser, showError, showSuccessRU, showErrorRU]);

  // Handle cancel edit
  const handleCancelEdit = useCallback(() => {
    setEditForm({
      username: user.username || '',
      gender: user.gender || 'male',
      timezone_offset: user.timezone_offset || 0
    });
    setIsEditing(false);
  }, [user.username, user.gender, user.timezone_offset]);

  // Handle form input changes
  const handleUsernameChange = useCallback((e) => {
    setEditForm(prev => ({ ...prev, username: e.target.value }));
  }, []);

  const handleGenderChange = useCallback((e) => {
    setEditForm(prev => ({ ...prev, gender: e.target.value }));
  }, []);

  const handleTimezoneChange = useCallback((e) => {
    setEditForm(prev => ({ ...prev, timezone_offset: parseInt(e.target.value) }));
  }, []);
  
  // Handle ID click (show full ID and copy via text selection)
  const handleIdClick = () => {
    setShowFullId(!showFullId);
    
    // Create a temporary element to select text
    const tempElement = document.createElement('textarea');
    tempElement.value = user.id;
    document.body.appendChild(tempElement);
    tempElement.select();
    tempElement.setSelectionRange(0, 99999); // For mobile devices
    
    try {
      document.execCommand('copy');
      showSuccessRU('ID скопирован в буфер обмена!');
    } catch (err) {
      showErrorRU('Не удалось скопировать ID');
    } finally {
      document.body.removeChild(tempElement);
    }
  };
  
  const ProfileOverview = () => (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <div className="flex items-center space-x-6">
          <div className="w-20 h-20 bg-gradient-accent rounded-full flex items-center justify-center">
            <img 
              src={isEditing ? (editForm.gender === 'female' ? '/Women.svg' : '/Men.svg') : (user.gender === 'female' ? '/Women.svg' : '/Men.svg')} 
              alt={isEditing ? (editForm.gender === 'female' ? 'Female' : 'Male') : (user.gender === 'female' ? 'Female' : 'Male')}
              className="w-22 h-22"
            />
          </div>
          <div className="flex-1">
            {isEditing ? (
              <div className="space-y-3">
                <div>
                  <label className="block font-roboto text-text-secondary text-sm mb-1">Username</label>
                  <input
                    type="text"
                    value={editForm.username}
                    onChange={handleUsernameChange}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-white font-rajdhani focus:outline-none focus:border-accent-primary"
                  />
                </div>
                <div>
                  <label className="block font-roboto text-text-secondary text-sm mb-1">Gender</label>
                  <select
                    value={editForm.gender}
                    onChange={handleGenderChange}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-white font-rajdhani focus:outline-none focus:border-accent-primary"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>
                <div>
                  <label className="block font-roboto text-text-secondary text-sm mb-1">Timezone Offset (UTC)</label>
                  <select
                    value={editForm.timezone_offset}
                    onChange={handleTimezoneChange}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-accent-primary border-opacity-30 rounded-lg text-white font-rajdhani focus:outline-none focus:border-accent-primary"
                  >
                    {Array.from({length: 25}, (_, i) => i - 12).map(offset => (
                      <option key={offset} value={offset}>
                        UTC{offset >= 0 ? '+' : ''}{offset}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center space-x-3 mb-2">
                  <h2 className="font-russo text-2xl text-white">{user.username}</h2>
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-3 py-1 bg-accent-primary text-white rounded-lg text-sm font-rajdhani font-bold hover:bg-opacity-80 transition-colors"
                  >
                    Edit Profile
                  </button>
                </div>
                <p className="font-roboto text-text-secondary mb-1">{user.email}</p>
              </>
            )}
            <div className="flex items-center space-x-4 mb-2">
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
            <div 
              className="font-roboto text-text-secondary text-sm cursor-pointer hover:text-accent-primary transition-colors"
              onClick={handleIdClick}
              title="Click to show full ID and copy"
            >
              ID: {showFullId ? user.id : formatShortId(user.id)}
            </div>
            {isEditing && (
              <div className="flex space-x-2 mt-3">
                <button
                  onClick={handleUpdateProfile}
                  disabled={updating}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-rajdhani font-bold hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {updating ? 'Saving...' : 'Save'}
                </button>
                <button
                  onClick={handleCancelEdit}
                  disabled={updating}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg text-sm font-rajdhani font-bold hover:bg-gray-700 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            )}
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
                {formatTimeWithOffset(user.created_at, user.timezone_offset || 0)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Last Login:</span>
              <span className="font-rajdhani text-white">
                {user.last_login ? formatTimeWithOffset(user.last_login, user.timezone_offset || 0) : 'Never'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Timezone:</span>
              <span className="font-rajdhani text-white">
                UTC{user.timezone_offset >= 0 ? '+' : ''}{user.timezone_offset || 0}
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
                {formatDollarAmount(user.total_amount_won || 0)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Net Profit:</span>
              <span className={`font-rajdhani font-bold ${
                (user.total_amount_won || 0) - (user.total_amount_wagered || 0) >= 0 
                  ? 'text-green-400' 
                  : 'text-red-400'
              }`}>
                {formatDollarAmount((user.total_amount_won || 0) - (user.total_amount_wagered || 0))}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-roboto text-text-secondary">Daily Limit Used:</span>
              <span className="font-rajdhani text-white">
                {formatDollarAmount(user.daily_limit_used || 0)} / {formatDollarAmount(user.daily_limit_max || 1000)}
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
                {formatDollarAmount(user.daily_limit_max)}
              </span>
            </div>
            <div className="flex justify-between items-center mb-2">
              <span className="font-roboto text-text-secondary">Used Today:</span>
              <span className="font-rajdhani text-warning font-bold">
                {formatDollarAmount(user.daily_limit_used)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-roboto text-text-secondary">Remaining:</span>
              <span className={`font-rajdhani font-bold ${canDeposit ? 'text-green-400' : 'text-red-400'}`}>
                {formatDollarAmount(remainingLimit)}
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
                  {formatDollarAmount(amount > 0 ? amount : 0)}
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
      {/* Mobile: Balance Display at top - now hidden to avoid duplication */}
      <div className="md:hidden hidden sticky top-0 z-30 bg-surface-sidebar border-b border-border-primary p-4">
        <HeaderPortfolio user={user} />
      </div>
      
      <div className="p-4 sm:p-6">
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
            { id: 'settings', label: 'Settings', icon: '⚙️' },
            { id: 'notifications', label: 'Уведомления', icon: '🔔' }
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
        {activeTab === 'notifications' && <NotificationSettings />}
      </div>
      </div>
    </div>
  );
};

export default Profile;