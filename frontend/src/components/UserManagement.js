import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import { formatDollarAmount } from '../utils/economy';
import { formatTimeWithOffset, formatDateWithOffset } from '../utils/timeUtils';
import Pagination from './Pagination';
import usePagination from '../hooks/usePagination';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserManagement = ({ user: currentUser }) => {
  const { showSuccessRU, showErrorRU, showWarningRU } = useNotifications();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  const [roleFilter, setRoleFilter] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [sortOrder, setSortOrder] = useState('asc');
  const [balanceMin, setBalanceMin] = useState('');
  const [balanceMax, setBalanceMax] = useState('');
  const [totalMin, setTotalMin] = useState('');      // Новый фильтр по минимальному TOTAL
  const [totalMax, setTotalMax] = useState('');      // Новый фильтр по максимальному TOTAL
  
  const [selectedUser, setSelectedUser] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date()); // Для живого счетчика
  
  // Multiple selection states
  const [selectedUsers, setSelectedUsers] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  
  const pagination = usePagination(1, 20);
  
  // Modal states
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isBanModalOpen, setIsBanModalOpen] = useState(false);
  const [isGemsModalOpen, setIsGemsModalOpen] = useState(false);
  const [isBetsModalOpen, setIsBetsModalOpen] = useState(false);
  const [isResetBalancesModalOpen, setIsResetBalancesModalOpen] = useState(false);
  const [isResetUserBetsModalOpen, setIsResetUserBetsModalOpen] = useState(false);
  const [isResetUserBalanceModalOpen, setIsResetUserBalanceModalOpen] = useState(false);
  const [isUnfreezeCommissionModalOpen, setIsUnfreezeCommissionModalOpen] = useState(false);
  const [isCreateUserModalOpen, setIsCreateUserModalOpen] = useState(false);
  const [resettingBalances, setResettingBalances] = useState(false);
  const [resettingUserBets, setResettingUserBets] = useState(null);
  const [resettingUserBalance, setResettingUserBalance] = useState(null);
  const [unfreezingCommission, setUnfreezingCommission] = useState(false);
  const [isInfoModalOpen, setIsInfoModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  
  // Form states
  const [banReason, setBanReason] = useState('');
  const [banDuration, setBanDuration] = useState('');
  const [deleteReason, setDeleteReason] = useState('');
  const [notificationText, setNotificationText] = useState('');
  
  // Create user form
  const [createUserForm, setCreateUserForm] = useState({
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    role: 'USER',
    virtual_balance: 1000,
    daily_limit_max: 1000,
    gender: 'male',
    status: 'ACTIVE',
    ban_reason: ''
  });
  const [createUserLoading, setCreateUserLoading] = useState(false);
  
  // Edit form
  const [editForm, setEditForm] = useState({
    username: '',
    email: '',
    role: '',
    virtual_balance: 0
  });

  // User details states
  const [userGems, setUserGems] = useState([]);
  const [userBets, setUserBets] = useState([]);
  const [userStats, setUserStats] = useState({});
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');

  useEffect(() => {
    const savedFilters = localStorage.getItem('userManagementFilters');
    if (savedFilters) {
      try {
        const filters = JSON.parse(savedFilters);
        setSearchTerm(filters.searchTerm || '');
        setStatusFilter(filters.statusFilter || '');
        setRoleFilter(filters.roleFilter || '');
        setSortBy(filters.sortBy || '');
        setSortOrder(filters.sortOrder || 'asc');
        setBalanceMin(filters.balanceMin || '');
        setBalanceMax(filters.balanceMax || '');
        setTotalMin(filters.totalMin || '');
        setTotalMax(filters.totalMax || '');
      } catch (error) {
        console.error('Error loading saved filters:', error);
      }
    }
  }, []);

  useEffect(() => {
    const filters = {
      searchTerm,
      statusFilter,
      roleFilter,
      sortBy,
      sortOrder,
      balanceMin,
      balanceMax,
      totalMin,
      totalMax
    };
    localStorage.setItem('userManagementFilters', JSON.stringify(filters));
  }, [searchTerm, statusFilter, roleFilter, sortBy, sortOrder, balanceMin, balanceMax, totalMin, totalMax]);

  // Debounce search term to prevent cursor loss
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 500); // 500ms delay

    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    fetchUsers();
  }, [pagination.currentPage, debouncedSearchTerm, statusFilter, roleFilter, sortBy, sortOrder, balanceMin, balanceMax, totalMin, totalMax]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        page: pagination.currentPage.toString(),
        limit: pagination.itemsPerPage.toString()
      });
      
      if (debouncedSearchTerm) params.append('search', debouncedSearchTerm);
      if (statusFilter) params.append('status', statusFilter);
      if (roleFilter) params.append('role', roleFilter);
      if (sortBy) params.append('sort_by', sortBy);
      if (sortOrder) params.append('sort_order', sortOrder);
      if (balanceMin) params.append('balance_min', balanceMin);
      if (balanceMax) params.append('balance_max', balanceMax);
      if (totalMin) params.append('total_min', totalMin);
      if (totalMax) params.append('total_max', totalMax);
      
      const response = await axios.get(`${API}/admin/users?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Применяем локальную сортировку по ролям только если нет явной сортировки
      let finalUsers = response.data.users || [];
      
      if (!sortBy) {
        // Применяем дефолтную сортировку по ролям только если пользователь не выбрал другую сортировку
        finalUsers = finalUsers.sort((a, b) => {
          const roleOrder = {
            'SUPER_ADMIN': 1,
            'ADMIN': 2, 
            'USER': 3,
            'HUMAN_BOT': 4,
            'REGULAR_BOT': 5
          };
          
          const aOrder = roleOrder[a.user_type] || roleOrder[a.role] || 5;
          const bOrder = roleOrder[b.user_type] || roleOrder[b.role] || 5;
          
          if (aOrder === bOrder) {
            return a.username.localeCompare(b.username);
          }
          
          return aOrder - bOrder;
        });
      }
      // Если sortBy установлен, используем сортировку от backend
      
      setUsers(finalUsers);
      pagination.updatePagination(response.data.total || 0);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки пользователей:', error);
      setLoading(false);
    }
  };

  const fetchUserDetails = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch real data from API endpoints
      const [gemsResponse, betsResponse, statsResponse] = await Promise.all([
        axios.get(`${API}/admin/users/${userId}/gems`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/users/${userId}/bets`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/users/${userId}/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setUserGems(gemsResponse.data.gems || []);
      setUserBets(betsResponse.data.active_bets || []);
      setUserStats({
        total_games: statsResponse.data.game_stats?.total_games || 0,
        games_won: statsResponse.data.game_stats?.games_won || 0,
        games_lost: statsResponse.data.game_stats?.games_lost || 0,
        games_draw: statsResponse.data.game_stats?.games_draw || 0,
        win_rate: statsResponse.data.game_stats?.win_rate || 0,
        profit: statsResponse.data.financial_stats?.total_profit || 0,
        gifts_sent: statsResponse.data.financial_stats?.gifts_sent || 0,
        gifts_received: statsResponse.data.financial_stats?.gifts_received || 0,
        ip_history: statsResponse.data.ip_history || []
      });
    } catch (error) {
      console.error('Error fetching user details:', error);
      showErrorRU('Ошибка при загрузке данных пользователя');
    }
  };

  // Utility functions
  const formatDate = (dateString) => {
    return formatDateWithOffset(dateString, currentUser?.timezone_offset || 0);
  };

  const formatDateTime = (dateString) => {
    return formatTimeWithOffset(dateString, currentUser?.timezone_offset || 0);
  };

  const getUserStatusBadge = (status) => {
    const statusMap = {
      'ACTIVE': { color: 'bg-green-600', text: 'Активен' },
      'BANNED': { color: 'bg-red-600', text: 'Заблокирован' },
      'EMAIL_PENDING': { color: 'bg-yellow-600', text: 'Ожидает подтв.' }
    };
    
    const statusInfo = statusMap[status] || { color: 'bg-gray-600', text: status };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold ${statusInfo.color}`}>
        {statusInfo.text}
      </span>
    );
  };

  const getUserOnlineStatusBadge = (user) => {
    let onlineStatus;
    
    if (user.user_type === 'HUMAN_BOT' || user.user_type === 'REGULAR_BOT') {
      onlineStatus = user.bot_status;
    } else {
      onlineStatus = user.online_status;
    }
    
    const statusMap = {
      'ONLINE': { color: 'bg-green-500', text: 'Онлайн' },
      'OFFLINE': { color: 'bg-gray-500', text: 'Офлайн' },
      'BANNED': { color: 'bg-red-500', text: 'BANNED' }
    };
    
    const statusInfo = statusMap[onlineStatus] || { color: 'bg-gray-500', text: onlineStatus };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold ${statusInfo.color}`}>
        {statusInfo.text}
      </span>
    );
  };

  const getUserRoleBadge = (user) => {
    if (user.user_type === 'HUMAN_BOT') {
      return (
        <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold bg-orange-600`}>
          Human-бот
        </span>
      );
    }
    
    if (user.user_type === 'REGULAR_BOT') {
      return (
        <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold bg-indigo-600`}>
          Обычный бот
        </span>
      );
    }
    
    const roleMap = {
      'USER': { color: 'bg-blue-600', text: 'Игрок' },
      'ADMIN': { color: 'bg-purple-600', text: 'Админ' },
      'SUPER_ADMIN': { color: 'bg-red-600', text: 'Супер-админ' }
    };
    
    const roleInfo = roleMap[user.role] || { color: 'bg-gray-600', text: user.role };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold ${roleInfo.color}`}>
        {roleInfo.text}
      </span>
    );
  };

  // Calculate suspicious activity flags
  const getSuspiciousFlags = (user) => {
    const flags = [];
    
    // High win rate (>80% over 10+ games)
    const totalGames = user.total_games_played || 0;
    const gamesWon = user.total_games_won || 0;
    const winRate = totalGames > 0 ? (gamesWon / totalGames) * 100 : 0;
    
    if (totalGames >= 10 && winRate > 80) {
      flags.push({
        type: 'high_winrate',
        message: `Высокий винрейт: ${winRate.toFixed(1)}% за ${totalGames} игр`
      });
    }
    
    // Additional flags can be added here based on actual data
    return flags;
  };

  // Additional gem utilities
  const getGemsTooltipContent = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/users/${userId}/gems`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.gems && response.data.gems.length > 0) {
        return response.data.gems
          .map(gem => `${gem.type} x${gem.quantity}`)
          .join(', ');
      }
      return 'Нет гемов';
    } catch (error) {
      console.error('Ошибка получения данных о гемах:', error);
      return 'Ошибка загрузки';
    }
  };

  // State for gems tooltips
  const [gemsTooltips, setGemsTooltips] = useState({});

  // Load gems tooltip data
  const loadGemsTooltip = async (userId) => {
    if (!gemsTooltips[userId]) {
      const content = await getGemsTooltipContent(userId);
      setGemsTooltips(prev => ({ ...prev, [userId]: content }));
    }
  };

  // Event handlers
  const handleSearch = useCallback((e) => {
    const newSearchTerm = e.target.value;
    setSearchTerm(newSearchTerm);
    
    // Only reset page to 1 if search term actually changed
    if (searchTerm !== newSearchTerm && newSearchTerm.length > 0) {
      pagination.handlePageChange(1);
    }
  }, [searchTerm, pagination]);

  const handleStatusFilter = (status) => {
    setStatusFilter(status);
    pagination.handlePageChange(1);
  };
  
  const handleRoleFilter = (role) => {
    setRoleFilter(role);
    pagination.handlePageChange(1);
  };
  
  const handleSortChange = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    pagination.handlePageChange(1);
  };
  
  const handleBalanceFilter = () => {
    pagination.handlePageChange(1);
  };
  
  const handleTotalFilter = () => {
    pagination.handlePageChange(1);
  };
  
  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('');
    setRoleFilter('');
    setSortBy('');
    setSortOrder('asc');
    setBalanceMin('');
    setBalanceMax('');
    setTotalMin('');
    setTotalMax('');
    pagination.handlePageChange(1);
  };
  
  const handleColumnSort = (columnField) => {
    if (sortBy === columnField) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(columnField);
      setSortOrder('desc');
    }
    pagination.handlePageChange(1);
  };
  
  const getSortIcon = (columnField) => {
    if (sortBy !== columnField) {
      return (
        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" className="opacity-50">
          <path d="M6 2L8 4H4L6 2Z" />
          <path d="M6 10L8 8H4L6 10Z" />
        </svg>
      );
    }
    
    if (sortOrder === 'desc') {
      return (
        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" className="text-accent-primary">
          <path d="M6 10L2 6H10L6 10Z" />
        </svg>
      );
    } else {
      return (
        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" className="text-accent-primary">
          <path d="M6 2L10 6H2L6 2Z" />
        </svg>
      );
    }
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setEditForm({
      username: user.username,
      email: user.email,
      role: user.role,
      virtual_balance: user.virtual_balance || 0
    });
    setIsEditModalOpen(true);
  };

  const handleSubmitEdit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/users/${selectedUser.id}`, editForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setIsEditModalOpen(false);
      fetchUsers();
      showSuccessRU('Пользователь обновлен');
    } catch (error) {
      console.error('Ошибка обновления пользователя:', error);
      showErrorRU('Ошибка при обновлении пользователя');
    }
  };

  const handleBanUser = (user) => {
    setSelectedUser(user);
    setBanReason('');
    setBanDuration('');
    setIsBanModalOpen(true);
  };

  const submitBan = async () => {
    if (!banReason.trim()) {
      showWarningRU('Укажите причину бана');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const banData = {
        reason: banReason,
        duration: banDuration || undefined
      };

      await axios.post(`${API}/admin/users/${selectedUser.id}/ban`, banData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setIsBanModalOpen(false);
      fetchUsers();
      showSuccessRU('Пользователь забанен');
    } catch (error) {
      console.error('Ошибка бана:', error);
      showErrorRU('Ошибка при бане пользователя');
    }
  };

  const handleUnbanUser = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/users/${userId}/unban`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchUsers();
      showSuccessRU('Пользователь разбанен');
    } catch (error) {
      console.error('Ошибка разбана:', error);
      showErrorRU('Ошибка при разбане пользователя');
    }
  };

  const handleGemsModal = async (user) => {
    setSelectedUser(user);
    await fetchUserDetails(user.id);
    setIsGemsModalOpen(true);
  };

  const handleBetsModal = async (user) => {
    setSelectedUser(user);
    await fetchUserDetails(user.id);
    setIsBetsModalOpen(true);
  };

  const cancelUserBet = async (betId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/users/${selectedUser.id}/bets/${betId}/cancel`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(response.data.message);
      await fetchUserDetails(selectedUser.id); // Refresh data
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
        `${API}/admin/users/${selectedUser.id}/bets/cleanup-stuck`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(`${response.data.message}. Обработано: ${response.data.total_processed} ставок`);
      await fetchUserDetails(selectedUser.id); // Refresh data
    } catch (error) {
      console.error('Error cleaning up stuck bets:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при очистке зависших ставок';
      showErrorRU(errorMessage);
    }
  };

  const resetAllBalances = async () => {
    try {
      setResettingBalances(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/users/reset-all-balances`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(`${response.data.message}. Обработано: ${response.data.total_users_processed} пользователей`);
      setIsResetBalancesModalOpen(false);
      await fetchUsers(); // Refresh data
    } catch (error) {
      console.error('Error resetting all balances:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при сбросе всех балансов';
      showErrorRU(errorMessage);
    } finally {
      setResettingBalances(false);
    }
  };

  const unfreezeStuckCommission = async () => {
    try {
      setUnfreezingCommission(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/users/unfreeze-stuck-commission`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        const { message, total_amount_unfrozen, total_users_affected } = response.data;
        showSuccessRU(`${message}. Разморожено: $${total_amount_unfrozen} для ${total_users_affected} пользователей`);
        setIsUnfreezeCommissionModalOpen(false);
        await fetchUsers(); // Refresh user data to show updated balances
      }
    } catch (error) {
      console.error('Error unfreezing stuck commission:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при разморозке зависшей комиссии';
      showErrorRU(errorMessage);
    } finally {
      setUnfreezingCommission(false);
    }
  };

  const resetUserBets = async (user) => {
    try {
      setResettingUserBets(user.id);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/users/${user.id}/reset-bets`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(`${response.data.message}. Обработано: ${response.data.total_processed} ставок`);
      await fetchUsers(); // Refresh data
    } catch (error) {
      console.error('Error resetting user bets:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при сбросе ставок пользователя';
      showErrorRU(errorMessage);
    } finally {
      setResettingUserBets(null);
    }
  };

  const resetUserBalance = async (user) => {
    try {
      setResettingUserBalance(user.id);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/admin/users/${user.id}/reset-balance`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      showSuccessRU(`${response.data.message}. Баланс: $${response.data.new_balance}`);
      await fetchUsers(); // Refresh data
    } catch (error) {
      console.error('Error resetting user balance:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка при сбросе баланса пользователя';
      showErrorRU(errorMessage);
    } finally {
      setResettingUserBalance(null);
    }
  };

  const handleInfoModal = async (user) => {
    setSelectedUser(user);
    await fetchUserDetails(user.id);
    setIsInfoModalOpen(true);
  };

  const handleDeleteUser = (user) => {
    setSelectedUser(user);
    setDeleteReason('');
    setIsDeleteModalOpen(true);
  };

  const submitDelete = async () => {
    if (!deleteReason.trim()) {
      showWarningRU('Укажите причину удаления');
      return;
    }

    if (currentUser?.role !== 'SUPER_ADMIN') {
      showErrorRU('Только SUPER_ADMIN может удалять аккаунты');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/users/${selectedUser.id}`, {
        headers: { Authorization: `Bearer ${token}` },
        data: { reason: deleteReason }
      });

      setIsDeleteModalOpen(false);
      fetchUsers();
      showSuccessRU('Пользователь удален');
    } catch (error) {
      console.error('Ошибка удаления:', error);
      showErrorRU('Ошибка при удалении пользователя');
    }
  };

  // Multiple selection functions
  const handleUserSelect = (userId) => {
    const newSelected = new Set(selectedUsers);
    if (newSelected.has(userId)) {
      newSelected.delete(userId);
    } else {
      newSelected.add(userId);
    }
    setSelectedUsers(newSelected);
    setShowBulkActions(newSelected.size > 0);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedUsers(new Set());
      setShowBulkActions(false);
    } else {
      const allUserIds = new Set(users.map(user => user.id));
      setSelectedUsers(allUserIds);
      setShowBulkActions(true);
    }
    setSelectAll(!selectAll);
  };

  const clearSelection = () => {
    setSelectedUsers(new Set());
    setSelectAll(false);
    setShowBulkActions(false);
  };

  const handleBulkDelete = async () => {
    if (selectedUsers.size === 0) return;

    if (currentUser?.role !== 'SUPER_ADMIN') {
      showErrorRU('Только SUPER_ADMIN может удалять аккаунты');
      return;
    }

    const reason = prompt('Укажите причину массового удаления:');
    if (!reason || !reason.trim()) {
      showWarningRU('Причина удаления обязательна');
      return;
    }

    // Check if any selected users are admins
    const selectedUserObjects = users.filter(user => selectedUsers.has(user.id));
    const adminUsers = selectedUserObjects.filter(user => user.role === 'ADMIN' || user.role === 'SUPER_ADMIN');
    
    if (adminUsers.length > 0) {
      showErrorRU(`Нельзя удалить администраторов: ${adminUsers.map(u => u.username).join(', ')}`);
      return;
    }

    const confirmed = window.confirm(`Вы уверены, что хотите удалить ${selectedUsers.size} выбранных пользователей? Это действие необратимо!`);
    if (!confirmed) return;

    setBulkActionLoading(true);
    const selectedUserIds = Array.from(selectedUsers);
    let successCount = 0;
    let errorCount = 0;

    try {
      const token = localStorage.getItem('token');
      
      for (const userId of selectedUserIds) {
        try {
          await axios.delete(`${API}/admin/users/${userId}`, {
            headers: { Authorization: `Bearer ${token}` },
            data: { reason: reason }
          });
          successCount++;
        } catch (error) {
          console.error(`Ошибка удаления пользователя ${userId}:`, error);
          errorCount++;
        }
      }

      showSuccessRU(`Успешно удалено ${successCount} из ${selectedUsers.size} пользователей`);
      if (errorCount > 0) {
        showWarningRU(`Не удалось удалить ${errorCount} пользователей`);
      }

      clearSelection();
      fetchUsers();
    } catch (error) {
      console.error('Ошибка массового удаления:', error);
      showErrorRU('Ошибка при массовом удалении');
    } finally {
      setBulkActionLoading(false);
    }
  };

  // Gem management functions
  const handleFreezeGems = async (gemType, quantity, reason) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/users/${selectedUser.id}/gems/freeze`, {
        gem_type: gemType,
        quantity: quantity,
        reason: reason || 'Admin action'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      showSuccessRU(`${quantity} ${gemType} гемов заморожено`);
      await fetchUserDetails(selectedUser.id); // Refresh data
    } catch (error) {
      console.error('Ошибка заморозки гемов:', error);
      showErrorRU('Ошибка при заморозке гемов');
    }
  };

  const handleUnfreezeGems = async (gemType, quantity, reason) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/users/${selectedUser.id}/gems/unfreeze`, {
        gem_type: gemType,
        quantity: quantity,
        reason: reason || 'Admin action'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      showSuccessRU(`${quantity} ${gemType} гемов разморожено`);
      await fetchUserDetails(selectedUser.id); // Refresh data
    } catch (error) {
      console.error('Ошибка разморозки гемов:', error);
      showErrorRU('Ошибка при разморозке гемов');
    }
  };

  const handleDeleteGems = async (gemType, quantity, reason) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/users/${selectedUser.id}/gems/${gemType}?quantity=${quantity}&reason=${encodeURIComponent(reason || 'Admin action')}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      showSuccessRU(`${quantity} ${gemType} гемов удалено`);
      await fetchUserDetails(selectedUser.id); // Refresh data
    } catch (error) {
      console.error('Ошибка удаления гемов:', error);
      showErrorRU('Ошибка при удалении гемов');
    }
  };

  const handleToggleSuspicious = async (user, reason) => {
    try {
      const token = localStorage.getItem('token');
      const currentFlags = getSuspiciousFlags(user);
      const isSuspicious = currentFlags.length === 0; // Toggle logic

      await axios.post(`${API}/admin/users/${user.id}/flag-suspicious`, {
        is_suspicious: isSuspicious,
        reason: reason || 'Admin action'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const action = isSuspicious ? 'отмечен как подозрительный' : 'снята метка подозрительности';
      showSuccessRU(`Пользователь ${action}`);
      fetchUsers(); // Refresh users list
    } catch (error) {
      console.error('Ошибка изменения флага подозрительности:', error);
      showErrorRU('Ошибка при изменении статуса пользователя');
    }
  };

  const handleModifyGems = async (gemType, change, reason, notificationMessage) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/users/${selectedUser.id}/gems/modify`, {
        gem_type: gemType,
        change: change,
        reason: reason || 'Admin action',
        notification: notificationMessage
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const action = change > 0 ? 'добавлено' : 'удалено';
      showSuccessRU(`${Math.abs(change)} ${gemType} гемов ${action}`);
      await fetchUserDetails(selectedUser.id); // Refresh data
      fetchUsers(); // Refresh users list to update totals
    } catch (error) {
      console.error('Ошибка изменения гемов:', error);
      showErrorRU('Ошибка при изменении гемов');
    }
  };

  // Modal Components
  const EditUserModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-rajdhani text-xl font-bold text-white">Редактировать пользователя</h3>
          <button
            onClick={() => setIsEditModalOpen(false)}
            className="text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmitEdit} className="space-y-4">
          <div>
            <label className="block text-text-secondary text-sm font-rajdhani mb-1">Имя пользователя</label>
            <input
              type="text"
              value={editForm.username}
              onChange={(e) => setEditForm({...editForm, username: e.target.value})}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
              required
            />
          </div>

          <div>
            <label className="block text-text-secondary text-sm font-rajdhani mb-1">Email</label>
            <input
              type="email"
              value={editForm.email}
              onChange={(e) => setEditForm({...editForm, email: e.target.value})}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
              required
            />
          </div>

          <div>
            <label className="block text-text-secondary text-sm font-rajdhani mb-1">Роль</label>
            <select
              value={editForm.role}
              onChange={(e) => setEditForm({...editForm, role: e.target.value})}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
            >
              <option value="USER">USER</option>
              <option value="ADMIN">ADMIN</option>
              <option value="SUPER_ADMIN">SUPER_ADMIN</option>
            </select>
          </div>

          <div>
            <label className="block text-text-secondary text-sm font-rajdhani mb-1">Баланс ($)</label>
            <input
              type="number"
              step="0.01"
              value={editForm.virtual_balance}
              onChange={(e) => setEditForm({...editForm, virtual_balance: parseFloat(e.target.value) || 0})}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="submit"
              className="flex-1 py-2 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity"
            >
              Сохранить
            </button>
            <button
              type="button"
              onClick={() => setIsEditModalOpen(false)}
              className="flex-1 py-2 bg-gray-600 text-white font-rajdhani font-bold rounded-lg hover:bg-gray-700 transition-colors"
            >
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const BanUserModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-surface-card border border-red-500 border-opacity-30 rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-rajdhani text-xl font-bold text-red-400">Забанить пользователя</h3>
          <button
            onClick={() => setIsBanModalOpen(false)}
            className="text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-4">
          <p className="text-text-secondary">Пользователь: <span className="text-white font-bold">{selectedUser?.username}</span></p>
          <p className="text-text-secondary">Email: <span className="text-white">{selectedUser?.email}</span></p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-text-secondary text-sm font-rajdhani mb-1">Причина бана *</label>
            <textarea
              value={banReason}
              onChange={(e) => setBanReason(e.target.value)}
              placeholder="Укажите причину бана..."
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
              rows="3"
              required
            />
          </div>

          <div>
            <label className="block text-text-secondary text-sm font-rajdhani mb-1">Длительность (опционально)</label>
            <select
              value={banDuration}
              onChange={(e) => setBanDuration(e.target.value)}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
            >
              <option value="">Постоянный бан</option>
              <option value="1hour">1 час</option>
              <option value="1day">1 день</option>
              <option value="1week">1 неделя</option>
              <option value="1month">1 месяц</option>
            </select>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              onClick={submitBan}
              className="flex-1 py-2 bg-red-600 text-white font-rajdhani font-bold rounded-lg hover:bg-red-700 transition-colors"
            >
              Забанить
            </button>
            <button
              onClick={() => setIsBanModalOpen(false)}
              className="flex-1 py-2 bg-gray-600 text-white font-rajdhani font-bold rounded-lg hover:bg-gray-700 transition-colors"
            >
              Отмена
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const GemsModal = () => {
    const [gemAction, setGemAction] = useState(''); // 'freeze', 'unfreeze', 'delete', 'modify'
    const [selectedGem, setSelectedGem] = useState(null);
    const [actionQuantity, setActionQuantity] = useState(1);
    const [actionReason, setActionReason] = useState('');
    const [modifyType, setModifyType] = useState('increase'); // 'increase' or 'decrease'
    const [customNotification, setCustomNotification] = useState('');

    const handleGemAction = async (action, gem) => {
      setGemAction(action);
      setSelectedGem(gem);
      setActionQuantity(1);
      setActionReason('');
      setCustomNotification('');
      setModifyType('increase');
    };

    const submitGemAction = async () => {
      if (!selectedGem || !actionQuantity || actionQuantity <= 0) {
        showWarningRU('Укажите корректное количество');
        return;
      }

      try {
        if (gemAction === 'freeze') {
          const availableQuantity = selectedGem.quantity - (selectedGem.frozen_quantity || 0);
          if (actionQuantity > availableQuantity) {
            showWarningRU('Недостаточно доступных гемов для заморозки');
            return;
          }
          await handleFreezeGems(selectedGem.type, actionQuantity, actionReason);
        } else if (gemAction === 'unfreeze') {
          if (actionQuantity > (selectedGem.frozen_quantity || 0)) {
            showWarningRU('Недостаточно замороженных гемов для разморозки');
            return;
          }
          await handleUnfreezeGems(selectedGem.type, actionQuantity, actionReason);
        } else if (gemAction === 'delete') {
          const availableQuantity = selectedGem.quantity - (selectedGem.frozen_quantity || 0);
          if (actionQuantity > availableQuantity) {
            showWarningRU('Нельзя удалять замороженные гемы. Сначала разморозьте их.');
            return;
          }
          await handleDeleteGems(selectedGem.type, actionQuantity, actionReason);
        } else if (gemAction === 'modify') {
          const change = modifyType === 'increase' ? actionQuantity : -actionQuantity;
          if (modifyType === 'decrease' && actionQuantity > selectedGem.quantity) {
            showWarningRU('Недостаточно гемов для уменьшения');
            return;
          }
          await handleModifyGems(selectedGem.type, change, actionReason, customNotification);
        }
        
        setGemAction('');
        setSelectedGem(null);
      } catch (error) {
        console.error('Ошибка операции с гемами:', error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-rajdhani text-xl font-bold text-white">💎 Управление гемами - {selectedUser?.username}</h3>
            <button
              onClick={() => setIsGemsModalOpen(false)}
              className="text-gray-400 hover:text-white"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-4">
            {userGems.length === 0 ? (
              <p className="text-text-secondary text-center py-4">У пользователя нет гемов</p>
            ) : (
              userGems.map((gem, index) => (
                <div key={index} className="bg-surface-sidebar rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-accent flex items-center justify-center">
                        💎
                      </div>
                      <div>
                        <div className="text-white font-rajdhani font-bold">{gem.type}</div>
                        <div className="text-text-secondary text-sm">
                          Всего: {gem.quantity} шт | Доступно: {gem.quantity - (gem.frozen_quantity || 0)} шт | Заморожено: {gem.frozen_quantity || 0} шт
                        </div>
                        <div className="text-accent-primary text-sm">
                          Общая стоимость: ${(gem.quantity * gem.price).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 mt-2 flex-wrap">
                    <button 
                      onClick={() => handleGemAction('modify', gem)}
                      className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 mb-1"
                    >
                      Изменить кол-во
                    </button>
                    <button 
                      onClick={() => handleGemAction('freeze', gem)}
                      className="px-3 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700 mb-1"
                      disabled={gem.quantity - (gem.frozen_quantity || 0) <= 0}
                    >
                      Заморозить
                    </button>
                    <button 
                      onClick={() => handleGemAction('unfreeze', gem)}
                      className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 mb-1"
                      disabled={(gem.frozen_quantity || 0) <= 0}
                    >
                      Разморозить
                    </button>
                    <button 
                      onClick={() => handleGemAction('delete', gem)}
                      className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 mb-1"
                      disabled={gem.quantity - (gem.frozen_quantity || 0) <= 0}
                    >
                      Удалить
                    </button>
                  </div>
                </div>
              ))
            )}

            {/* Action Modal */}
            {gemAction && selectedGem && (
              <div className="mt-4 bg-surface-sidebar rounded-lg p-4 border border-accent-primary border-opacity-30">
                <h4 className="font-rajdhani font-bold text-white mb-2">
                  {gemAction === 'freeze' && 'Заморозить гемы'}
                  {gemAction === 'unfreeze' && 'Разморозить гемы'}
                  {gemAction === 'delete' && 'Удалить гемы'}
                  {gemAction === 'modify' && 'Изменить количество гемов'}
                </h4>
                <p className="text-text-secondary text-sm mb-3">
                  Гем: {selectedGem.type} | 
                  {gemAction === 'freeze' && ` Доступно: ${selectedGem.quantity - (selectedGem.frozen_quantity || 0)} шт`}
                  {gemAction === 'unfreeze' && ` Заморожено: ${selectedGem.frozen_quantity || 0} шт`}
                  {gemAction === 'delete' && ` Доступно: ${selectedGem.quantity - (selectedGem.frozen_quantity || 0)} шт`}
                  {gemAction === 'modify' && ` Текущее количество: ${selectedGem.quantity} шт`}
                </p>
                
                <div className="space-y-3">
                  {gemAction === 'modify' && (
                    <div>
                      <label className="block text-text-secondary text-sm mb-1">Действие:</label>
                      <select
                        value={modifyType}
                        onChange={(e) => setModifyType(e.target.value)}
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white"
                      >
                        <option value="increase">Увеличить количество</option>
                        <option value="decrease">Уменьшить количество</option>
                      </select>
                    </div>
                  )}
                  
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Количество:</label>
                    <input
                      type="number"
                      min="1"
                      max={
                        gemAction === 'freeze' ? selectedGem.quantity - (selectedGem.frozen_quantity || 0) :
                        gemAction === 'unfreeze' ? (selectedGem.frozen_quantity || 0) :
                        gemAction === 'delete' ? selectedGem.quantity - (selectedGem.frozen_quantity || 0) :
                        gemAction === 'modify' && modifyType === 'decrease' ? selectedGem.quantity :
                        999999
                      }
                      value={actionQuantity}
                      onChange={(e) => setActionQuantity(parseInt(e.target.value) || 1)}
                      className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-text-secondary text-sm mb-1">Причина (опционально):</label>
                    <input
                      type="text"
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Причина действия..."
                      className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white"
                    />
                  </div>

                  {gemAction === 'modify' && (
                    <div>
                      <label className="block text-text-secondary text-sm mb-1">Уведомление пользователю:</label>
                      <textarea
                        value={customNotification}
                        onChange={(e) => setCustomNotification(e.target.value)}
                        placeholder="Персональное сообщение пользователю о изменении гемов..."
                        className="w-full px-3 py-2 bg-surface-card border border-border-primary rounded-lg text-white"
                        rows="2"
                      />
                    </div>
                  )}
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={submitGemAction}
                      className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary font-rajdhani font-bold"
                    >
                      Подтвердить
                    </button>
                    <button
                      onClick={() => {
                        setGemAction('');
                        setSelectedGem(null);
                      }}
                      className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                    >
                      Отмена
                    </button>
                  </div>
                </div>
              </div>
            )}
            
            <div className="mt-6 border-t border-border-primary pt-4">
              <label className="block text-text-secondary text-sm font-rajdhani mb-2">
                Общее уведомление игроку (опционально):
              </label>
              <textarea
                value={notificationText}
                onChange={(e) => setNotificationText(e.target.value)}
                placeholder="Напишите общее сообщение пользователю о изменениях..."
                className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                rows="3"
              />
            </div>
          </div>
        </div>
      </div>
    );
  };

  const BetsModal = () => {
    const getStatusBadge = (status) => {
      const statusMap = {
        'WAITING': { color: 'bg-yellow-600', text: 'Ожидание' },
        'ACTIVE': { color: 'bg-blue-600', text: 'Активная' },
        'REVEAL': { color: 'bg-purple-600', text: 'Раскрытие' },
        'COMPLETED': { color: 'bg-green-600', text: 'Завершена' },
        'CANCELLED': { color: 'bg-red-600', text: 'Отменена' }
      };
      
      const statusInfo = statusMap[status] || { color: 'bg-gray-600', text: status };
      
      return (
        <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold ${statusInfo.color}`}>
          {statusInfo.text}
        </span>
      );
    };

    const canCancelBet = (bet) => {
      return bet.status === 'WAITING';
    };

    const isStuckBet = (bet) => {
      const betTime = new Date(bet.created_at);
      // Apply admin's timezone offset for correct comparison
      const adminTimezoneOffset = currentUser?.timezone_offset || 0;
      const adjustedBetTime = new Date(betTime.getTime() + (adminTimezoneOffset * 3600000));
      const now = new Date();
      const hoursDiff = (now - adjustedBetTime) / (1000 * 60 * 60);
      return hoursDiff > 24 && ['WAITING', 'ACTIVE', 'REVEAL'].includes(bet.status);
    };

    const hasStuckBets = userBets.some(bet => isStuckBet(bet));

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-rajdhani text-xl font-bold text-white">🎯 Ставки пользователя - {selectedUser?.username}</h3>
            <button
              onClick={() => setIsBetsModalOpen(false)}
              className="text-gray-400 hover:text-white"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Cleanup stuck bets button */}
          {hasStuckBets && (
            <div className="mb-4 p-3 bg-yellow-900 border border-yellow-600 rounded-lg">
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-yellow-400 font-rajdhani font-bold text-sm">⚠️ Обнаружены зависшие ставки</div>
                  <div className="text-yellow-300 text-xs">Ставки, находящиеся в состоянии ожидания более 24 часов</div>
                </div>
                <button
                  onClick={cleanupStuckBets}
                  className="px-4 py-2 bg-orange-600 text-white text-sm rounded-lg hover:bg-orange-700 font-rajdhani font-bold transition-colors"
                >
                  🧹 Очистить зависшие
                </button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {userBets.length === 0 ? (
              <p className="text-text-secondary text-center py-4">У пользователя нет активных ставок</p>
            ) : (
              userBets.map((bet, index) => (
                <div key={index} className={`bg-surface-sidebar rounded-lg p-4 border-l-4 ${
                  isStuckBet(bet) ? 'border-yellow-500' : 
                  bet.status === 'WAITING' ? 'border-blue-500' : 
                  bet.status === 'ACTIVE' ? 'border-green-500' : 'border-gray-500'
                }`}>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <div className="text-white font-rajdhani font-bold text-lg">
                          ${bet.amount}
                        </div>
                        {getStatusBadge(bet.status)}
                        {bet.is_creator && (
                          <span className="px-2 py-1 text-xs rounded-full bg-purple-600 text-white font-rajdhani">
                            Создатель
                          </span>
                        )}
                        {isStuckBet(bet) && (
                          <span className="px-2 py-1 text-xs rounded-full bg-yellow-600 text-white font-rajdhani">
                            ⏰ Зависла
                          </span>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                        <div className="text-text-secondary">
                          <span className="text-white">ID:</span> {bet.id}
                        </div>
                        <div className="text-text-secondary">
                          <span className="text-white">Создана:</span> {formatDateTime(bet.created_at)}
                        </div>
                        {bet.opponent && (
                          <div className="text-text-secondary">
                            <span className="text-white">Противник:</span> {bet.opponent}
                          </div>
                        )}
                        <div className="text-text-secondary">
                          <span className="text-white">Возраст:</span> {
                            (() => {
                              const created = new Date(bet.created_at);
                              // Apply admin's timezone offset
                              const adminTimezoneOffset = currentUser?.timezone_offset || 0;
                              const adjustedCreated = new Date(created.getTime() + (adminTimezoneOffset * 3600000));
                              const diffInSeconds = Math.floor((currentTime - adjustedCreated) / 1000);
                              const totalSeconds = Math.max(0, diffInSeconds);
                              
                              const hours = Math.floor(totalSeconds / 3600);
                              const minutes = Math.floor((totalSeconds % 3600) / 60);
                              const seconds = totalSeconds % 60;
                              
                              return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                            })()
                          }
                        </div>
                      </div>

                      {/* Gems display */}
                      {bet.gems && Object.keys(bet.gems).length > 0 && (
                        <div className="mt-2">
                          <div className="text-text-secondary text-xs mb-1">Ставка:</div>
                          <div className="flex flex-wrap gap-1">
                            {Object.entries(bet.gems).map(([gemType, quantity]) => (
                              quantity > 0 && (
                                <span key={gemType} className="px-2 py-1 bg-accent-primary bg-opacity-20 text-accent-primary text-xs rounded font-rajdhani">
                                  {gemType}: {quantity}
                                </span>
                              )
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex flex-col space-y-2 ml-4">
                      {canCancelBet(bet) && (
                        <button 
                          onClick={() => cancelUserBet(bet.id)}
                          className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 font-rajdhani font-bold transition-colors"
                          title="Отменить ставку"
                        >
                          🚫 Отменить
                        </button>
                      )}
                      {!canCancelBet(bet) && (
                        <span className="px-3 py-1 bg-gray-600 text-gray-300 text-xs rounded font-rajdhani text-center">
                          Нельзя отменить
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Summary */}
          {userBets.length > 0 && (
            <div className="mt-4 pt-4 border-t border-border-primary">
              <div className="flex justify-between text-sm">
                <span className="text-text-secondary">Всего ставок:</span>
                <span className="text-white font-rajdhani font-bold">{userBets.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-secondary">Можно отменить:</span>
                <span className="text-green-400 font-rajdhani font-bold">
                  {userBets.filter(bet => canCancelBet(bet)).length}
                </span>
              </div>
              {hasStuckBets && (
                <div className="flex justify-between text-sm">
                  <span className="text-yellow-400">Зависших:</span>
                  <span className="text-yellow-400 font-rajdhani font-bold">
                    {userBets.filter(bet => isStuckBet(bet)).length}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  const InfoModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="font-rajdhani text-2xl font-bold text-white">ℹ️ Карточка игрока - {selectedUser?.username}</h3>
          <button
            onClick={() => setIsInfoModalOpen(false)}
            className="text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Статистика игр */}
          <div className="bg-surface-sidebar rounded-lg p-4">
            <h4 className="font-rajdhani font-bold text-accent-primary mb-3">📊 Статистика игр</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">Всего игр:</span>
                <span className="text-white">{userStats.total_games || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-400">Побед:</span>
                <span className="text-green-400">{userStats.games_won || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-red-400">Поражений:</span>
                <span className="text-red-400">{userStats.games_lost || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Ничьих:</span>
                <span className="text-gray-400">{userStats.games_draw || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Win Rate:</span>
                <span className="text-accent-primary">{userStats.win_rate || 0}%</span>
              </div>
            </div>
          </div>

          {/* Финансовая статистика */}
          <div className="bg-surface-sidebar rounded-lg p-4">
            <h4 className="font-rajdhani font-bold text-accent-primary mb-3">💰 Финансовые данные</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">Общий результат:</span>
                <span className={`${(userStats.profit || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${(userStats.profit || 0).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Подарков отправлено:</span>
                <span className="text-white">{userStats.gifts_sent || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Подарков получено:</span>
                <span className="text-white">{userStats.gifts_received || 0}</span>
              </div>
            </div>
          </div>

          {/* Активность */}
          <div className="bg-surface-sidebar rounded-lg p-4">
            <h4 className="font-rajdhani font-bold text-accent-primary mb-3">🕒 Активность</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">Регистрация:</span>
                <span className="text-white">{formatDateTime(selectedUser?.created_at)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Последний визит:</span>
                <span className="text-yellow-400">{formatDateTime(selectedUser?.last_login || selectedUser?.created_at)}</span>
              </div>
            </div>
          </div>

          {/* IP адреса */}
          <div className="bg-surface-sidebar rounded-lg p-4">
            <h4 className="font-rajdhani font-bold text-accent-primary mb-3">🌐 IP История</h4>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {(userStats.ip_history || ['192.168.1.1', '10.0.0.1']).map((ip, index) => (
                <div key={index} className="text-xs text-text-secondary">
                  {ip} {index === 0 && <span className="text-accent-primary">(текущий)</span>}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-center">
          <button className="px-6 py-2 bg-accent-primary text-white font-rajdhani font-bold rounded-lg hover:opacity-90">
            📤 Поделиться информацией
          </button>
        </div>
      </div>
    </div>
  );

  // Create user function
  const handleCreateUser = async () => {
    try {
      // Validate form
      if (!createUserForm.username.trim()) {
        alert('Имя пользователя обязательно');
        return;
      }
      
      if (!createUserForm.email.trim()) {
        alert('Email обязательно');
        return;
      }
      
      if (createUserForm.password.length < 8) {
        alert('Пароль должен содержать минимум 8 символов');
        return;
      }
      
      if (createUserForm.password !== createUserForm.confirm_password) {
        alert('Пароли не совпадают');
        return;
      }
      
      if (createUserForm.status === 'BANNED' && !createUserForm.ban_reason.trim()) {
        alert('Причина блокировки обязательна при статусе "заблокирован"');
        return;
      }

      setCreateUserLoading(true);

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(createUserForm)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка создания пользователя');
      }

      const result = await response.json();
      
      // Show success notification
      if (window.addNotification) {
        window.addNotification('Пользователь успешно создан', 'success');
      } else {
        alert('Пользователь успешно создан');
      }

      // Reset form and close modal
      setCreateUserForm({
        username: '',
        email: '',
        password: '',
        confirm_password: '',
        role: 'USER',
        virtual_balance: 1000,
        daily_limit_max: 1000,
        gender: 'male',
        status: 'ACTIVE',
        ban_reason: ''
      });
      setIsCreateUserModalOpen(false);

      // Refresh users list
      await fetchUsers();

    } catch (error) {
      console.error('Error creating user:', error);
      let errorMessage = 'Ошибка создания пользователя';
      
      if (error.message.includes('Email already exists')) {
        errorMessage = 'Пользователь с таким email уже существует. Используйте другой email.';
      } else if (error.message.includes('Username already exists')) {
        errorMessage = 'Пользователь с таким именем уже существует. Используйте другое имя.';
      } else if (error.message.includes('Passwords do not match')) {
        errorMessage = 'Пароли не совпадают. Проверьте правильность ввода.';
      } else {
        errorMessage = `Ошибка создания пользователя: ${error.message}`;
      }
      
      if (window.addNotification) {
        window.addNotification(errorMessage, 'error');
      } else {
        alert(errorMessage);
      }
    } finally {
      setCreateUserLoading(false);
    }
  };

  const DeleteModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-surface-card border border-red-500 border-opacity-30 rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-rajdhani text-xl font-bold text-red-400">❌ Удаление пользователя</h3>
          <button
            onClick={() => setIsDeleteModalOpen(false)}
            className="text-gray-400 hover:text-white"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-4">
          <div className="bg-red-900 bg-opacity-20 border border-red-500 border-opacity-30 rounded-lg p-3 mb-4">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="text-red-400 text-sm font-rajdhani">Необратимое действие!</span>
            </div>
          </div>
          
          <p className="text-text-secondary">Пользователь: <span className="text-white font-bold">{selectedUser?.username}</span></p>
          <p className="text-text-secondary mb-4">Email: <span className="text-white">{selectedUser?.email}</span></p>
          
          {currentUser?.role !== 'SUPER_ADMIN' && (
            <div className="bg-yellow-900 bg-opacity-20 border border-yellow-500 border-opacity-30 rounded-lg p-3 mb-4">
              <span className="text-yellow-400 text-sm">Только SUPER_ADMIN может удалять аккаунты</span>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-text-secondary text-sm font-rajdhani mb-1">Причина удаления *</label>
            <textarea
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
              placeholder="Подробно опишите причину удаления аккаунта..."
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
              rows="3"
              required
              disabled={currentUser?.role !== 'SUPER_ADMIN'}
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              onClick={submitDelete}
              disabled={currentUser?.role !== 'SUPER_ADMIN'}
              className="flex-1 py-2 bg-red-600 text-white font-rajdhani font-bold rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Удалить навсегда
            </button>
            <button
              onClick={() => setIsDeleteModalOpen(false)}
              className="flex-1 py-2 bg-gray-600 text-white font-rajdhani font-bold rounded-lg hover:bg-gray-700 transition-colors"
            >
              Отмена
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Заголовок и статистика */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-russo text-2xl text-white">Управление Пользователями</h2>
          <p className="font-roboto text-text-secondary">
            Всего пользователей: {users.length} из многих
          </p>
        </div>
        <div className="flex space-x-3">
          {/* Add user button */}
          <button
            onClick={() => setIsCreateUserModalOpen(true)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-rajdhani font-bold transition-colors"
          >
            ➕ Добавить пользователя
          </button>
          
          {/* Unfreeze stuck commission button (SUPER_ADMIN only) */}
          <button
            onClick={() => setIsUnfreezeCommissionModalOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-rajdhani font-bold transition-colors"
          >
            🔓 Разморозить всю зависшую комиссию
          </button>
          
          {/* Reset all balances button (SUPER_ADMIN only) */}
          <button
            onClick={() => setIsResetBalancesModalOpen(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-rajdhani font-bold transition-colors"
          >
            💰 Обнулить балансы
          </button>
          
          <div className="flex space-x-2">
            {['', 'ONLINE', 'OFFLINE', 'BANNED', 'EMAIL_PENDING'].map((status) => (
              <button
                key={status}
                onClick={() => handleStatusFilter(status)}
                className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
                  statusFilter === status
                    ? 'bg-accent-primary text-white'
                    : 'bg-surface-card text-text-secondary hover:text-white'
                }`}
              >
                {status ? (status === 'ONLINE' ? 'Онлайн' : 
                          status === 'OFFLINE' ? 'Офлайн' : 
                          status === 'BANNED' ? 'Заблокированы' : 
                          status === 'EMAIL_PENDING' ? 'Ожидают подтв.' : status) : 'Все'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Поиск */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <svg className="absolute left-3 top-3 w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Поиск по имени или email..."
              value={searchTerm}
              onChange={handleSearch}
              className="w-full pl-10 pr-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
            />
          </div>
        </div>
        <button
          onClick={fetchUsers}
          className="px-6 py-3 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity"
        >
          Обновить
        </button>
      </div>

      {/* Расширенные фильтры */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Фильтр по роли */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-secondary">Роль</label>
            <select
              value={roleFilter}
              onChange={(e) => handleRoleFilter(e.target.value)}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="">Все роли</option>
              <option value="USER">Игрок</option>
              <option value="ADMIN">Админ</option>
              <option value="SUPER_ADMIN">Супер-админ</option>
              <option value="HUMAN_BOT">Human-бот</option>
              <option value="REGULAR_BOT">Обычный бот</option>
            </select>
          </div>

          {/* Фильтр по статусу */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-secondary">Статус</label>
            <select
              value={statusFilter}
              onChange={(e) => handleStatusFilter(e.target.value)}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="">Все статусы</option>
              <option value="ONLINE">Онлайн</option>
              <option value="OFFLINE">Офлайн</option>
              <option value="BANNED">Заблокирован</option>
              <option value="EMAIL_PENDING">Ожидает подтв.</option>
            </select>
          </div>

          {/* Кнопка очистки фильтров */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-secondary">Действия</label>
            <button
              onClick={clearFilters}
              className="w-full px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold transition-colors"
            >
              Очистить фильтры
            </button>
          </div>
        </div>

        {/* Фильтр по балансу */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-secondary">Минимальный баланс</label>
            <input
              type="number"
              placeholder="0"
              value={balanceMin}
              onChange={(e) => setBalanceMin(e.target.value)}
              onBlur={handleBalanceFilter}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-secondary">Максимальный баланс</label>
            <input
              type="number"
              placeholder="∞"
              value={balanceMax}
              onChange={(e) => setBalanceMax(e.target.value)}
              onBlur={handleBalanceFilter}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>
        </div>

        {/* Фильтр по TOTAL */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-secondary">Минимальный TOTAL</label>
            <input
              type="number"
              placeholder="0"
              value={totalMin}
              onChange={(e) => setTotalMin(e.target.value)}
              onBlur={handleTotalFilter}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-text-secondary">Максимальный TOTAL</label>
            <input
              type="number"
              placeholder="∞"
              value={totalMax}
              onChange={(e) => setTotalMax(e.target.value)}
              onBlur={handleTotalFilter}
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
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
                Выбрано пользователей: <span className="font-bold">{selectedUsers.size}</span>
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
                {bulkActionLoading ? 'Удаление...' : 'Удалить выбранных'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Таблица пользователей */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="text-white text-lg font-roboto">Загрузка пользователей...</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
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
                  <th 
                    onClick={() => handleColumnSort('name')}
                    className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider cursor-pointer hover:bg-surface-main transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>Пользователь</span>
                      <span className="text-accent-primary">{getSortIcon('name')}</span>
                    </div>
                  </th>
                  <th 
                    onClick={() => handleColumnSort('online_status')}
                    className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider cursor-pointer hover:bg-surface-main transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>Онлайн статус</span>
                      <span className="text-accent-primary">{getSortIcon('online_status')}</span>
                    </div>
                  </th>
                  <th 
                    onClick={() => handleColumnSort('role')}
                    className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider cursor-pointer hover:bg-surface-main transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>Роль</span>
                      <span className="text-accent-primary">{getSortIcon('role')}</span>
                    </div>
                  </th>
                  <th 
                    onClick={() => handleColumnSort('balance')}
                    className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider cursor-pointer hover:bg-surface-main transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>Баланс</span>
                      <span className="text-accent-primary">{getSortIcon('balance')}</span>
                    </div>
                  </th>
                  <th 
                    onClick={() => handleColumnSort('total')}
                    className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider cursor-pointer hover:bg-surface-main transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>TOTAL</span>
                      <span className="text-accent-primary">{getSortIcon('total')}</span>
                    </div>
                  </th>
                  <th 
                    onClick={() => handleColumnSort('gems')}
                    className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider cursor-pointer hover:bg-surface-main transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>Гемы</span>
                      <span className="text-accent-primary">{getSortIcon('gems')}</span>
                    </div>
                  </th>
                  <th 
                    onClick={() => handleColumnSort('bets')}
                    className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider cursor-pointer hover:bg-surface-main transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>Ставки</span>
                      <span className="text-accent-primary">{getSortIcon('bets')}</span>
                    </div>
                  </th>
                  <th 
                    onClick={() => handleColumnSort('games')}
                    className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider cursor-pointer hover:bg-surface-main transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>ИГРЫ</span>
                      <span className="text-accent-primary">{getSortIcon('games')}</span>
                    </div>
                  </th>
                  <th 
                    onClick={() => handleColumnSort('registration_date')}
                    className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider cursor-pointer hover:bg-surface-main transition-colors"
                  >
                    <div className="flex items-center space-x-1">
                      <span>Рег / Пос. визит</span>
                      <span className="text-accent-primary">{getSortIcon('registration_date')}</span>
                    </div>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-primary">
                {users.map((user) => {
                  const suspiciousFlags = getSuspiciousFlags(user);
                  const totalGames = user.total_games_played || 0;
                  const gamesWon = user.total_games_won || 0;
                  const gamesLost = (user.total_games_lost || (totalGames - gamesWon - (user.total_games_draw || 0)));
                  const gamesDraw = user.total_games_draw || 0;
                  
                  return (
                    <tr key={user.id} className="hover:bg-surface-sidebar transition-colors">
                      <td className="px-4 py-4 whitespace-nowrap text-center">
                        <input
                          type="checkbox"
                          checked={selectedUsers.has(user.id)}
                          onChange={() => handleUserSelect(user.id)}
                          className="rounded border-border-primary text-accent-primary focus:ring-accent-primary"
                        />
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            user.gender === 'female' ? 'bg-pink-600' : 'bg-blue-600'
                          }`}>
                            {user.gender === 'female' ? '👩' : '👨'}
                          </div>
                          <div className="ml-3">
                            <div className="font-rajdhani font-bold text-white">{user.username}</div>
                            <div className="font-roboto text-text-secondary text-sm">{user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        {getUserOnlineStatusBadge(user)}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        {getUserRoleBadge(user)}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="font-rajdhani font-bold text-accent-primary">
                          {formatDollarAmount(user.virtual_balance || 0)}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="font-rajdhani font-bold text-green-400">
                          {formatDollarAmount(user.total_balance || 0)}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="relative group">
                          <button
                            onClick={() => handleGemsModal(user)}
                            onMouseEnter={() => loadGemsTooltip(user.id)}
                            className="text-accent-primary hover:text-accent-secondary underline text-sm"
                            title="Посмотреть и управлять гемами"
                          >
                            {user.total_gems || 0} шт / ${(user.total_gems_value || 0).toFixed(2)}
                          </button>
                          {/* Tooltip */}
                          <div className="absolute bottom-full left-0 mb-2 w-48 bg-gray-900 border border-gray-600 rounded-lg p-2 text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity z-10">
                            <div className="font-bold mb-1">Разбивка по типам:</div>
                            <div>{gemsTooltips[user.id] || 'Загрузка...'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleBetsModal(user)}
                          className="text-blue-400 hover:text-blue-300 underline text-sm"
                          title="Посмотреть активные ставки"
                        >
                          {user.active_bets_count || 0} активные
                        </button>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm">
                          <span className="text-green-400">{gamesWon}</span>/
                          <span className="text-red-400">{gamesLost}</span>/
                          <span className="text-gray-400">{gamesDraw}</span>
                        </div>
                        <div className="text-text-secondary text-xs">
                          Пбд / Прж / Нчя
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="text-white font-roboto text-sm">
                          {formatDate(user.created_at)}
                        </div>
                        <div className="text-yellow-400 text-xs">
                          {formatDate(user.last_login || user.created_at)}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-1">
                          {/* Suspicious Activity Flag */}
                          <div className="relative group">
                            <button 
                              onClick={() => handleToggleSuspicious(user, 'Admin manual flag')}
                              className={`p-1 text-white rounded hover:opacity-80 ${
                                suspiciousFlags.length > 0 
                                  ? 'bg-red-600 hover:bg-red-700' 
                                  : 'bg-gray-600 hover:bg-gray-700 opacity-50'
                              }`}
                              title={suspiciousFlags.length > 0 ? "Снять флаг подозрительности" : "Отметить как подозрительного"}
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
                              </svg>
                            </button>
                            {suspiciousFlags.length > 0 && (
                              <div className="absolute bottom-full left-0 mb-2 w-48 bg-red-900 border border-red-500 rounded-lg p-2 text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                {suspiciousFlags.map((flag, idx) => (
                                  <div key={idx}>{flag.message}</div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Info Button */}
                          <button
                            onClick={() => handleInfoModal(user)}
                            className="p-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                            title="Информация о игроке"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </button>

                          {/* Edit Button */}
                          <button
                            onClick={() => handleEditUser(user)}
                            className="p-1 bg-green-600 text-white rounded hover:bg-green-700"
                            title="Редактировать"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          
                          {/* Ban/Unban Button */}
                          {user.status === 'BANNED' ? (
                            <button
                              onClick={() => handleUnbanUser(user.id)}
                              className="p-1 bg-green-600 text-white rounded hover:bg-green-700"
                              title="Разбанить"
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            </button>
                          ) : (
                            <button
                              onClick={() => handleBanUser(user)}
                              className="p-1 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                              title="Забанить"
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
                              </svg>
                            </button>
                          )}

                          {/* Reset User Bets Button */}
                          <button
                            onClick={() => resetUserBets(user)}
                            disabled={resettingUserBets === user.id}
                            className="p-1 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
                            title="Сбросить ставки пользователя"
                          >
                            {resettingUserBets === user.id ? (
                              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                            ) : (
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            )}
                          </button>

                          {/* Reset User Balance Button */}
                          <button
                            onClick={() => resetUserBalance(user)}
                            disabled={resettingUserBalance === user.id}
                            className="p-1 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                            title="Обнулить баланс пользователя"
                          >
                            {resettingUserBalance === user.id ? (
                              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                            ) : (
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                              </svg>
                            )}
                          </button>

                          {/* Delete Button */}
                          <button
                            onClick={() => handleDeleteUser(user)}
                            className="p-1 bg-red-600 text-white rounded hover:bg-red-700"
                            title="Удалить пользователя"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Пагинация */}
      <Pagination
        currentPage={pagination.currentPage}
        totalPages={pagination.totalPages}
        onPageChange={pagination.handlePageChange}
        itemsPerPage={pagination.itemsPerPage}
        totalItems={pagination.totalItems}
        className="mt-6"
      />

      {/* Модальные окна */}
      {isEditModalOpen && <EditUserModal />}
      {isBanModalOpen && <BanUserModal />}
      {isGemsModalOpen && <GemsModal />}
      {isBetsModalOpen && <BetsModal />}
      {isInfoModalOpen && <InfoModal />}
      {isDeleteModalOpen && <DeleteModal />}

      {/* Reset All Balances Modal */}
      {isResetBalancesModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-red-600 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-red-400">💰 Обнулить все балансы</h3>
              <button
                onClick={() => setIsResetBalancesModalOpen(false)}
                disabled={resettingBalances}
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
                  <div>• Все балансы станут равными нулю</div>
                  <div>• Все гемы будут сброшены</div>
                  <div>• Все игры будут отменены</div>
                  <div>• Будут затронуты ВСЕ игроки</div>
                </div>
              </div>

              <div className="text-center">
                <p className="text-white font-rajdhani text-lg mb-2">
                  Вы уверены, что хотите обнулить все балансы?
                </p>
                <p className="text-text-secondary text-sm">
                  Всем игрокам будут выданы стартовые значения
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setIsResetBalancesModalOpen(false)}
                  disabled={resettingBalances}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold transition-colors disabled:opacity-50"
                >
                  Отмена
                </button>
                <button
                  onClick={resetAllBalances}
                  disabled={resettingBalances}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-rajdhani font-bold transition-colors disabled:opacity-50 flex items-center justify-center"
                >
                  {resettingBalances ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Сбрасываем...
                    </>
                  ) : (
                    'Обнулить все балансы'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Unfreeze Stuck Commission Modal */}
      {isUnfreezeCommissionModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-blue-600 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-rajdhani text-xl font-bold text-blue-400">🔓 Разморозить зависшую комиссию</h3>
              <button
                onClick={() => setIsUnfreezeCommissionModalOpen(false)}
                disabled={unfreezingCommission}
                className="text-gray-400 hover:text-white disabled:opacity-50"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="bg-blue-900 border border-blue-600 rounded-lg p-4">
                <div className="text-blue-400 text-sm mb-2">
                  ℹ️ <strong>ИНФОРМАЦИЯ</strong>
                </div>
                <div className="text-blue-300 text-sm space-y-1">
                  <div>• Разморозка комиссии из незавершенных игр</div>
                  <div>• Переносится из frozen_balance в virtual_balance</div>
                  <div>• Затрагивает игры в статусах WAITING, ACTIVE, TIMEOUT</div>
                  <div>• Применяется ко всем пользователям (включая ботов)</div>
                </div>
              </div>

              <div className="text-center">
                <p className="text-white font-rajdhani text-lg mb-2">
                  Разморозить всю зависшую комиссию?
                </p>
                <p className="text-text-secondary text-sm">
                  Это безопасная операция - комиссии будут возвращены на балансы пользователей
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setIsUnfreezeCommissionModalOpen(false)}
                  disabled={unfreezingCommission}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-rajdhani font-bold transition-colors disabled:opacity-50"
                >
                  Отмена
                </button>
                <button
                  onClick={unfreezeStuckCommission}
                  disabled={unfreezingCommission}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-rajdhani font-bold transition-colors disabled:opacity-50 flex items-center justify-center"
                >
                  {unfreezingCommission ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Размораживаем...
                    </>
                  ) : (
                    'Разморозить комиссию'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {isCreateUserModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-russo text-xl text-white">Создать нового пользователя</h3>
              <button
                onClick={() => setIsCreateUserModalOpen(false)}
                className="text-text-secondary hover:text-white"
                disabled={createUserLoading}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              {/* Username and Email */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Имя пользователя *
                  </label>
                  <input
                    type="text"
                    value={createUserForm.username}
                    onChange={(e) => setCreateUserForm(prev => ({...prev, username: e.target.value}))}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    placeholder="user123"
                    disabled={createUserLoading}
                    pattern="[a-zA-Z0-9._+-]+"
                    title="Только латиница, цифры, точка, минус/плюс, подчеркивания, тире"
                  />
                  <p className="text-xs text-text-secondary mt-1">
                    Только латиница, цифры, точка, минус/плюс, подчеркивания, тире
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Email *
                  </label>
                  <input
                    type="email"
                    value={createUserForm.email}
                    onChange={(e) => setCreateUserForm(prev => ({...prev, email: e.target.value}))}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    placeholder="user@example.com"
                    disabled={createUserLoading}
                  />
                </div>
              </div>

              {/* Password fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Пароль *
                  </label>
                  <input
                    type="password"
                    value={createUserForm.password}
                    onChange={(e) => setCreateUserForm(prev => ({...prev, password: e.target.value}))}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    placeholder="Минимум 8 символов"
                    disabled={createUserLoading}
                    minLength="8"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Подтверждение пароля *
                  </label>
                  <input
                    type="password"
                    value={createUserForm.confirm_password}
                    onChange={(e) => setCreateUserForm(prev => ({...prev, confirm_password: e.target.value}))}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    placeholder="Повторите пароль"
                    disabled={createUserLoading}
                    minLength="8"
                  />
                </div>
              </div>

              {/* Role and Gender */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Роль
                  </label>
                  <select
                    value={createUserForm.role}
                    onChange={(e) => setCreateUserForm(prev => ({...prev, role: e.target.value}))}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    disabled={createUserLoading}
                  >
                    <option value="USER">USER</option>
                    <option value="ADMIN">ADMIN</option>
                    <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Пол
                  </label>
                  <select
                    value={createUserForm.gender}
                    onChange={(e) => setCreateUserForm(prev => ({...prev, gender: e.target.value}))}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    disabled={createUserLoading}
                  >
                    <option value="male">Мужчина</option>
                    <option value="female">Женщина</option>
                  </select>
                </div>
              </div>

              {/* Balance and Limit */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Начальный демо-баланс ($)
                  </label>
                  <input
                    type="number"
                    value={createUserForm.virtual_balance}
                    onChange={(e) => setCreateUserForm(prev => ({...prev, virtual_balance: Math.max(1, Math.min(10000, parseInt(e.target.value) || 1000))}))}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    min="1"
                    max="10000"
                    disabled={createUserLoading}
                  />
                  <p className="text-xs text-text-secondary mt-1">От 1 до 10000</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Дневной лимит пополнения ($)
                  </label>
                  <input
                    type="number"
                    value={createUserForm.daily_limit_max}
                    onChange={(e) => setCreateUserForm(prev => ({...prev, daily_limit_max: Math.max(1, Math.min(10000, parseInt(e.target.value) || 1000))}))}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    min="1"
                    max="10000"
                    disabled={createUserLoading}
                  />
                  <p className="text-xs text-text-secondary mt-1">От 1 до 10000</p>
                </div>
              </div>

              {/* Status and Ban Reason */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Статус
                  </label>
                  <select
                    value={createUserForm.status}
                    onChange={(e) => setCreateUserForm(prev => ({...prev, status: e.target.value}))}
                    className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    disabled={createUserLoading}
                  >
                    <option value="ACTIVE">Активный</option>
                    <option value="BANNED">Заблокирован</option>
                  </select>
                </div>
                
                {createUserForm.status === 'BANNED' && (
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">
                      Причина блокировки *
                    </label>
                    <textarea
                      value={createUserForm.ban_reason}
                      onChange={(e) => setCreateUserForm(prev => ({...prev, ban_reason: e.target.value}))}
                      className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary resize-none"
                      rows="3"
                      placeholder="Укажите причину блокировки..."
                      disabled={createUserLoading}
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="flex space-x-4 mt-6">
              <button
                onClick={handleCreateUser}
                disabled={createUserLoading}
                className="flex-1 py-2 bg-accent-primary text-white font-rajdhani font-bold rounded-lg hover:bg-opacity-80 transition-colors disabled:opacity-50"
              >
                {createUserLoading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Создание...
                  </>
                ) : (
                  'Создать пользователя'
                )}
              </button>
              <button
                onClick={() => setIsCreateUserModalOpen(false)}
                disabled={createUserLoading}
                className="flex-1 py-2 bg-gray-600 text-white font-rajdhani font-bold rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;