import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const API = process.env.REACT_APP_BACKEND_URL;

// Доступные разрешения с описаниями на русском
const PERMISSION_DESCRIPTIONS = {
  'VIEW_PROFILE': 'Просмотр профиля',
  'EDIT_PROFILE': 'Редактирование профиля',
  'CREATE_GAME': 'Создание игр',
  'JOIN_GAME': 'Присоединение к играм',
  'VIEW_GAMES': 'Просмотр игр',
  'VIEW_ADMIN_PANEL': 'Доступ к админ панели',
  'MANAGE_USERS': 'Управление пользователями',
  'MANAGE_GAMES': 'Управление играми',
  'MANAGE_BOTS': 'Управление ботами',
  'MANAGE_ECONOMY': 'Управление экономикой',
  'VIEW_ANALYTICS': 'Просмотр аналитики',
  'MANAGE_SOUNDS': 'Управление звуками',
  'MANAGE_ROLES': 'Управление ролями',
  'SYSTEM_SETTINGS': 'Системные настройки'
};

const ROLE_DESCRIPTIONS = {
  'USER': 'Обычный пользователь - базовые игровые права',
  'MODERATOR': 'Модератор - права на управление пользователями и играми',  
  'ADMIN': 'Администратор - полные права, кроме управления ролями',
  'SUPER_ADMIN': 'Супер администратор - все права включая управление ролями'
};

