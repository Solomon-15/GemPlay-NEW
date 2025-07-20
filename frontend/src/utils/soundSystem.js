/**
 * Sound System for GemPlay
 * Управление звуковыми эффектами с настройками громкости
 */

class SoundSystem {
  constructor() {
    this.enabled = true;
    this.volume = 0.3; // Тихий режим по умолчанию
    this.sounds = {};
    this.context = null;
    
    // Инициализация AudioContext
    this.initAudioContext();
    
    // Загрузка настроек из localStorage
    this.loadSettings();
    
    // Создание звуков программно (для начала)
    this.createProgrammaticSounds();
  }

  initAudioContext() {
    try {
      this.context = new (window.AudioContext || window.webkitAudioContext)();
    } catch (error) {
      console.warn('AudioContext не поддерживается:', error);
    }
  }

  // Загрузка настроек звука из localStorage
  loadSettings() {
    try {
      const settings = JSON.parse(localStorage.getItem('gemplay-sound-settings') || '{}');
      this.enabled = settings.enabled !== false; // По умолчанию включено
      this.volume = settings.volume || 0.3; // Тихий режим по умолчанию
    } catch (error) {
      console.warn('Ошибка загрузки настроек звука:', error);
    }
  }

  // Сохранение настроек звука
  saveSettings() {
    try {
      const settings = {
        enabled: this.enabled,
        volume: this.volume
      };
      localStorage.setItem('gemplay-sound-settings', JSON.stringify(settings));
    } catch (error) {
      console.warn('Ошибка сохранения настроек звука:', error);
    }
  }

  // Создание звуков программно с помощью Web Audio API
  createProgrammaticSounds() {
    if (!this.context) return;

    // 1. Создание ставки - короткий щелчок
    this.sounds.createBet = () => this.createClickSound(800, 0.1, 'sine');

    // 2. Принятие ставки - подтверждающий "тинг"
    this.sounds.acceptBet = () => this.createTingSound([600, 800], 0.3);

    // 3. Выбор хода - тактильный щелчок
    this.sounds.selectMove = () => this.createClickSound(400, 0.05, 'square');

    // 4. Reveal - магический звук
    this.sounds.reveal = () => this.createMagicalSound();

    // 5. Победа - торжественная фанфара
    this.sounds.victory = () => this.createVictorySound();

    // 6. Поражение - мягкий грустный звук
    this.sounds.defeat = () => this.createDefeatSound();

    // 7. Ничья - нейтральный звук
    this.sounds.draw = () => this.createDrawSound();

    // 8. Покупка гема - звон монеты
    this.sounds.buyGem = () => this.createCoinSound();

    // 9. Продажа гема - рассыпание кристаллов
    this.sounds.sellGem = () => this.createCrystalSound();

    // 10. Подарок гемов - всплеск света
    this.sounds.giftGem = () => this.createGiftSound();

    // 11. Наведение на элементы - лёгкий ховер
    this.sounds.hover = () => this.createHoverSound();

    // 12. Модальные окна - woosh
    this.sounds.modalOpen = () => this.createWooshSound(true);
    this.sounds.modalClose = () => this.createWooshSound(false);

    // 13. Уведомления - чёткий сигнал
    this.sounds.notification = () => this.createNotificationSound();

    // 14. Ошибка - предупреждающий пинг
    this.sounds.error = () => this.createErrorSound();

    // 15. Таймер - тиканье и отмена
    this.sounds.timerTick = () => this.createTickSound();
    this.sounds.timerExpire = () => this.createExpireSound();

    // 16. Награда - праздничный bling
    this.sounds.reward = () => this.createRewardSound();

    // 17. Настройки - тонкий клик
    this.sounds.settings = () => this.createSettingsSound();
  }

  // Базовая функция воспроизведения звука
  playSound(soundName, volumeMultiplier = 1) {
    if (!this.enabled || !this.context || !this.sounds[soundName]) return;

    try {
      // Возобновляем AudioContext если приостановлен
      if (this.context.state === 'suspended') {
        this.context.resume();
      }

      this.sounds[soundName](this.volume * volumeMultiplier);
    } catch (error) {
      console.warn(`Ошибка воспроизведения звука ${soundName}:`, error);
    }
  }

