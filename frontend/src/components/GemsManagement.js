import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GemsManagement = () => {
  const { showSuccess, showError } = useNotifications();
  
  // States
  const [gems, setGems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingGem, setEditingGem] = useState(null);
  const [saving, setSaving] = useState(false);

  // Form data
  const [formData, setFormData] = useState({
    name: '',
    price: 1,
    color: '#FF0000',
    icon: '',
    rarity: 'Common'
  });

  useEffect(() => {
    fetchGems();
  }, []);

  const fetchGems = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/admin/gems`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGems(response.data);
    } catch (error) {
      console.error('Error fetching gems:', error);
      showError('Ошибка загрузки гемов');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Check file size (1MB limit)
    if (file.size > 1024 * 1024) {
      showError('Размер файла не должен превышать 1MB');
      return;
    }

    // Check file type
    if (!['image/png', 'image/jpg', 'image/jpeg', 'image/svg+xml'].includes(file.type)) {
      showError('Поддерживаются только PNG, JPG и SVG файлы');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setFormData({ ...formData, icon: e.target.result });
    };
    reader.readAsDataURL(file);
  };

  const handleCreateGem = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      await axios.post(`${API}/admin/gems`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      showSuccess('Гем успешно создан');
      setShowCreateModal(false);
      resetForm();
      fetchGems();
    } catch (error) {
      console.error('Error creating gem:', error);
      showError(error.response?.data?.detail || 'Ошибка создания гема');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateGem = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const updateData = { ...formData };
      // Don't send icon if it hasn't changed
      if (updateData.icon === editingGem.icon) {
        delete updateData.icon;
      }
      await axios.put(`${API}/admin/gems/${editingGem.id}`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      showSuccess('Гем успешно обновлен');
      setShowEditModal(false);
      setEditingGem(null);
      resetForm();
      fetchGems();
    } catch (error) {
      console.error('Error updating gem:', error);
      showError(error.response?.data?.detail || 'Ошибка обновления гема');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteGem = async (gem) => {
    if (gem.is_default) {
      showError('Нельзя удалить базовые гемы');
      return;
    }

    if (!window.confirm(`Вы уверены, что хотите удалить гем "${gem.name}"?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/admin/gems/${gem.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      showSuccess('Гем успешно удален');
      fetchGems();
    } catch (error) {
      console.error('Error deleting gem:', error);
      showError(error.response?.data?.detail || 'Ошибка удаления гема');
    }
  };

  const openEditModal = (gem) => {
    setEditingGem(gem);
    setFormData({
      name: gem.name,
      price: gem.price,
      color: gem.color,
      icon: gem.icon,
      rarity: gem.rarity
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      price: 1,
      color: '#FF0000',
      icon: '',
      rarity: 'Common'
    });
  };

  const closeModals = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setEditingGem(null);
    resetForm();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-white text-xl font-roboto">Загрузка гемов...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="font-russo text-2xl text-white">Управление гемами</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-opacity-80 transition-colors font-rajdhani font-bold"
        >
          Создать гем
        </button>
      </div>

      {/* Gems Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {gems.map((gem) => (
          <div
            key={gem.id}
            className="rounded-xl p-6 transition-all duration-300 hover:scale-105 group"
            style={{
              backgroundColor: '#081730',
              border: `1px solid ${gem.color}`,
              boxShadow: `0 0 20px ${gem.color}40`
            }}
          >
            {/* Gem Icon */}
            <div className="flex justify-center mb-4">
              <div className="w-24 h-24 flex items-center justify-center relative">
                <div 
                  className="absolute inset-0 animate-pulse"
                  style={{
                    background: `radial-gradient(circle, ${gem.color}40, transparent 70%)`,
                    filter: 'blur(8px)',
                    transform: 'scale(1.2)'
                  }}
                ></div>
                
                <img
                  src={gem.icon}
                  alt={gem.name}
                  className="w-20 h-20 object-contain drop-shadow-lg relative z-10"
                  style={{
                    filter: `drop-shadow(0 0 10px ${gem.color}40)`
                  }}
                />
              </div>
            </div>
            
            {/* Gem Info */}
            <div className="text-center">
              <h3 className="font-russo text-xl text-white mb-2">
                {gem.name}
              </h3>
              
              <p className="font-roboto text-text-secondary text-sm mb-3">
                {gem.rarity}
              </p>
              
              {/* Price */}
              <div className="mb-4">
                <span className="font-rajdhani text-2xl font-bold text-green-400">
                  ${gem.price}
                </span>
                <span className="font-roboto text-text-secondary text-sm"> each</span>
              </div>
              
              {/* Default Badge */}
              {gem.is_default && (
                <div className="mb-4">
                  <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded-full font-roboto">
                    Базовый
                  </span>
                </div>
              )}
              
              {/* Action Buttons */}
              <div className="flex space-x-2 justify-center">
                <button
                  onClick={() => openEditModal(gem)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-rajdhani"
                >
                  Редактировать
                </button>
                {!gem.is_default && (
                  <button
                    onClick={() => handleDeleteGem(gem)}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-rajdhani"
                  >
                    Удалить
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-russo text-white mb-6">Создать новый гем</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-white font-rajdhani mb-2">Название</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                  placeholder="Введите название гема"
                />
              </div>
              
              <div>
                <label className="block text-white font-rajdhani mb-2">Цена ($)</label>
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: parseInt(e.target.value) || 1 })}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                />
              </div>
              
              <div>
                <label className="block text-white font-rajdhani mb-2">Цвет (HEX)</label>
                <input
                  type="text"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                  placeholder="#FF0000"
                />
              </div>
              
              <div>
                <label className="block text-white font-rajdhani mb-2">Редкость</label>
                <select
                  value={formData.rarity}
                  onChange={(e) => setFormData({ ...formData, rarity: e.target.value })}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                >
                  <option value="Common">Common</option>
                  <option value="Uncommon">Uncommon</option>
                  <option value="Rare">Rare</option>
                  <option value="Epic">Epic</option>
                  <option value="Legendary">Legendary</option>
                  <option value="Mythic">Mythic</option>
                </select>
              </div>
              
              <div>
                <label className="block text-white font-rajdhani mb-2">Иконка</label>
                <input
                  type="file"
                  accept="image/png,image/jpg,image/jpeg,image/svg+xml"
                  onChange={handleFileUpload}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                />
                {formData.icon && (
                  <img src={formData.icon} alt="Preview" className="w-16 h-16 mt-2 object-contain" />
                )}
              </div>
            </div>
            
            <div className="flex space-x-4 mt-6">
              <button
                onClick={handleCreateGem}
                disabled={saving || !formData.name || !formData.icon}
                className="flex-1 py-2 bg-accent-primary text-white rounded-lg hover:bg-opacity-80 transition-colors font-rajdhani font-bold disabled:opacity-50"
              >
                {saving ? 'Создание...' : 'Создать'}
              </button>
              <button
                onClick={closeModals}
                className="flex-1 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-rajdhani font-bold"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingGem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-russo text-white mb-6">Редактировать гем</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-white font-rajdhani mb-2">Название</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                />
              </div>
              
              <div>
                <label className="block text-white font-rajdhani mb-2">Цена ($)</label>
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: parseInt(e.target.value) || 1 })}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                />
              </div>
              
              <div>
                <label className="block text-white font-rajdhani mb-2">Цвет (HEX)</label>
                <input
                  type="text"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                />
              </div>
              
              <div>
                <label className="block text-white font-rajdhani mb-2">Редкость</label>
                <select
                  value={formData.rarity}
                  onChange={(e) => setFormData({ ...formData, rarity: e.target.value })}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                >
                  <option value="Common">Common</option>
                  <option value="Uncommon">Uncommon</option>
                  <option value="Rare">Rare</option>
                  <option value="Epic">Epic</option>
                  <option value="Legendary">Legendary</option>
                  <option value="Mythic">Mythic</option>
                </select>
              </div>
              
              <div>
                <label className="block text-white font-rajdhani mb-2">Иконка</label>
                <input
                  type="file"
                  accept="image/png,image/jpg,image/jpeg,image/svg+xml"
                  onChange={handleFileUpload}
                  className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                />
                {formData.icon && (
                  <img src={formData.icon} alt="Preview" className="w-16 h-16 mt-2 object-contain" />
                )}
              </div>
            </div>
            
            <div className="flex space-x-4 mt-6">
              <button
                onClick={handleUpdateGem}
                disabled={saving || !formData.name}
                className="flex-1 py-2 bg-accent-primary text-white rounded-lg hover:bg-opacity-80 transition-colors font-rajdhani font-bold disabled:opacity-50"
              >
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
              <button
                onClick={closeModals}
                className="flex-1 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-rajdhani font-bold"
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

export default GemsManagement;