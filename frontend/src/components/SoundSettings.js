import React, { useState, useEffect } from 'react';
import { soundSystem, playSound } from '../utils/soundSystem';

const SoundSettings = ({ isOpen, onClose }) => {
  const [volumeLevel, setVolumeLevel] = useState(soundSystem.getVolumeLevel());
  const [enabled, setEnabled] = useState(soundSystem.getEnabled());

  useEffect(() => {
    setVolumeLevel(soundSystem.getVolumeLevel());
    setEnabled(soundSystem.getEnabled());
  }, [isOpen]);

  const handleVolumeChange = (level) => {
    soundSystem.setVolumeLevel(level);
    setVolumeLevel(level);
    setEnabled(level !== 'off');
    
    // Проигрываем тестовый звук
    if (level !== 'off') {
      setTimeout(() => playSound.settings(), 100);
    }
  };

  const testSound = (soundName) => {
    if (enabled) {
      playSound[soundName]();
    }
  };

  if (!isOpen) return null;

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
                    checked={volumeLevel === level.value}
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
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => testSound('createBet')}
                  className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                >
                  💎 Ставка
                </button>
                <button
                  onClick={() => testSound('victory')}
                  className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
                >
                  🎉 Победа
                </button>
                <button
                  onClick={() => testSound('buyGem')}
                  className="px-3 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors text-sm"
                >
                  💰 Покупка
                </button>
                <button
                  onClick={() => testSound('notification')}
                  className="px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors text-sm"
                >
                  🔔 Уведомление
                </button>
              </div>
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