  // Создание простого щелчка
  createClickSound(frequency, duration, waveType = 'sine') {
    return (volume) => {
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.frequency.value = frequency;
      oscillator.type = waveType;
      
      gainNode.gain.setValueAtTime(0, this.context.currentTime);
      gainNode.gain.linearRampToValueAtTime(volume, this.context.currentTime + 0.01);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + duration);
      
      oscillator.start(this.context.currentTime);
      oscillator.stop(this.context.currentTime + duration);
    };
  }

  // Создание "тинг" звука
  createTingSound(frequencies, duration) {
    return (volume) => {
      frequencies.forEach((freq, index) => {
        setTimeout(() => {
          const oscillator = this.context.createOscillator();
          const gainNode = this.context.createGain();
          
          oscillator.connect(gainNode);
          gainNode.connect(this.context.destination);
          
          oscillator.frequency.value = freq;
          oscillator.type = 'sine';
          
          gainNode.gain.setValueAtTime(0, this.context.currentTime);
          gainNode.gain.linearRampToValueAtTime(volume * 0.5, this.context.currentTime + 0.01);
          gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + duration);
          
          oscillator.start(this.context.currentTime);
          oscillator.stop(this.context.currentTime + duration);
        }, index * 50);
      });
    };
  }

  // Магический звук для reveal
  createMagicalSound() {
    return (volume) => {
      const frequencies = [400, 500, 600, 800, 1000];
      frequencies.forEach((freq, index) => {
        setTimeout(() => {
          const oscillator = this.context.createOscillator();
          const gainNode = this.context.createGain();
          
          oscillator.connect(gainNode);
          gainNode.connect(this.context.destination);
          
          oscillator.frequency.setValueAtTime(freq, this.context.currentTime);
          oscillator.frequency.linearRampToValueAtTime(freq * 1.5, this.context.currentTime + 0.3);
          oscillator.type = 'triangle';
          
          gainNode.gain.setValueAtTime(0, this.context.currentTime);
          gainNode.gain.linearRampToValueAtTime(volume * 0.3, this.context.currentTime + 0.05);
          gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.4);
          
          oscillator.start(this.context.currentTime);
          oscillator.stop(this.context.currentTime + 0.4);
        }, index * 60);
      });
    };
  }

  // Звук победы
  createVictorySound() {
    return (volume) => {
      const notes = [262, 330, 392, 523]; // C-E-G-C октава
      notes.forEach((freq, index) => {
        setTimeout(() => {
          const oscillator = this.context.createOscillator();
          const gainNode = this.context.createGain();
          
          oscillator.connect(gainNode);
          gainNode.connect(this.context.destination);
          
          oscillator.frequency.value = freq;
          oscillator.type = 'triangle';
          
          gainNode.gain.setValueAtTime(0, this.context.currentTime);
          gainNode.gain.linearRampToValueAtTime(volume * 0.4, this.context.currentTime + 0.05);
          gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.3);
          
          oscillator.start(this.context.currentTime);
          oscillator.stop(this.context.currentTime + 0.3);
        }, index * 120);
      });
    };
  }

  // Звук поражения
  createDefeatSound() {
    return (volume) => {
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.frequency.setValueAtTime(300, this.context.currentTime);
      oscillator.frequency.linearRampToValueAtTime(150, this.context.currentTime + 0.5);
      oscillator.type = 'sawtooth';
      
      gainNode.gain.setValueAtTime(0, this.context.currentTime);
      gainNode.gain.linearRampToValueAtTime(volume * 0.2, this.context.currentTime + 0.1);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.6);
      
      oscillator.start(this.context.currentTime);
      oscillator.stop(this.context.currentTime + 0.6);
    };
  }

  // Остальные звуки (сокращенно для экономии места)
  createDrawSound() {
    return (volume) => this.createClickSound(300, 0.2, 'square')(volume);
  }

  createCoinSound() {
    return (volume) => {
      [800, 1000, 1200].forEach((freq, i) => {
        setTimeout(() => this.createClickSound(freq, 0.1, 'sine')(volume * 0.5), i * 30);
      });
    };
  }

  createCrystalSound() {
    return (volume) => {
      for (let i = 0; i < 5; i++) {
        setTimeout(() => {
          this.createClickSound(1000 + Math.random() * 500, 0.08, 'triangle')(volume * 0.3);
        }, i * 20);
      }
    };
  }

  createGiftSound() {
    return (volume) => this.createTingSound([500, 700, 900], 0.4)(volume);
  }

  createHoverSound() {
    return (volume) => this.createClickSound(600, 0.05, 'sine')(volume * 0.3);
  }

  createWooshSound(opening) {
    return (volume) => {
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      const startFreq = opening ? 200 : 400;
      const endFreq = opening ? 400 : 200;
      
      oscillator.frequency.setValueAtTime(startFreq, this.context.currentTime);
      oscillator.frequency.linearRampToValueAtTime(endFreq, this.context.currentTime + 0.2);
      oscillator.type = 'sawtooth';
      
      gainNode.gain.setValueAtTime(0, this.context.currentTime);
      gainNode.gain.linearRampToValueAtTime(volume * 0.2, this.context.currentTime + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.25);
      
      oscillator.start(this.context.currentTime);
      oscillator.stop(this.context.currentTime + 0.25);
    };
  }

  createNotificationSound() {
    return (volume) => this.createTingSound([600, 800], 0.2)(volume);
  }

  createErrorSound() {
    return (volume) => {
      [400, 350, 300].forEach((freq, i) => {
        setTimeout(() => this.createClickSound(freq, 0.15, 'square')(volume * 0.4), i * 100);
      });
    };
  }

  createTickSound() {
    return (volume) => this.createClickSound(1000, 0.05, 'square')(volume * 0.2);
  }

  createExpireSound() {
    return (volume) => {
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.frequency.setValueAtTime(800, this.context.currentTime);
      oscillator.frequency.linearRampToValueAtTime(200, this.context.currentTime + 0.8);
      oscillator.type = 'sawtooth';
      
      gainNode.gain.setValueAtTime(0, this.context.currentTime);
      gainNode.gain.linearRampToValueAtTime(volume * 0.3, this.context.currentTime + 0.1);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.9);
      
      oscillator.start(this.context.currentTime);
      oscillator.stop(this.context.currentTime + 0.9);
    };
  }

  createRewardSound() {
    return (volume) => {
      const notes = [523, 659, 784, 1047]; // C5-E5-G5-C6
      notes.forEach((freq, index) => {
        setTimeout(() => {
          this.createClickSound(freq, 0.3, 'triangle')(volume * 0.4);
        }, index * 80);
      });
    };
  }

  createSettingsSound() {
    return (volume) => this.createClickSound(500, 0.05, 'sine')(volume * 0.3);
  }

  // Управление настройками
  setEnabled(enabled) {
    this.enabled = enabled;
    this.saveSettings();
  }

  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume)); // 0-1
    this.saveSettings();
  }

  getEnabled() {
    return this.enabled;
  }

  getVolume() {
    return this.volume;
  }

  // Предустановленные уровни громкости
  setVolumeLevel(level) {
    switch (level) {
      case 'off':
        this.setEnabled(false);
        break;
      case 'quiet':
        this.setEnabled(true);
        this.setVolume(0.2);
        break;
      case 'normal':
        this.setEnabled(true);
        this.setVolume(0.5);
        break;
      case 'loud':
        this.setEnabled(true);
        this.setVolume(0.8);
        break;
    }
  }

  getVolumeLevel() {
    if (!this.enabled) return 'off';
    if (this.volume <= 0.3) return 'quiet';
    if (this.volume <= 0.6) return 'normal';
    return 'loud';
  }
}

