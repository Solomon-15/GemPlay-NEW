import React, { useState, useEffect } from 'react';
import soundManager from '../utils/SoundManager';

const SoundSettings = ({ isOpen, onClose }) => {
  const [volume, setVolume] = useState(soundManager.volume);
  const [enabled, setEnabled] = useState(soundManager.enabled);
  const [reloading, setReloading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setVolume(soundManager.volume);
      setEnabled(soundManager.enabled);
    }
  }, [isOpen]);

  // Преобразование volume в уровни для совместимости
  const getVolumeLevel = (vol) => {
    if (!enabled || vol === 0) return 'off';
    if (vol <= 0.3) return 'quiet';
    if (vol <= 0.7) return 'normal';
    return 'loud';
  };

  const getVolumeFromLevel = (level) => {
    switch (level) {
      case 'off': return 0;
      case 'quiet': return 0.3;
      case 'normal': return 0.5;
      case 'loud': return 1.0;
      default: return 0.3;
    }
  };

  const handleVolumeChange = (level) => {
    const newVolume = getVolumeFromLevel(level);
    const newEnabled = level !== 'off';
    
    soundManager.updateSettings(newEnabled, newVolume);
    setVolume(newVolume);
    setEnabled(newEnabled);
    
    // Проигрываем тестовый звук
    if (newEnabled) {
      setTimeout(() => soundManager.playSound('создание_ставки'), 100);
    }
  };

  const testSound = async (eventTrigger) => {
    if (enabled) {
      await soundManager.playSound(eventTrigger);
    }
  };

  const handleReloadSounds = async () => {
    setReloading(true);
    try {
      await soundManager.reloadSounds();
      console.log('Sounds reloaded successfully');
    } catch (error) {
      console.error('Error reloading sounds:', error);
    } finally {
      setReloading(false);
    }
  };

  if (!isOpen) return null;

  const currentLevel = getVolumeLevel(volume);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-russo text-xl text-white">🔊 Настройки звука</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-6">
          {/* Уровни громкости */}
          <div>
            <h4 className="text-white font-semibold mb-3">Громкость звука</h4>
            <div className="space-y-2">
              {[
                { value: 'off', label: '🔇 Отключено', description: 'Без звука' },
                { value: 'quiet', label: '🔈 Тихо', description: 'Для концентрации' },
                { value: 'normal', label: '🔉 Обычно', description: 'Рекомендуемый уровень' },
                { value: 'loud', label: '🔊 Громко', description: 'Максимальное погружение' }
              ].map((level) => (
                <label key={level.value} className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="volumeLevel"
                    value={level.value}
                    checked={currentLevel === level.value}
                    onChange={() => handleVolumeChange(level.value)}
                    className="w-4 h-4 text-accent-primary"
                  />
                  <div className="flex-1">
                    <div className="text-white font-medium">{level.label}</div>
                    <div className="text-text-secondary text-sm">{level.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Тест звуков */}
          {enabled && (
            <div>
              <h4 className="text-white font-semibold mb-3">Тест звуков</h4>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <button
                  onClick={() => testSound('создание_ставки')}
                  className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                >
                  💎 Ставка
                </button>
                <button
                  onClick={() => testSound('победа')}
                  className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
                >
                  🎉 Победа
                </button>
                <button
                  onClick={() => testSound('покупка_гема')}
                  className="px-3 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors text-sm"
                >
                  💰 Покупка
                </button>
                <button
                  onClick={() => testSound('уведомление')}
                  className="px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors text-sm"
                >
                  🔔 Уведомление
                </button>
              </div>
              
              {/* Кнопка перезагрузки звуков */}
              <button
                onClick={handleReloadSounds}
                disabled={reloading}
                className="w-full px-3 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors text-sm disabled:opacity-50"
              >
                {reloading ? '🔄 Перезагружаем...' : '🔄 Перезагрузить звуки'}
              </button>
            </div>
          )}

          {/* Информация */}
          <div className="bg-surface-sidebar rounded-lg p-4">
            <div className="text-text-secondary text-sm">
              <p className="mb-2">
                <strong>💡 Совет:</strong> Звуки помогают лучше ощущать игровой процесс и не пропускать важные события.
              </p>
              <p>
                Настройки автоматически сохраняются и применяются ко всем играм.
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/80 transition-colors font-medium"
          >
            Готово
          </button>
        </div>
      </div>
    </div>
  );
};

export default SoundSettings;