import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserManagement = () => {
  const { showSuccessRU, showErrorRU, showWarningRU } = useNotifications();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isBanModalOpen, setIsBanModalOpen] = useState(false);
  const [banReason, setBanReason] = useState('');
  const [banDuration, setBanDuration] = useState('');

  useEffect(() => {
    fetchUsers();
  }, [currentPage, searchTerm, statusFilter]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: '20'
      });
      
      if (searchTerm) params.append('search', searchTerm);
      if (statusFilter) params.append('status', statusFilter);
      
      const response = await axios.get(`${API}/admin/users?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setUsers(response.data.users || []);
      setTotalPages(response.data.pages || 1);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки пользователей:', error);
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1); // Сброс на первую страницу при поиске
  };

  const handleStatusFilter = (status) => {
    setStatusFilter(status);
    setCurrentPage(1);
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setIsEditModalOpen(true);
  };

  const handleBanUser = (user) => {
    setSelectedUser(user);
    setBanReason('');
    setBanDuration('');
    setIsBanModalOpen(true);
  };

  const handleUnbanUser = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/users/${userId}/unban`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchUsers(); // Обновляем список
      showSuccessRU('Пользователь разбанен');
    } catch (error) {
      console.error('Ошибка разбана:', error);
      showErrorRU('Ошибка при разбане пользователя');
    }
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

  const updateUserBalance = async (userId, newBalance) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/users/${userId}/balance`, {
        balance: parseFloat(newBalance)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchUsers();
      showSuccessRU('Баланс обновлен');
    } catch (error) {
      console.error('Ошибка обновления баланса:', error);
      showErrorRU('Ошибка при обновлении баланса');
    }
  };

  const getUserStatusBadge = (status) => {
    const badges = {
      'ACTIVE': 'bg-green-500 text-white',
      'BANNED': 'bg-red-500 text-white',
      'EMAIL_PENDING': 'bg-yellow-500 text-white'
    };
    
    const statusText = {
      'ACTIVE': 'Активен',
      'BANNED': 'Забанен',
      'EMAIL_PENDING': 'Ожидает подтверждения'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-rajdhani font-bold ${badges[status] || 'bg-gray-500 text-white'}`}>
        {statusText[status] || status}
      </span>
    );
  };

  const getUserRoleBadge = (role) => {
    const badges = {
      'USER': 'bg-blue-500 text-white',
      'ADMIN': 'bg-purple-500 text-white',
      'SUPER_ADMIN': 'bg-red-600 text-white'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-rajdhani font-bold ${badges[role] || 'bg-gray-500 text-white'}`}>
        {role}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Не указано';
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const EditUserModal = () => {
    const [editForm, setEditForm] = useState({
      username: selectedUser?.username || '',
      email: selectedUser?.email || '',
      role: selectedUser?.role || 'USER',
      virtual_balance: selectedUser?.virtual_balance || 0
    });

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

    return (
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
  };

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
        <div className="flex space-x-2">
          {['', 'ACTIVE', 'BANNED', 'EMAIL_PENDING'].map((status) => (
            <button
              key={status}
              onClick={() => handleStatusFilter(status)}
              className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
                statusFilter === status
                  ? 'bg-accent-primary text-white'
                  : 'bg-surface-card text-text-secondary hover:text-white'
              }`}
            >
              {status || 'Все'}
            </button>
          ))}
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
                  <th className="px-6 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Пользователь
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Статус
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Роль
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Баланс
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Игры
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Регистрация
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-rajdhani font-bold text-text-secondary uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-primary">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-surface-sidebar transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
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
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getUserStatusBadge(user.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getUserRoleBadge(user.role)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-rajdhani font-bold text-accent-primary">
                        ${user.virtual_balance?.toFixed(2) || '0.00'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-white font-roboto">
                        {user.total_games_played || 0} / {user.total_games_won || 0}
                      </div>
                      <div className="text-text-secondary text-sm">
                        всего / выигрыши
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-white font-roboto text-sm">
                        {formatDate(user.created_at)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleEditUser(user)}
                          className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                          title="Редактировать"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        
                        {user.status === 'BANNED' ? (
                          <button
                            onClick={() => handleUnbanUser(user.id)}
                            className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                            title="Разбанить"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </button>
                        ) : (
                          <button
                            onClick={() => handleBanUser(user)}
                            className="p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                            title="Забанить"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Пагинация */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white disabled:opacity-50"
          >
            Назад
          </button>
          <span className="font-roboto text-text-secondary">
            Страница {currentPage} из {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="px-4 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white disabled:opacity-50"
          >
            Вперед
          </button>
        </div>
      )}

      {/* Модальные окна */}
      {isEditModalOpen && <EditUserModal />}
      {isBanModalOpen && <BanUserModal />}
    </div>
  );
};

export default UserManagement;