// Создаем глобальный экземпляр
export const soundSystem = new SoundSystem();

// Хелпер функции для легкого использования
export const playSound = {
  createBet: () => soundSystem.playSound('createBet'),
  acceptBet: () => soundSystem.playSound('acceptBet'),
  selectMove: () => soundSystem.playSound('selectMove'),
  reveal: () => soundSystem.playSound('reveal'),
  victory: () => soundSystem.playSound('victory'),
  defeat: () => soundSystem.playSound('defeat'),
  draw: () => soundSystem.playSound('draw'),
  buyGem: () => soundSystem.playSound('buyGem'),
  sellGem: () => soundSystem.playSound('sellGem'),
  giftGem: () => soundSystem.playSound('giftGem'),
  hover: () => soundSystem.playSound('hover', 0.5), // Тише для ховера
  modalOpen: () => soundSystem.playSound('modalOpen'),
  modalClose: () => soundSystem.playSound('modalClose'),
  notification: () => soundSystem.playSound('notification'),
  error: () => soundSystem.playSound('error'),
  timerTick: () => soundSystem.playSound('timerTick'),
  timerExpire: () => soundSystem.playSound('timerExpire'),
  reward: () => soundSystem.playSound('reward'),
  settings: () => soundSystem.playSound('settings')
};

export default soundSystem;