const RoleManagement = ({ user }) => {
  const [roles, setRoles] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingRole, setEditingRole] = useState(null);
  const [editingUser, setEditingUser] = useState(null);
  const [newRoleName, setNewRoleName] = useState('');
  const [newRoleDescription, setNewRoleDescription] = useState('');
  const [selectedPermissions, setSelectedPermissions] = useState([]);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditUserModalOpen, setIsEditUserModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('roles'); // 'roles' or 'users'
  
  // User edit form state
  const [userEditForm, setUserEditForm] = useState({
    username: '',
    email: '',
    role: 'USER',
    virtual_balance: 0,
    status: 'ACTIVE'
  });
  
  const { showSuccess, showError } = useNotifications();

  useEffect(() => {
    fetchRoles();
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/users?limit=100`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.users) {
        // Фильтруем только обычных пользователей (не ботов)
        const regularUsers = response.data.users.filter(u => 
          u.user_type !== 'HUMAN_BOT' && u.user_type !== 'REGULAR_BOT'
        );
        setUsers(regularUsers);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      showError('Ошибка загрузки пользователей');
    }
  };

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Получаем роли (временно используем информацию из системы)
      const systemRoles = [
        {
          name: 'USER',
          description: ROLE_DESCRIPTIONS.USER,
          permissions: ['VIEW_PROFILE', 'EDIT_PROFILE', 'CREATE_GAME', 'JOIN_GAME', 'VIEW_GAMES'],
          is_system_role: true,
          users_count: 0
        },
        {
          name: 'MODERATOR', 
          description: ROLE_DESCRIPTIONS.MODERATOR,
          permissions: ['VIEW_PROFILE', 'EDIT_PROFILE', 'CREATE_GAME', 'JOIN_GAME', 'VIEW_GAMES', 'VIEW_ADMIN_PANEL', 'MANAGE_USERS', 'MANAGE_GAMES'],
          is_system_role: true,
          users_count: 0
        },
        {
          name: 'ADMIN',
          description: ROLE_DESCRIPTIONS.ADMIN, 
          permissions: ['VIEW_PROFILE', 'EDIT_PROFILE', 'CREATE_GAME', 'JOIN_GAME', 'VIEW_GAMES', 'VIEW_ADMIN_PANEL', 'MANAGE_USERS', 'MANAGE_GAMES', 'MANAGE_BOTS', 'MANAGE_ECONOMY', 'VIEW_ANALYTICS', 'MANAGE_SOUNDS'],
          is_system_role: true,
          users_count: 0
        },
        {
          name: 'SUPER_ADMIN',
          description: ROLE_DESCRIPTIONS.SUPER_ADMIN,
          permissions: Object.keys(PERMISSION_DESCRIPTIONS),
          is_system_role: true,
          users_count: 0
        }
      ];

      // Пытаемся получить количество пользователей для каждой роли
      try {
        const usersResponse = await axios.get(`${API}/admin/users?limit=1000`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        const users = usersResponse.data.users || [];
        systemRoles.forEach(role => {
          role.users_count = users.filter(user => user.role === role.name).length;
        });
        
        console.log('✅ Роли загружены с подсчетом пользователей');
      } catch (userCountError) {
        console.warn('⚠️ Не удалось получить количество пользователей для ролей:', userCountError.response?.data?.detail || userCountError.message);
        // Продолжаем работать без подсчета пользователей
      }

      setRoles(systemRoles);
      console.log('✅ Роли успешно установлены:', systemRoles.length);
      
    } catch (error) {
      console.error('❌ Ошибка загрузки ролей:', error);
      
      // Более детальная обработка ошибок
      if (error.response?.status === 403) {
        showError('Недостаточно прав для просмотра ролей. Требуется роль SUPER_ADMIN.');
      } else if (error.response?.status === 401) {
        showError('Необходима авторизация. Пожалуйста, войдите в систему снова.');
      } else {
        showError(`Ошибка загрузки ролей: ${error.response?.data?.detail || error.message || 'Неизвестная ошибка'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePermissionToggle = (permission) => {
    setSelectedPermissions(prev => 
      prev.includes(permission) 
        ? prev.filter(p => p !== permission)
        : [...prev, permission]
    );
  };

  const handleEditRole = (role) => {
    setEditingRole(role);
    setNewRoleName(role.name);
    setNewRoleDescription(role.description);
    setSelectedPermissions([...role.permissions]);
  };

  const handleSaveRole = async () => {
    try {
      // В реальной системе здесь был бы запрос к API для сохранения роли
      showError('Редактирование системных ролей временно недоступно. Это функция для кастомных ролей.');
      setEditingRole(null);
    } catch (error) {
      console.error('Error saving role:', error);
      showError('Ошибка сохранения роли');
    }
  };

  const handleCreateRole = async () => {
    try {
      if (!newRoleName.trim()) {
        showError('Введите название роли');
        return;
      }

      // В реальной системе здесь был бы запрос к API
      showError('Создание новых ролей будет доступно в следующих версиях');
      setIsCreateModalOpen(false);
      setNewRoleName('');
      setNewRoleDescription('');
      setSelectedPermissions([]);
    } catch (error) {
      console.error('Error creating role:', error);
      showError('Ошибка создания роли');
    }
  };

  const handleEditUser = (userToEdit) => {
    setEditingUser(userToEdit);
    setUserEditForm({
      username: userToEdit.username || '',
      email: userToEdit.email || '',
      role: userToEdit.role || 'USER',
      virtual_balance: userToEdit.virtual_balance || 0,
      status: userToEdit.status || 'ACTIVE'
    });
    setIsEditUserModalOpen(true);
  };

  const handleSaveUser = async () => {
    try {
      if (!userEditForm.username.trim()) {
        showError('Введите имя пользователя');
        return;
      }

      if (!userEditForm.email.trim()) {
        showError('Введите email');
        return;
      }

      // Проверка прав доступа - только SUPER_ADMIN может назначать любые роли
      if (user?.role !== 'SUPER_ADMIN') {
        if (userEditForm.role === 'SUPER_ADMIN') {
          showError('Только SUPER_ADMIN может назначать роль SUPER_ADMIN');
          return;
        }
      }

      const token = localStorage.getItem('token');
      await axios.put(`${API}/admin/users/${editingUser.id}`, userEditForm, {
        headers: { Authorization: `Bearer ${token}` }
      });

      showSuccess('Пользователь успешно обновлен');
      setIsEditUserModalOpen(false);
      setEditingUser(null);
      fetchUsers(); // Обновляем список пользователей
    } catch (error) {
      console.error('Error updating user:', error);
      showError(error.response?.data?.detail || 'Ошибка обновления пользователя');
    }
  };

  const getUserRoleBadge = (userRole) => {
    const roleColors = {
      'USER': 'bg-blue-600',
      'MODERATOR': 'bg-green-600',
      'ADMIN': 'bg-purple-600',
      'SUPER_ADMIN': 'bg-red-600'
    };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold ${roleColors[userRole] || 'bg-gray-600'}`}>
        {userRole}
      </span>
    );
  };

  const getUserStatusBadge = (status) => {
    const statusColors = {
      'ACTIVE': 'bg-green-600',
      'BANNED': 'bg-red-600',
      'EMAIL_PENDING': 'bg-yellow-600'
    };
    
    const statusLabels = {
      'ACTIVE': 'Активен',
      'BANNED': 'Заблокирован',
      'EMAIL_PENDING': 'Ожидает подтв.'
    };
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full text-white font-rajdhani font-bold ${statusColors[status] || 'bg-gray-600'}`}>
        {statusLabels[status] || status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary"></div>
      </div>
    );
  }

  return (
    <div className="bg-surface-sidebar rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-white font-rajdhani">
          Управление Ролями и Разрешениями
        </h2>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="bg-accent-primary text-white px-4 py-2 rounded-lg font-rajdhani font-bold hover:bg-accent-primary/90 transition-colors"
        >
          + Создать Роль
        </button>
      </div>

      {/* Табы */}
      <div className="mb-6">
        <div className="border-b border-border-primary">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('roles')}
              className={`py-2 px-1 border-b-2 font-rajdhani font-medium text-sm ${
                activeTab === 'roles'
                  ? 'border-accent-primary text-accent-primary'
                  : 'border-transparent text-text-secondary hover:text-white hover:border-gray-300'
              }`}
            >
              Роли
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`py-2 px-1 border-b-2 font-rajdhani font-medium text-sm ${
                activeTab === 'users'
                  ? 'border-accent-primary text-accent-primary'
                  : 'border-transparent text-text-secondary hover:text-white hover:border-gray-300'
              }`}
            >
              Пользователи
            </button>
          </nav>
        </div>
      </div>

      {/* Содержимое табов */}
      {activeTab === 'roles' && (
        <div className="space-y-4">
          {roles.map((role) => (
            <div key={role.name} className="bg-surface-primary rounded-lg p-4 border border-border-primary">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-white font-rajdhani">
                      {role.name}
                    </h3>
                    {role.is_system_role && (
                      <span className="px-2 py-1 text-xs bg-blue-600 text-white rounded-full font-rajdhani">
                        Системная
                      </span>
                    )}
                  </div>
                  
                  <p className="text-text-secondary font-roboto text-sm mb-3">
                    {role.description}
                  </p>
                  
                  <div className="text-text-secondary font-roboto text-sm mb-2">
                    {role.users_count} пользователей
                  </div>
                  
                  <div className="flex flex-wrap gap-1">
                    {role.permissions.slice(0, 5).map((permission) => (
                      <span key={permission} className="px-2 py-1 bg-accent-primary/20 text-accent-primary text-xs rounded font-roboto">
                        {PERMISSION_DESCRIPTIONS[permission] || permission}
                      </span>
                    ))}
                    {role.permissions.length > 5 && (
                      <span className="px-2 py-1 bg-gray-600 text-white text-xs rounded font-roboto">
                        +{role.permissions.length - 5} еще
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEditRole(role)}
                    className="text-text-secondary hover:text-white font-roboto text-sm"
                  >
                    Редактировать
                  </button>
                  {!role.is_system_role && (
                    <button
                      onClick={() => {/* handleDeleteRole */}}
                      className="text-red-400 hover:text-red-300 font-roboto text-sm"
                    >
                      Удалить
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="text-text-secondary font-roboto text-sm mb-4">
            Всего пользователей: {users.length}
          </div>
          {users.map((userItem) => (
            <div key={userItem.id} className="bg-surface-primary rounded-lg p-4 border border-border-primary">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-white font-rajdhani">
                      {userItem.username}
                    </h3>
                    {getUserRoleBadge(userItem.role)}
                    {getUserStatusBadge(userItem.status)}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                    <div className="text-text-secondary">
                      <span className="text-white">Email:</span> {userItem.email}
                    </div>
                    <div className="text-text-secondary">
                      <span className="text-white">Баланс:</span> ${userItem.virtual_balance?.toFixed(2) || '0.00'}
                    </div>
                    <div className="text-text-secondary">
                      <span className="text-white">ID:</span> {userItem.id}
                    </div>
                    <div className="text-text-secondary">
                      <span className="text-white">Регистрация:</span> {new Date(userItem.created_at).toLocaleDateString('ru-RU')}
                    </div>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEditUser(userItem)}
                    className="text-text-secondary hover:text-white font-roboto text-sm bg-surface-sidebar px-3 py-1 rounded hover:bg-accent-primary/20 transition-colors"
                  >
                    Редактировать пользователя
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Модальное окно редактирования роли */}
      {editingRole && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-sidebar rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-white font-rajdhani mb-4">
              Редактирование роли: {editingRole.name}
            </h3>
            
            {editingRole.is_system_role && (
              <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3 mb-4">
                <p className="text-yellow-300 text-sm font-roboto">
                  ⚠️ Системные роли защищены от изменений. Просмотр только для ознакомления.
                </p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-text-secondary font-roboto text-sm mb-1">
                  Название роли
                </label>
                <input
                  type="text"
                  value={newRoleName}
                  onChange={(e) => setNewRoleName(e.target.value)}
                  disabled={editingRole.is_system_role}
                  className="w-full px-3 py-2 bg-surface-primary border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                />
              </div>

              <div>
                <label className="block text-text-secondary font-roboto text-sm mb-1">
                  Описание
                </label>
                <textarea
                  value={newRoleDescription}
                  onChange={(e) => setNewRoleDescription(e.target.value)}
                  disabled={editingRole.is_system_role}
                  className="w-full px-3 py-2 bg-surface-primary border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  rows="3"
                />
              </div>

              <div>
                <label className="block text-text-secondary font-roboto text-sm mb-3">
                  Разрешения
                </label>
                <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                  {Object.entries(PERMISSION_DESCRIPTIONS).map(([permission, description]) => (
                    <label key={permission} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={selectedPermissions.includes(permission)}
                        onChange={() => handlePermissionToggle(permission)}
                        disabled={editingRole.is_system_role}
                        className="text-accent-primary focus:ring-accent-primary border-border-primary rounded"
                      />
                      <span className="text-sm text-white font-roboto">
                        {description}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setEditingRole(null)}
                className="px-4 py-2 text-text-secondary hover:text-white font-roboto"
              >
                Отмена
              </button>
              {!editingRole.is_system_role && (
                <button
                  onClick={handleSaveRole}
                  className="bg-accent-primary text-white px-4 py-2 rounded-lg font-rajdhani font-bold hover:bg-accent-primary/90"
                >
                  Сохранить
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно создания роли */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-sidebar rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-white font-rajdhani mb-4">
              Создание новой роли
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-text-secondary font-roboto text-sm mb-1">
                  Название роли
                </label>
                <input
                  type="text"
                  value={newRoleName}
                  onChange={(e) => setNewRoleName(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-primary border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  placeholder="Введите название роли"
                />
              </div>

              <div>
                <label className="block text-text-secondary font-roboto text-sm mb-1">
                  Описание
                </label>
                <textarea
                  value={newRoleDescription}
                  onChange={(e) => setNewRoleDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-primary border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  placeholder="Описание роли"
                  rows="3"
                />
              </div>

              <div>
                <label className="block text-text-secondary font-roboto text-sm mb-3">
                  Выберите разрешения
                </label>
                <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                  {Object.entries(PERMISSION_DESCRIPTIONS).map(([permission, description]) => (
                    <label key={permission} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={selectedPermissions.includes(permission)}
                        onChange={() => handlePermissionToggle(permission)}
                        className="text-accent-primary focus:ring-accent-primary border-border-primary rounded"
                      />
                      <span className="text-sm text-white font-roboto">
                        {description}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setIsCreateModalOpen(false);
                  setNewRoleName('');
                  setNewRoleDescription('');
                  setSelectedPermissions([]);
                }}
                className="px-4 py-2 text-text-secondary hover:text-white font-roboto"
              >
                Отмена
              </button>
              <button
                onClick={handleCreateRole}
                className="bg-accent-primary text-white px-4 py-2 rounded-lg font-rajdhani font-bold hover:bg-accent-primary/90"
              >
                Создать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RoleManagement;