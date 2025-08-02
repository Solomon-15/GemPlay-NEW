import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import { formatTimeWithOffset } from '../utils/timeUtils';
import Pagination from './Pagination';
import usePagination from '../hooks/usePagination';
import { formatDollarsAsGems } from '../utils/gemUtils';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BetsManagement = ({ user: currentUser }) => {
  const [stats, setStats] = useState({
    total_bets: 0,
    total_bets_value: 0,
    active_bets: 0,
    completed_bets: 0,
    cancelled_bets: 0,
    stuck_bets: 0,
    average_bet: 0
  });
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [userFilter, setUserFilter] = useState('');
  const [selectedBet, setSelectedBet] = useState(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [isResetAllModalOpen, setIsResetAllModalOpen] = useState(false);
  const [isResetBetModalOpen, setIsResetBetModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [cancellingBet, setCancellingBet] = useState(null);
  const [resettingAll, setResettingAll] = useState(false);
  const [resettingBet, setResettingBet] = useState(null);
  const [isResetFractionalModalOpen, setIsResetFractionalModalOpen] = useState(false);
  const [resettingFractional, setResettingFractional] = useState(false);
  const [isDeleteAllModalOpen, setIsDeleteAllModalOpen] = useState(false);
  const [deletingAll, setDeletingAll] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date()); // Для живого счетчика

  // Multiple selection states
  const [selectedBets, setSelectedBets] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);

  const pagination = usePagination(1, 10);

  const { showSuccessRU, showErrorRU, showWarningRU } = useNotifications();

  useEffect(() => {
    fetchStats();
    fetchBets();
  }, [statusFilter, userFilter, pagination.currentPage]);

  // Auto-refresh data every 10 seconds to show real-time status updates
  useEffect(() => {
    const refreshInterval = setInterval(() => {
      fetchStats();
      fetchBets();
    }, 10000); // Refresh every 10 seconds

    return () => clearInterval(refreshInterval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/bets/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Ошибка загрузки статистики ставок:', error);
    }
  };

  const fetchBets = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = {
        page: pagination.currentPage,
        limit: pagination.itemsPerPage
      };
      
      if (statusFilter) params.status = statusFilter;
      if (userFilter) params.user_id = userFilter;
      
      const response = await axios.get(`${API}/admin/bets/list`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
      
      setBets(response.data.bets || []);
      pagination.updatePagination(response.data.pagination?.total_count || 0);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки ставок:', error);
      setLoading(false);
    }
  };

  const cancelBet = async () => {
    if (!cancelReason.trim()) {
      showWarningRU('Укажите причину отмены ставки');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/bets/${cancellingBet.id}/cancel`,
        { reason: cancelReason },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(response.data.message);
      setIsCancelModalOpen(false);
      setCancellingBet(null);
      setCancelReason('');
      await fetchStats();
      await fetchBets();
    } catch (error) {
      console.error('Error cancelling bet:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при отмене ставки';
      showErrorRU(errorMessage);
    }
  };

  const cleanupStuckBets = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/bets/cleanup-stuck`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(`${response.data.message}. Обработано: ${response.data.total_processed} ставок`);
      await fetchStats();
      await fetchBets();
    } catch (error) {
      console.error('Error cleaning up stuck bets:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при очистке зависших ставок';
      showErrorRU(errorMessage);
    }
  };

  const resetAllBets = async () => {
    try {
      setResettingAll(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/bets/reset-all`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(`${response.data.message}. Обработано: ${response.data.total_processed} ставок`);
      setIsResetAllModalOpen(false);
      await fetchStats();
      await fetchBets();
    } catch (error) {
      console.error('Error resetting all bets:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при сбросе всех ставок';
      showErrorRU(errorMessage);
    } finally {
      setResettingAll(false);
    }
  };

  const deleteAllBets = async () => {
    try {
      setDeletingAll(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/bets/delete-all`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(`${response.data.message}. Удалено: ${response.data.actual_database_deletions} ставок`);
      setIsDeleteAllModalOpen(false);
      await fetchStats();
      await fetchBets();
    } catch (error) {
      console.error('Error deleting all bets:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при удалении всех ставок';
      showErrorRU(errorMessage);
    } finally {
      setDeletingAll(false);
    }
  };

  const resetFractionalBets = async () => {
    try {
      setResettingFractional(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/bets/reset-fractional`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.total_processed > 0) {
        showSuccessRU(`${response.data.message}. Обработано: ${response.data.total_processed} ставок`);
      } else {
        showSuccessRU('Ставки с дробными значениями гемов не найдены');
      }
      setIsResetFractionalModalOpen(false);
      await fetchStats();
      await fetchBets();
    } catch (error) {
      console.error('Error resetting fractional bets:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при сбросе ставок с дробными значениями';
      showErrorRU(errorMessage);
    } finally {
      setResettingFractional(false);
    }
  };

  const resetSingleBet = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/bets/${resettingBet.id}/cancel`,
        { reason: 'Сброс ставки администратором' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(response.data.message);
      setIsResetBetModalOpen(false);
      setResettingBet(null);
      await fetchStats();
      await fetchBets();
    } catch (error) {
      console.error('Error resetting bet:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при сбросе ставки';
      showErrorRU(errorMessage);
    }
  };

  const formatDate = (dateString) => {
    return formatTimeWithOffset(dateString, currentUser?.timezone_offset || 0);
  };

  const formatTimeAge = (createdAt) => {
    const created = new Date(createdAt);
    // Apply admin's timezone offset for correct age calculation
    const adminTimezoneOffset = currentUser?.timezone_offset || 0;
    const adjustedCreated = new Date(created.getTime() + (adminTimezoneOffset * 3600000));
    const diffInSeconds = Math.floor((currentTime - adjustedCreated) / 1000);
    
    const totalSeconds = Math.max(0, diffInSeconds);
    
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'COMPLETED': { color: 'bg-green-600', text: 'Завершена' },
      'CANCELLED': { color: 'bg-red-600', text: 'Отменена' },
      'WAITING': { color: 'bg-yellow-600', text: 'Ожидание' },
      'ACTIVE': { color: 'bg-blue-600', text: 'Активна' },
      'REVEAL': { color: 'bg-purple-600', text: 'Раскрытие' }
    };
    
    const statusInfo = statusMap[status] || { color: 'bg-gray-600', text: status };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold ${statusInfo.color}`}>
        {statusInfo.text}
      </span>
    );
  };

  const handleDetailsModal = (bet) => {
    setSelectedBet(bet);
    setIsDetailsModalOpen(true);
  };

  const handleCancelModal = (bet) => {
    setCancellingBet(bet);
    setCancelReason('');
    setIsCancelModalOpen(true);
  };

  const handleResetBetModal = (bet) => {
    setResettingBet(bet);
    setIsResetBetModalOpen(true);
  };

  // Multiple selection functions
  const handleBetSelect = (betId) => {
    const newSelected = new Set(selectedBets);
    if (newSelected.has(betId)) {
      newSelected.delete(betId);
    } else {
      newSelected.add(betId);
    }
    setSelectedBets(newSelected);
    setShowBulkActions(newSelected.size > 0);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedBets(new Set());
      setShowBulkActions(false);
    } else {
      const allBetIds = new Set(bets.map(bet => bet.id));
      setSelectedBets(allBetIds);
      setShowBulkActions(true);
    }
    setSelectAll(!selectAll);
  };

  const clearSelection = () => {
    setSelectedBets(new Set());
    setSelectAll(false);
    setShowBulkActions(false);
  };

  const handleBulkDelete = async () => {
    if (selectedBets.size === 0) return;

    const confirmed = window.confirm(`Вы уверены, что хотите удалить ${selectedBets.size} выбранных ставок? Это действие необратимо!`);
    if (!confirmed) return;

    setBulkActionLoading(true);
    const selectedBetIds = Array.from(selectedBets);
    let successCount = 0;
    let errorCount = 0;

    try {
      const token = localStorage.getItem('token');
      
      for (const betId of selectedBetIds) {
        try {
          await axios.delete(`${API}/admin/games/${betId}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          successCount++;
        } catch (error) {
          console.error(`Ошибка удаления ставки ${betId}:`, error);
          errorCount++;
        }
      }

      showSuccessRU(`Успешно удалено ${successCount} из ${selectedBets.size} ставок`);
      if (errorCount > 0) {
        showWarningRU(`Не удалось удалить ${errorCount} ставок`);
      }

      clearSelection();
      fetchBets();
    } catch (error) {
      console.error('Ошибка массового удаления:', error);
      showErrorRU('Ошибка при массовом удалении');
    } finally {
      setBulkActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-rajdhani font-bold text-white">Управление Ставками</h2>
        
        <div className="flex space-x-3">
          {/* Manual refresh button */}
          <button
            onClick={() => {
              fetchStats();
              fetchBets();
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-rajdhani font-bold transition-colors"
            title="Обновить данные"
          >
            🔄 Обновить
          </button>
          
          {/* Cleanup stuck bets button */}
          {stats.stuck_bets > 0 && (
            <button
              onClick={cleanupStuckBets}
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-rajdhani font-bold transition-colors"
            >
              🧹 Очистить зависшие ({stats.stuck_bets})
            </button>
          )}
          
          {/* Reset all bets button (SUPER_ADMIN only) */}
          <button
            onClick={() => setIsResetAllModalOpen(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-rajdhani font-bold transition-colors"
          >
            🗑️ Сбросить все ставки
          </button>
          
          {/* Delete all bets button (SUPER_ADMIN only) */}
          <button
            onClick={() => setIsDeleteAllModalOpen(true)}
            className="px-4 py-2 bg-red-800 text-white rounded-lg hover:bg-red-900 font-rajdhani font-bold transition-colors"
          >
            💥 Удалить все ставки
          </button>
          
          {/* Reset fractional bets button (SUPER_ADMIN only) */}
          <button
            onClick={() => setIsResetFractionalModalOpen(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-rajdhani font-bold transition-colors"
          >
            ⚡ Сбросить дробные ставки
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-blue-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Всего ставок</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.total_bets}</p>
              <p className="text-accent-primary text-xs">{formatDollarsAsGems(stats.total_bets_value || 0)}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Активных</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.active_bets}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-green-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Завершённых</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.completed_bets}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-red-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Отменённых</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.cancelled_bets}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-orange-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Зависших</p>
              <p className="text-white text-lg font-rajdhani font-bold">{stats.stuck_bets}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
          <div className="flex items-center">
            <div className="p-2 bg-purple-600 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-text-secondary text-sm font-rajdhani">Средняя сумма</p>
              <p className="text-white text-lg font-rajdhani font-bold">{formatDollarsAsGems(stats.average_bet || 0)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
        <h3 className="text-lg font-rajdhani font-bold text-white mb-3">Фильтры</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Статус</label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setStatusFilter('')}
                className={`px-3 py-1 text-sm rounded-lg font-rajdhani font-bold transition-colors ${
                  statusFilter === '' ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary hover:text-white'
                }`}
              >
                Все
              </button>
              <button
                onClick={() => setStatusFilter(statusFilter === 'WAITING' ? statusFilter : 'WAITING')}
                className={`px-3 py-1 text-sm rounded-lg font-rajdhani font-bold transition-colors ${
                  statusFilter === 'WAITING' ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary hover:text-white'
                }`}
              >
                Ожидают
              </button>
              <button
                onClick={() => setStatusFilter(statusFilter === 'ACTIVE' ? statusFilter : 'ACTIVE')}
                className={`px-3 py-1 text-sm rounded-lg font-rajdhani font-bold transition-colors ${
                  statusFilter === 'ACTIVE' ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary hover:text-white'
                }`}
              >
                Активные
              </button>
              <button
                onClick={() => setStatusFilter(statusFilter === 'COMPLETED' ? statusFilter : 'COMPLETED')}
                className={`px-3 py-1 text-sm rounded-lg font-rajdhani font-bold transition-colors ${
                  statusFilter === 'COMPLETED' ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary hover:text-white'
                }`}
              >
                Завершённые
              </button>
              <button
                onClick={() => setStatusFilter(statusFilter === 'CANCELLED' ? statusFilter : 'CANCELLED')}
                className={`px-3 py-1 text-sm rounded-lg font-rajdhani font-bold transition-colors ${
                  statusFilter === 'CANCELLED' ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary hover:text-white'
                }`}
              >
                Отменённые
              </button>
            </div>
          </div>

          {/* User Filter */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Фильтр по пользователю</label>
            <input
              type="text"
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              placeholder="ID пользователя"
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
            />
          </div>
        </div>
      </div>

      {/* Массовые действия */}
      {showBulkActions && (
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-text-secondary font-roboto">
                Выбрано ставок: <span className="font-bold">{selectedBets.size}</span>
              </span>
              <button
                onClick={clearSelection}
                className="text-text-secondary hover:text-white transition-colors"
              >
                Очистить выбор
              </button>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleBulkDelete}
                disabled={bulkActionLoading}
                className="px-4 py-2 bg-red-600 text-white font-rajdhani font-bold rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {bulkActionLoading ? 'Удаление...' : 'Удалить выбранные'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bets Table */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-border-primary">
          <h3 className="text-lg font-rajdhani font-bold text-white">
            Список ставок ({pagination.totalItems} записей)
          </h3>
        </div>
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-white text-lg font-roboto">Загрузка ставок...</div>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-surface-sidebar">
                <tr>
                  <th className="px-4 py-3 text-center text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={selectAll}
                      onChange={handleSelectAll}
                      className="rounded border-border-primary text-accent-primary focus:ring-accent-primary"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    ID Ставки
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Создатель
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Противник
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Сумма
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Статус
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Возраст
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Дата создания
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-primary">
                {bets.length === 0 ? (
                  <tr>
                    <td colSpan="9" className="px-4 py-8 text-center text-text-secondary">
                      Нет данных для отображения
                    </td>
                  </tr>
                ) : (
                  bets.map((bet) => (
                    <tr key={bet.id} className={`hover:bg-surface-sidebar hover:bg-opacity-50 ${
                      bet.status === 'CANCELLED' ? 'opacity-60' : ''
                    } ${bet.is_stuck ? 'bg-yellow-900 bg-opacity-20' : ''}`}>
                      <td className="px-4 py-4 whitespace-nowrap text-center">
                        <input
                          type="checkbox"
                          checked={selectedBets.has(bet.id)}
                          onChange={() => handleBetSelect(bet.id)}
                          className="rounded border-border-primary text-accent-primary focus:ring-accent-primary"
                        />
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm font-mono">
                          {bet.id ? bet.id.substring(0, 8) : 'N/A'}...
                        </div>
                        {bet.is_bot_game && (
                          <span className="inline-block px-1 py-0.5 text-xs bg-blue-600 text-white rounded">
                            BOT
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm">
                          {bet.creator?.username || 'N/A'}
                        </div>
                        {bet.creator?.email && (
                          <div className="text-text-secondary text-xs">
                            {bet.creator.email}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm">
                          {bet.opponent?.username || 'Нет'}
                        </div>
                        {bet.opponent?.email && (
                          <div className="text-text-secondary text-xs">
                            {bet.opponent.email}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-accent-primary font-rajdhani font-bold">
                          {formatDollarsAsGems(bet.bet_amount || 0)}
                        </div>
                        <div className="text-yellow-400 text-xs">
                          Комиссия: {formatDollarsAsGems(bet.commission_amount || 0)}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          {getStatusBadge(bet.status)}
                          {bet.is_stuck && (
                            <span className="text-yellow-400 text-xs">⏰</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm">
                          {formatTimeAge(bet.created_at)}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm">
                          {formatDate(bet.created_at)}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="flex space-x-2">
                          <button 
                            onClick={() => handleDetailsModal(bet)}
                            className="p-1 bg-blue-600 text-white rounded hover:bg-blue-700" 
                            title="Просмотр деталей"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          </button>
                          {bet.can_cancel && (
                            <button 
                              onClick={() => handleCancelModal(bet)}
                              className="p-1 bg-red-600 text-white rounded hover:bg-red-700" 
                              title="Отменить"
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          )}
                          {/* Reset Bet Button */}
                          <button 
                            onClick={() => handleResetBetModal(bet)}
                            className="p-1 bg-orange-600 text-white rounded hover:bg-orange-700" 
                            title="Сбросить ставку"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Pagination */}
      <Pagination
        currentPage={pagination.currentPage}
        totalPages={pagination.totalPages}
        onPageChange={pagination.handlePageChange}
        itemsPerPage={pagination.itemsPerPage}
        totalItems={pagination.totalItems}
        className="mt-6"
      />

      {/* Details Modal */}
      {isDetailsModalOpen && selectedBet && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-white">Детали ставки</h3>
              <button
                onClick={() => setIsDetailsModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-text-secondary text-sm">ID ставки:</label>
                  <div className="text-white font-mono">{selectedBet.id}</div>
                </div>
                <div>
                  <label className="text-text-secondary text-sm">Статус:</label>
                  <div>{getStatusBadge(selectedBet.status)}</div>
                </div>
                <div>
                  <label className="text-text-secondary text-sm">Сумма ставки:</label>
                  <div className="text-accent-primary font-bold">{formatDollarsAsGems(selectedBet.bet_amount || 0)}</div>
                </div>
                <div>
                  <label className="text-text-secondary text-sm">Комиссия:</label>
                  <div className="text-yellow-400 font-bold">{formatDollarsAsGems(selectedBet.commission_amount || 0)}</div>
                </div>
                <div>
                  <label className="text-text-secondary text-sm">Создана:</label>
                  <div className="text-white">{formatDate(selectedBet.created_at)}</div>
                </div>
                <div>
                  <label className="text-text-secondary text-sm">Возраст:</label>
                  <div className="text-white">{formatTimeAge(selectedBet.created_at)}</div>
                </div>
              </div>

              {/* Creator info */}
              <div>
                <label className="text-text-secondary text-sm">Создатель:</label>
                <div className="bg-surface-sidebar rounded p-2 mt-1">
                  <div className="text-white">{selectedBet.creator?.username}</div>
                  {selectedBet.creator?.email && (
                    <div className="text-text-secondary text-sm">{selectedBet.creator.email}</div>
                  )}
                  <div className="text-xs text-accent-primary">{selectedBet.creator?.type}</div>
                </div>
              </div>

              {/* Opponent info */}
              {selectedBet.opponent && (
                <div>
                  <label className="text-text-secondary text-sm">Противник:</label>
                  <div className="bg-surface-sidebar rounded p-2 mt-1">
                    <div className="text-white">{selectedBet.opponent.username}</div>
                    {selectedBet.opponent.email && (
                      <div className="text-text-secondary text-sm">{selectedBet.opponent.email}</div>
                    )}
                    <div className="text-xs text-accent-primary">{selectedBet.opponent.type}</div>
                  </div>
                </div>
              )}

              {/* Gems info */}
              {selectedBet.bet_gems && Object.keys(selectedBet.bet_gems).length > 0 && (
                <div>
                  <label className="text-text-secondary text-sm">Ставка (гемы):</label>
                  <div className="bg-surface-sidebar rounded p-2 mt-1">
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(selectedBet.bet_gems).map(([gemType, quantity]) => (
                        quantity > 0 && (
                          <span key={gemType} className="px-2 py-1 bg-accent-primary bg-opacity-20 text-accent-primary text-sm rounded">
                            {gemType}: {quantity}
                          </span>
                        )
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Moves info for completed games */}
              {selectedBet.status === 'COMPLETED' && (
                <div>
                  <label className="text-text-secondary text-sm">Результат игры:</label>
                  <div className="bg-surface-sidebar rounded p-2 mt-1">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-white">Ход создателя:</div>
                        <div className="text-accent-primary">{selectedBet.creator_move}</div>
                      </div>
                      <div>
                        <div className="text-white">Ход противника:</div>
                        <div className="text-accent-primary">{selectedBet.opponent_move}</div>
                      </div>
                    </div>
                    {selectedBet.winner_id && (
                      <div className="mt-2">
                        <div className="text-green-400">
                          Победитель: {selectedBet.winner_id === selectedBet.creator.id ? selectedBet.creator.username : selectedBet.opponent?.username}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cancel Modal */}
      {isCancelModalOpen && cancellingBet && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-white">Отменить ставку</h3>
              <button
                onClick={() => setIsCancelModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-yellow-900 border border-yellow-600 rounded-lg p-3">
                <div className="text-yellow-400 text-sm">
                  ⚠️ Вы собираетесь отменить ставку {cancellingBet.id?.substring(0, 8)}... на сумму ${cancellingBet.bet_amount?.toFixed(2)}
                </div>
              </div>

              <div>
                <label className="block text-text-secondary text-sm mb-2">Причина отмены (обязательно):</label>
                <textarea
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="Укажите причину отмены ставки..."
                  className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:outline-none focus:border-accent-primary"
                  rows="3"
                />
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setIsCancelModalOpen(false)}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold transition-colors"
                >
                  Отмена
                </button>
                <button
                  onClick={cancelBet}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-rajdhani font-bold transition-colors"
                >
                  Отменить ставку
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reset All Bets Modal */}
      {isResetAllModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-red-600 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-red-400">🗑️ Сбросить все ставки</h3>
              <button
                onClick={() => setIsResetAllModalOpen(false)}
                disabled={resettingAll}
                className="text-gray-400 hover:text-white disabled:opacity-50"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-red-900 border border-red-600 rounded-lg p-4">
                <div className="text-red-400 text-sm mb-2">
                  ⚠️ <strong>ВНИМАНИЕ!</strong> Это действие нельзя отменить!
                </div>
                <div className="text-red-300 text-sm space-y-1">
                  <div>• Будут отменены ВСЕ активные ставки ({stats.active_bets})</div>
                  <div>• Заблокированные средства будут разморожены</div>
                  <div>• Гемы и комиссия вернутся игрокам</div>
                  <div>• Обновятся все интерфейсы игры</div>
                </div>
              </div>

              <div className="text-center">
                <p className="text-white font-rajdhani text-lg mb-2">
                  Вы уверены, что хотите сбросить все ставки?
                </p>
                <p className="text-text-secondary text-sm">
                  Это действие затронет всех игроков и ботов
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setIsResetAllModalOpen(false)}
                  disabled={resettingAll}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold transition-colors disabled:opacity-50"
                >
                  Отмена
                </button>
                <button
                  onClick={resetAllBets}
                  disabled={resettingAll}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-rajdhani font-bold transition-colors disabled:opacity-50 flex items-center justify-center"
                >
                  {resettingAll ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Сброс...
                    </>
                  ) : (
                    '🗑️ Сбросить все'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reset Single Bet Modal */}
      {isResetBetModalOpen && resettingBet && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-orange-600 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-orange-400">🗑️ Сбросить ставку</h3>
              <button
                onClick={() => setIsResetBetModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-orange-900 border border-orange-600 rounded-lg p-4">
                <div className="text-orange-400 text-sm mb-2">
                  ⚠️ <strong>ВНИМАНИЕ!</strong> Это действие нельзя отменить!
                </div>
                <div className="text-orange-300 text-sm space-y-1">
                  <div>• ID ставки: {resettingBet.id?.substring(0, 8)}...</div>
                  <div>• Сумма: ${resettingBet.bet_amount?.toFixed(2)}</div>
                  <div>• Создатель: {resettingBet.creator?.username}</div>
                  {resettingBet.opponent && (
                    <div>• Противник: {resettingBet.opponent?.username}</div>
                  )}
                  <div>• Средства будут разморожены</div>
                  <div>• Ресурсы вернутся игрокам</div>
                </div>
              </div>

              <div className="text-center">
                <p className="text-white font-rajdhani text-lg mb-2">
                  Вы уверены, что хотите сбросить эту ставку?
                </p>
                <p className="text-text-secondary text-sm">
                  Ставка будет отменена, а ресурсы возвращены
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setIsResetBetModalOpen(false)}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold transition-colors"
                >
                  Отмена
                </button>
                <button
                  onClick={resetSingleBet}
                  className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-rajdhani font-bold transition-colors"
                >
                  🗑️ Сбросить
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete All Bets Modal */}
      {isDeleteAllModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-red-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-red-400">💥 Удалить все ставки</h3>
              <button
                onClick={() => setIsDeleteAllModalOpen(false)}
                disabled={deletingAll}
                className="text-gray-400 hover:text-white disabled:opacity-50"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-red-900 border border-red-600 rounded-lg p-4">
                <div className="text-red-400 text-sm mb-2">
                  ⚠️ <strong>КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ!</strong> Это действие необратимо!
                </div>
                <div className="text-red-300 text-sm space-y-1">
                  <div>• Будут ФИЗИЧЕСКИ УДАЛЕНЫ все записи ставок ({stats.total_bets})</div>
                  <div>• Активные ставки: возврат ресурсов → удаление</div>
                  <div>• Завершённые ставки: немедленное удаление</div>
                  <div>• Восстановление данных будет НЕВОЗМОЖНО</div>
                  <div>• Очистится вся история игр</div>
                </div>
              </div>

              <div className="text-center">
                <p className="text-white font-rajdhani text-lg mb-2">
                  ФИЗИЧЕСКИ удалить ВСЕ ставки из базы данных?
                </p>
                <p className="text-text-secondary text-sm">
                  Это критическая операция, которая уничтожит всю историю
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setIsDeleteAllModalOpen(false)}
                  disabled={deletingAll}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold transition-colors disabled:opacity-50"
                >
                  Отмена
                </button>
                <button
                  onClick={deleteAllBets}
                  disabled={deletingAll}
                  className="flex-1 px-4 py-2 bg-red-800 text-white rounded-lg hover:bg-red-900 font-rajdhani font-bold transition-colors disabled:opacity-50 flex items-center justify-center"
                >
                  {deletingAll ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Удаление...
                    </>
                  ) : (
                    '💥 УДАЛИТЬ ВСЁ'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reset Fractional Bets Modal */}
      {isResetFractionalModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-purple-600 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-purple-400">⚡ Сбросить дробные ставки</h3>
              <button
                onClick={() => setIsResetFractionalModalOpen(false)}
                disabled={resettingFractional}
                className="text-gray-400 hover:text-white disabled:opacity-50"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-purple-900 border border-purple-600 rounded-lg p-4">
                <div className="text-purple-400 text-sm mb-2">
                  ⚠️ <strong>ВНИМАНИЕ!</strong> Это действие нельзя отменить!
                </div>
                <div className="text-purple-300 text-sm space-y-1">
                  <div>• Будут найдены все ставки с дробными значениями гемов</div>
                  <div>• Эти ставки будут принудительно отменены</div>
                  <div>• Заблокированные ресурсы вернутся игрокам</div>
                  <div>• Комиссия будет возвращена</div>
                  <div>• Это затронет только ставки с нецелыми значениями</div>
                </div>
              </div>

              <div className="text-center">
                <p className="text-white font-rajdhani text-lg mb-2">
                  Принудительно сбросить все ставки с дробными значениями гемов?
                </p>
                <p className="text-text-secondary text-sm">
                  Операция затронет только ставки с нецелыми суммами
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setIsResetFractionalModalOpen(false)}
                  disabled={resettingFractional}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold transition-colors disabled:opacity-50"
                >
                  Отмена
                </button>
                <button
                  onClick={resetFractionalBets}
                  disabled={resettingFractional}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-rajdhani font-bold transition-colors disabled:opacity-50 flex items-center justify-center"
                >
                  {resettingFractional ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Сброс...
                    </>
                  ) : (
                    '⚡ Сбросить дробные'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BetsManagement;