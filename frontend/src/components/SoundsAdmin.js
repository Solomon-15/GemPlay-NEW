import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import useConfirmation from '../hooks/useConfirmation';
import ConfirmationModal from './ConfirmationModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SoundsAdmin = ({ user }) => {
  const [sounds, setSounds] = useState([]);
  const [categories, setCategories] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeModal, setActiveModal] = useState(null);
  const [editingSound, setEditingSound] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Form state for creating/editing sounds
  const [formData, setFormData] = useState({
    name: '',
    category: 'GAMING',
    event_trigger: '',
    game_type: 'ALL',
    is_enabled: true,
    priority: 5,
    volume: 0.5,
    delay: 0,
    can_repeat: true
  });

  const { showSuccessRU, showErrorRU } = useNotifications();
  const { confirm, confirmationModal } = useConfirmation();

  useEffect(() => {
    loadSounds();
    loadCategories();
    loadEvents();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const loadSounds = async () => {
    try {
      const response = await axios.get(`${API}/admin/sounds`, {
        headers: getAuthHeaders()
      });
      setSounds(response.data);
    } catch (error) {
      console.error('Error loading sounds:', error);
      showErrorRU('Ошибка загрузки звуков');
    }
  };

  const loadCategories = async () => {
    try {
      const response = await axios.get(`${API}/admin/sounds/categories`, {
        headers: getAuthHeaders()
      });
      setCategories(response.data);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const loadEvents = async () => {
    try {
      const response = await axios.get(`${API}/admin/sounds/events`, {
        headers: getAuthHeaders()
      });
      setEvents(response.data);
    } catch (error) {
      console.error('Error loading events:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSound = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/admin/sounds`, formData, {
        headers: getAuthHeaders()
      });
      setSounds([...sounds, response.data]);
      setActiveModal(null);
      resetForm();
      showSuccessRU('Звук создан успешно');
    } catch (error) {
      console.error('Error creating sound:', error);
      showErrorRU('Ошибка создания звука');
    }
  };

  const handleUpdateSound = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.put(`${API}/admin/sounds/${editingSound.id}`, formData, {
        headers: getAuthHeaders()
      });
      setSounds(sounds.map(s => s.id === editingSound.id ? response.data : s));
      setActiveModal(null);
      setEditingSound(null);
      resetForm();
      showSuccessRU('Звук обновлён успешно');
    } catch (error) {
      console.error('Error updating sound:', error);
      showErrorRU('Ошибка обновления звука');
    }
  };

  const handleDeleteSound = async (soundId) => {
    const sound = sounds.find(s => s.id === soundId);
    const soundName = sound ? sound.name : 'звук';
    
    const confirmed = await confirm({
      title: 'Удаление звука',
      message: `Вы уверены, что хотите удалить звук "${soundName}"?`,
      confirmText: 'Удалить',
      cancelText: 'Отмена',
      type: 'danger'
    });

    if (!confirmed) {
      return;
    }
    
    try {
      await axios.delete(`${API}/admin/sounds/${soundId}`, {
        headers: getAuthHeaders()
      });
      setSounds(sounds.filter(s => s.id !== soundId));
      showSuccessRU('Звук удалён успешно');
    } catch (error) {
      console.error('Error deleting sound:', error);
      const message = error.response?.data?.detail || 'Ошибка удаления звука';
      showErrorRU(message);
    }
  };

  const handleFileUpload = async (soundId, fileInput) => {
    const file = fileInput.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/ogg'];
    if (!allowedTypes.includes(file.type)) {
      showErrorRU('Поддерживаются только MP3, WAV и OGG файлы');
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5242880) {
      showErrorRU('Размер файла не должен превышать 5MB');
      return;
    }

    setUploading(true);
    try {
      // Convert file to base64
      const base64 = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.readAsDataURL(file);
      });

      const uploadData = {
        file_data: base64,
        file_format: file.name.split('.').pop().toLowerCase(),
        file_size: file.size
      };

      const response = await axios.post(`${API}/admin/sounds/${soundId}/upload`, uploadData, {
        headers: getAuthHeaders()
      });

      setSounds(sounds.map(s => s.id === soundId ? response.data : s));
      showSuccessRU('Файл загружен успешно');
    } catch (error) {
      console.error('Error uploading file:', error);
      showErrorRU('Ошибка загрузки файла');
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      category: 'GAMING',
      event_trigger: '',
      game_type: 'ALL',
      is_enabled: true,
      priority: 5,
      volume: 0.5,
      delay: 0,
      can_repeat: true
    });
  };

  const openEditModal = (sound) => {
    setEditingSound(sound);
    setFormData({
      name: sound.name,
      category: sound.category,
      event_trigger: sound.event_trigger,
      game_type: sound.game_type,
      is_enabled: sound.is_enabled,
      priority: sound.priority,
      volume: sound.volume,
      delay: sound.delay,
      can_repeat: sound.can_repeat
    });
    setActiveModal('edit');
  };

  const filteredSounds = sounds.filter(sound => {
    const matchesCategory = categoryFilter === 'ALL' || sound.category === categoryFilter;
    const matchesSearch = sound.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         sound.event_trigger.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'GAMING':
        return '🎮';
      case 'UI':
        return '🖱️';
      case 'SYSTEM':
        return '⚙️';
      case 'BACKGROUND':
        return '🎵';
      default:
        return '🔊';
    }
  };

  const getPriorityBadge = (priority) => {
    if (priority >= 9) return { text: 'КРИТИЧЕСКИЙ', class: 'bg-red-500' };
    if (priority >= 6) return { text: 'ВЫСОКИЙ', class: 'bg-orange-500' };
    if (priority >= 3) return { text: 'СРЕДНИЙ', class: 'bg-yellow-500' };
    return { text: 'НИЗКИЙ', class: 'bg-gray-500' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-white text-xl font-rajdhani">Загрузка звуков...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-russo text-3xl text-white mb-2">Управление звуками</h1>
          <p className="font-roboto text-text-secondary">Настройка звуковых эффектов для игры</p>
        </div>
        <button
          onClick={() => setActiveModal('create')}
          className="px-6 py-3 bg-accent-primary text-white font-rajdhani font-bold rounded-lg hover:bg-green-600 transition-colors"
        >
          + Создать звук
        </button>
      </div>

      {/* Filters */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block font-roboto text-text-secondary mb-2">Категория</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:border-accent-primary"
            >
              <option value="ALL">Все категории</option>
              {categories.map(category => (
                <option key={category} value={category}>
                  {getCategoryIcon(category)} {category}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block font-roboto text-text-secondary mb-2">Поиск</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Поиск по названию или событию..."
              className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:border-accent-primary"
            />
          </div>
        </div>
      </div>

      {/* Sounds Table */}
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-sidebar">
              <tr>
                <th className="px-6 py-4 text-left font-rajdhani font-bold text-accent-primary">Название</th>
                <th className="px-6 py-4 text-left font-rajdhani font-bold text-accent-primary">Категория</th>
                <th className="px-6 py-4 text-left font-rajdhani font-bold text-accent-primary">Событие</th>
                <th className="px-6 py-4 text-left font-rajdhani font-bold text-accent-primary">Тип игры</th>
                <th className="px-6 py-4 text-left font-rajdhani font-bold text-accent-primary">Приоритет</th>
                <th className="px-6 py-4 text-left font-rajdhani font-bold text-accent-primary">Статус</th>
                <th className="px-6 py-4 text-left font-rajdhani font-bold text-accent-primary">Файл</th>
                <th className="px-6 py-4 text-center font-rajdhani font-bold text-accent-primary">Действия</th>
              </tr>
            </thead>
            <tbody>
              {filteredSounds.map((sound, index) => {
                const priorityBadge = getPriorityBadge(sound.priority);
                return (
                  <tr key={sound.id} className={index % 2 === 0 ? 'bg-surface-card' : 'bg-surface-sidebar bg-opacity-30'}>
                    <td className="px-6 py-4">
                      <div className="font-rajdhani font-medium text-white">{sound.name}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="flex items-center space-x-2 text-text-secondary">
                        <span>{getCategoryIcon(sound.category)}</span>
                        <span>{sound.category}</span>
                      </span>
                    </td>
                    <td className="px-6 py-4 font-roboto text-text-secondary">{sound.event_trigger}</td>
                    <td className="px-6 py-4 font-roboto text-text-secondary">{sound.game_type}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-white text-xs font-bold ${priorityBadge.class}`}>
                        {priorityBadge.text} ({sound.priority})
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        sound.is_enabled 
                          ? 'bg-green-500 text-white' 
                          : 'bg-red-500 text-white'
                      }`}>
                        {sound.is_enabled ? 'Включен' : 'Выключен'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {sound.has_audio_file ? (
                          <span className="text-green-400 text-sm">
                            📄 {sound.file_format?.toUpperCase()}
                          </span>
                        ) : (
                          <span className="text-gray-500 text-sm">🔇 Программный</span>
                        )}
                        <label className="cursor-pointer">
                          <input
                            type="file"
                            accept=".mp3,.wav,.ogg"
                            className="hidden"
                            onChange={(e) => handleFileUpload(sound.id, e.target)}
                            disabled={uploading}
                          />
                          <span className="text-blue-400 hover:text-blue-300 text-sm">
                            {uploading ? '⏳' : '📁'}
                          </span>
                        </label>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-center space-x-2">
                        <button
                          onClick={() => openEditModal(sound)}
                          className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm"
                        >
                          ✏️
                        </button>
                        {!sound.is_default && (
                          <button
                            onClick={() => handleDeleteSound(sound.id)}
                            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors text-sm"
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {filteredSounds.length === 0 && (
          <div className="text-center py-20">
            <div className="text-text-secondary text-xl font-rajdhani">Звуки не найдены</div>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {activeModal === 'create' || activeModal === 'edit' && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-surface-card border border-accent-primary rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto">
            <div className="p-6">
              <h2 className="font-russo text-2xl text-white mb-6">
                {activeModal === 'create' ? 'Создать звук' : 'Редактировать звук'}
              </h2>
              
              <form onSubmit={activeModal === 'create' ? handleCreateSound : handleUpdateSound} className="space-y-4">
                <div>
                  <label className="block font-roboto text-text-secondary mb-2">Название звука</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:border-accent-primary"
                    required
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-roboto text-text-secondary mb-2">Категория</label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({...formData, category: e.target.value})}
                      className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:border-accent-primary"
                    >
                      {categories.map(category => (
                        <option key={category} value={category}>{category}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block font-roboto text-text-secondary mb-2">Событие</label>
                    <select
                      value={formData.event_trigger}
                      onChange={(e) => setFormData({...formData, event_trigger: e.target.value})}
                      className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:border-accent-primary"
                    >
                      <option value="">Выберите событие</option>
                      {events.map(event => (
                        <option key={event} value={event}>{event}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-roboto text-text-secondary mb-2">Тип игры</label>
                    <select
                      value={formData.game_type}
                      onChange={(e) => setFormData({...formData, game_type: e.target.value})}
                      className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:border-accent-primary"
                    >
                      <option value="ALL">Все игры</option>
                      <option value="HUMAN_VS_HUMAN">Человек vs Человек</option>
                      <option value="HUMAN_VS_BOT">Человек vs Бот</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block font-roboto text-text-secondary mb-2">Приоритет (1-10)</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={formData.priority}
                      onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value)})}
                      className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-roboto text-text-secondary mb-2">Громкость (0.0-1.0)</label>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.1"
                      value={formData.volume}
                      onChange={(e) => setFormData({...formData, volume: parseFloat(e.target.value)})}
                      className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                  
                  <div>
                    <label className="block font-roboto text-text-secondary mb-2">Задержка (мс)</label>
                    <input
                      type="number"
                      min="0"
                      max="5000"
                      value={formData.delay}
                      onChange={(e) => setFormData({...formData, delay: parseInt(e.target.value)})}
                      className="w-full px-4 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:border-accent-primary"
                    />
                  </div>
                </div>
                
                <div className="flex items-center space-x-6">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.is_enabled}
                      onChange={(e) => setFormData({...formData, is_enabled: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="font-roboto text-text-secondary">Включен</span>
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.can_repeat}
                      onChange={(e) => setFormData({...formData, can_repeat: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="font-roboto text-text-secondary">Может повторяться</span>
                  </label>
                </div>
                
                <div className="flex justify-end space-x-4 mt-8">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveModal(null);
                      setEditingSound(null);
                      resetForm();
                    }}
                    className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-green-600 transition-colors"
                  >
                    {activeModal === 'create' ? 'Создать' : 'Сохранить'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
      
      {/* Confirmation Modal */}
      <ConfirmationModal {...confirmationModal} />
    </div>
  );
};

export default SoundsAdmin;