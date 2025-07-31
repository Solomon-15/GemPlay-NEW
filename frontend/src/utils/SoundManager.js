/**
 * Advanced Sound Manager for GemPlay
 * Управление звуковыми эффектами с поддержкой API и приоритетов
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

class SoundManager {
  constructor() {
    this.enabled = true;
    this.volume = 0.3;
    this.sounds = new Map(); // Хранилище звуков по event_trigger
    this.audioCache = new Map(); // Кэш аудиофайлов
    this.context = null;
    this.contextInitialized = false;
    this.userInteracted = false;
    this.currentlyPlaying = null; // Для системы приоритетов
    this.criticalSounds = new Set(); // Критичные звуки для предзагрузки
    
    // НЕ инициализируем AudioContext сразу - ждем пользовательского взаимодействия
    this.loadSettings();
    this.loadSounds();
    
    this.criticalSounds = new Set([
      'создание_ставки',
      'принятие_ставки', 
      'выбор_хода',
      'reveal',
      'победа',
      'поражение',
      'ничья',
      'покупка_гема',
      'продажа_гема'
    ]);

    // Слушатели для первого пользовательского взаимодействия
    this.setupUserInteractionListeners();
  }

  setupUserInteractionListeners() {
    const handleFirstInteraction = () => {
      if (!this.userInteracted) {
        this.userInteracted = true;
        this.initAudioContext();
        
        // Удаляем слушатели после первого взаимодействия
        document.removeEventListener('click', handleFirstInteraction);
        document.removeEventListener('touchstart', handleFirstInteraction);
        document.removeEventListener('keydown', handleFirstInteraction);
        
        console.log('🔊 Audio context activated after user interaction');
      }
    };

    // Добавляем слушатели для различных типов взаимодействия
    document.addEventListener('click', handleFirstInteraction, { passive: true });
    document.addEventListener('touchstart', handleFirstInteraction, { passive: true });
    document.addEventListener('keydown', handleFirstInteraction, { passive: true });
  }

  initAudioContext() {
    if (this.contextInitialized) return;
    
    try {
      this.context = new (window.AudioContext || window.webkitAudioContext)();
      this.contextInitialized = true;
      console.log('🔊 AudioContext successfully initialized');
    } catch (error) {
      console.warn('AudioContext не поддерживается:', error);
    }
  }

  loadSettings() {
    try {
      const settings = JSON.parse(localStorage.getItem('gemplay-sound-settings') || '{}');
      this.enabled = settings.enabled !== false;
      this.volume = settings.volume || 0.3;
    } catch (error) {
      console.warn('Ошибка загрузки настроек звука:', error);
    }
  }

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

  async loadSounds() {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.log('No auth token, using fallback sounds');
        this.createFallbackSounds();
        return;
      }

      const response = await fetch(`${API}/admin/sounds`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const soundsData = await response.json();
      console.log(`Loaded ${soundsData.length} sounds from API`);

      for (const sound of soundsData) {
        if (!this.sounds.has(sound.event_trigger)) {
          this.sounds.set(sound.event_trigger, []);
        }
        this.sounds.get(sound.event_trigger).push(sound);
      }

      for (const [trigger, soundList] of this.sounds.entries()) {
        soundList.sort((a, b) => b.priority - a.priority);
      }

      await this.preloadCriticalSounds();

    } catch (error) {
      console.warn('Ошибка загрузки звуков из API:', error);
      this.createFallbackSounds();
    }
  }

  async preloadCriticalSounds() {
    const preloadPromises = [];
    
    for (const trigger of this.criticalSounds) {
      const soundList = this.sounds.get(trigger);
      if (soundList) {
        for (const sound of soundList) {
          if (sound.has_audio_file && !this.audioCache.has(sound.id)) {
            preloadPromises.push(this.loadAudioFile(sound));
          }
        }
      }
    }

    try {
      await Promise.all(preloadPromises);
      console.log('Critical sounds preloaded');
    } catch (error) {
      console.warn('Error preloading critical sounds:', error);
    }
  }

  async loadAudioFile(sound) {
    if (this.audioCache.has(sound.id)) {
      return this.audioCache.get(sound.id);
    }

    try {
      const audioBuffer = await this.createProgrammaticSound(sound.event_trigger);
      this.audioCache.set(sound.id, audioBuffer);
      return audioBuffer;
    } catch (error) {
      console.warn(`Error loading audio for sound ${sound.id}:`, error);
      return null;
    }
  }

  createFallbackSounds() {
    const fallbackSounds = [
      { event_trigger: 'создание_ставки', priority: 7, is_enabled: true, volume: 0.5, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'принятие_ставки', priority: 6, is_enabled: true, volume: 0.5, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'выбор_хода', priority: 5, is_enabled: true, volume: 0.5, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'reveal', priority: 8, is_enabled: true, volume: 0.6, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'победа', priority: 9, is_enabled: true, volume: 0.8, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'поражение', priority: 6, is_enabled: true, volume: 0.4, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'ничья', priority: 4, is_enabled: true, volume: 0.5, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'покупка_гема', priority: 6, is_enabled: true, volume: 0.6, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'hover', priority: 2, is_enabled: true, volume: 0.3, delay: 0, can_repeat: false, game_type: 'ALL' },
      { event_trigger: 'открытие_модала', priority: 3, is_enabled: true, volume: 0.4, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'закрытие_модала', priority: 3, is_enabled: true, volume: 0.4, delay: 0, can_repeat: true, game_type: 'ALL' },
      { event_trigger: 'ошибка', priority: 8, is_enabled: true, volume: 0.5, delay: 0, can_repeat: true, game_type: 'ALL' },
    ];

    for (const sound of fallbackSounds) {
      if (!this.sounds.has(sound.event_trigger)) {
        this.sounds.set(sound.event_trigger, []);
      }
      this.sounds.get(sound.event_trigger).push(sound);
    }

    console.log('Fallback sounds created');
  }

  async playSound(eventTrigger, gameType = 'ALL', volumeMultiplier = 1) {
    if (!this.enabled) return;

    // Если пользователь еще не взаимодействовал с страницей, не воспроизводим звук
    if (!this.userInteracted || !this.context) {
      console.log(`🔇 Sound skipped (no user interaction yet): ${eventTrigger}`);
      return;
    }

    const soundList = this.sounds.get(eventTrigger);
    if (!soundList || soundList.length === 0) {
      console.warn(`Sound not found for event: ${eventTrigger}`);
      return;
    }

    const applicableSounds = soundList.filter(sound => 
      sound.is_enabled && 
      (sound.game_type === 'ALL' || sound.game_type === gameType)
    );

    if (applicableSounds.length === 0) {
      console.warn(`No applicable sounds for event: ${eventTrigger}, gameType: ${gameType}`);
      return;
    }

    const sound = applicableSounds[0];

    if (this.currentlyPlaying && this.currentlyPlaying.priority >= sound.priority) {
      console.log(`Sound blocked by higher priority: ${this.currentlyPlaying.priority} >= ${sound.priority}`);
      return;
    }

    if (!sound.can_repeat && this.currentlyPlaying && this.currentlyPlaying.event_trigger === eventTrigger) {
      console.log(`Sound repeat blocked for: ${eventTrigger}`);
      return;
    }

    if (this.currentlyPlaying) {
      this.stopCurrentSound();
    }

    if (sound.delay > 0) {
      await new Promise(resolve => setTimeout(resolve, sound.delay));
    }

    try {
      // Убеждаемся, что AudioContext запущен
      if (this.context.state === 'suspended') {
        await this.context.resume();
      }

      this.currentlyPlaying = sound;
      
      if (sound.has_audio_file) {
        await this.playAudioFile(sound, volumeMultiplier);
      } else {
        await this.playProgrammaticSound(sound, volumeMultiplier);
      }

    } catch (error) {
      console.warn(`Error playing sound ${eventTrigger}:`, error);
    } finally {
      this.currentlyPlaying = null;
    }
  }

  async playAudioFile(sound, volumeMultiplier) {
    let audioBuffer = this.audioCache.get(sound.id);
    
    if (!audioBuffer) {
      audioBuffer = await this.loadAudioFile(sound);
      if (!audioBuffer) {
        // Fallback to programmatic sound
        await this.playProgrammaticSound(sound, volumeMultiplier);
        return;
      }
    }

    const source = this.context.createBufferSource();
    const gainNode = this.context.createGain();
    
    source.buffer = audioBuffer;
    source.connect(gainNode);
    gainNode.connect(this.context.destination);
    
    const finalVolume = this.volume * sound.volume * volumeMultiplier;
    gainNode.gain.setValueAtTime(finalVolume, this.context.currentTime);
    
    source.start(0);
    
    source.onended = () => {
      if (this.currentlyPlaying === sound) {
        this.currentlyPlaying = null;
      }
    };
  }

  async playProgrammaticSound(sound, volumeMultiplier) {
    const soundFunction = this.getProgrammaticSoundFunction(sound.event_trigger);
    if (soundFunction) {
      const finalVolume = this.volume * sound.volume * volumeMultiplier;
      soundFunction(finalVolume);
      
      setTimeout(() => {
        if (this.currentlyPlaying === sound) {
          this.currentlyPlaying = null;
        }
      }, 1000);
    }
  }

  getProgrammaticSoundFunction(eventTrigger) {
    const soundMap = {
      'создание_ставки': (volume) => this.createClickSound(800, 0.1 * volume, 'sine'),
      'принятие_ставки': (volume) => this.createTingSound([600, 800], 0.3 * volume),
      'выбор_хода': (volume) => this.createClickSound(400, 0.05 * volume, 'square'),
      'reveal': (volume) => this.createMagicalSound(volume),
      'победа': (volume) => this.createVictorySound(volume),
      'поражение': (volume) => this.createDefeatSound(volume),
      'ничья': (volume) => this.createDrawSound(volume),
      'покупка_гема': (volume) => this.createCoinSound(volume),
      'продажа_гема': (volume) => this.createCrystalSound(volume),
      'подарок_гемов': (volume) => this.createGiftSound(volume),
      'hover': (volume) => this.createHoverSound(volume),
      'открытие_модала': (volume) => this.createWooshSound(true, volume),
      'закрытие_модала': (volume) => this.createWooshSound(false, volume),
      'уведомление': (volume) => this.createNotificationSound(volume),
      'ошибка': (volume) => this.createErrorSound(volume),
      'таймер_reveal': (volume) => this.createExpireSound(volume),
      'награда': (volume) => this.createRewardSound(volume)
    };

    return soundMap[eventTrigger];
  }

  stopCurrentSound() {
    this.currentlyPlaying = null;
  }

  updateSettings(enabled, volume) {
    this.enabled = enabled;
    this.volume = Math.max(0, Math.min(1, volume));
    this.saveSettings();
  }

  async reloadSounds() {
    this.sounds.clear();
    this.audioCache.clear();
    await this.loadSounds();
  }

  async createProgrammaticSound(eventTrigger) {
    return null;
  }

  
  createClickSound(frequency = 800, duration = 0.1, waveType = 'sine') {
    if (!this.context) return;

    const oscillator = this.context.createOscillator();
    const gainNode = this.context.createGain();
    
    oscillator.frequency.setValueAtTime(frequency, this.context.currentTime);
    oscillator.type = waveType;
    
    gainNode.gain.setValueAtTime(0, this.context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.3 * this.volume, this.context.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + duration);
    
    oscillator.connect(gainNode);
    gainNode.connect(this.context.destination);
    
    oscillator.start(this.context.currentTime);
    oscillator.stop(this.context.currentTime + duration);
  }

  createTingSound(frequencies = [600, 800], duration = 0.3) {
    if (!this.context) return;

    frequencies.forEach((freq, index) => {
      const delay = index * 0.05;
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.frequency.setValueAtTime(freq, this.context.currentTime + delay);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0, this.context.currentTime + delay);
      gainNode.gain.linearRampToValueAtTime(0.2 * this.volume, this.context.currentTime + delay + 0.01);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + delay + duration);
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.start(this.context.currentTime + delay);
      oscillator.stop(this.context.currentTime + delay + duration);
    });
  }

  createMagicalSound(volume = 1) {
    if (!this.context) return;

    const baseTime = this.context.currentTime;
    const frequencies = [440, 554, 659, 880];
    
    frequencies.forEach((freq, index) => {
      const delay = index * 0.1;
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.frequency.setValueAtTime(freq, baseTime + delay);
      oscillator.frequency.exponentialRampToValueAtTime(freq * 1.5, baseTime + delay + 0.5);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0, baseTime + delay);
      gainNode.gain.linearRampToValueAtTime(0.3 * this.volume * volume, baseTime + delay + 0.1);
      gainNode.gain.exponentialRampToValueAtTime(0.001, baseTime + delay + 0.8);
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.start(baseTime + delay);
      oscillator.stop(baseTime + delay + 0.8);
    });
  }

  createVictorySound(volume = 1) {
    if (!this.context) return;

    const baseTime = this.context.currentTime;
    const melody = [523, 659, 784, 1047]; // C5, E5, G5, C6
    
    melody.forEach((freq, index) => {
      const delay = index * 0.15;
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.frequency.setValueAtTime(freq, baseTime + delay);
      oscillator.type = 'triangle';
      
      gainNode.gain.setValueAtTime(0, baseTime + delay);
      gainNode.gain.linearRampToValueAtTime(0.4 * this.volume * volume, baseTime + delay + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.001, baseTime + delay + 0.3);
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.start(baseTime + delay);
      oscillator.stop(baseTime + delay + 0.3);
    });
  }

  createDefeatSound(volume = 1) {
    if (!this.context) return;

    const oscillator = this.context.createOscillator();
    const gainNode = this.context.createGain();
    
    oscillator.frequency.setValueAtTime(220, this.context.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(110, this.context.currentTime + 0.8);
    oscillator.type = 'sawtooth';
    
    gainNode.gain.setValueAtTime(0, this.context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.2 * this.volume * volume, this.context.currentTime + 0.1);
    gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.8);
    
    oscillator.connect(gainNode);
    gainNode.connect(this.context.destination);
    
    oscillator.start(this.context.currentTime);
    oscillator.stop(this.context.currentTime + 0.8);
  }

  createDrawSound(volume = 1) {
    if (!this.context) return;

    const oscillator = this.context.createOscillator();
    const gainNode = this.context.createGain();
    
    oscillator.frequency.setValueAtTime(330, this.context.currentTime);
    oscillator.type = 'square';
    
    gainNode.gain.setValueAtTime(0, this.context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.15 * this.volume * volume, this.context.currentTime + 0.1);
    gainNode.gain.linearRampToValueAtTime(0, this.context.currentTime + 0.3);
    
    oscillator.connect(gainNode);
    gainNode.connect(this.context.destination);
    
    oscillator.start(this.context.currentTime);
    oscillator.stop(this.context.currentTime + 0.3);
  }

  createCoinSound(volume = 1) {
    if (!this.context) return;

    const frequencies = [800, 1000, 1200];
    frequencies.forEach((freq, index) => {
      const delay = index * 0.05;
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.frequency.setValueAtTime(freq, this.context.currentTime + delay);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0, this.context.currentTime + delay);
      gainNode.gain.linearRampToValueAtTime(0.25 * this.volume * volume, this.context.currentTime + delay + 0.01);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + delay + 0.2);
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.start(this.context.currentTime + delay);
      oscillator.stop(this.context.currentTime + delay + 0.2);
    });
  }

  createCrystalSound(volume = 1) {
    if (!this.context) return;

    for (let i = 0; i < 8; i++) {
      const delay = i * 0.02;
      const freq = 800 + Math.random() * 800;
      
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.frequency.setValueAtTime(freq, this.context.currentTime + delay);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0, this.context.currentTime + delay);
      gainNode.gain.linearRampToValueAtTime(0.1 * this.volume * volume, this.context.currentTime + delay + 0.01);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + delay + 0.3);
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.start(this.context.currentTime + delay);
      oscillator.stop(this.context.currentTime + delay + 0.3);
    }
  }

  createGiftSound(volume = 1) {
    if (!this.context) return;

    const baseTime = this.context.currentTime;
    const melody = [659, 784, 988]; // E5, G5, B5
    
    melody.forEach((freq, index) => {
      const delay = index * 0.1;
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.frequency.setValueAtTime(freq, baseTime + delay);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0, baseTime + delay);
      gainNode.gain.linearRampToValueAtTime(0.2 * this.volume * volume, baseTime + delay + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.001, baseTime + delay + 0.25);
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.start(baseTime + delay);
      oscillator.stop(baseTime + delay + 0.25);
    });
  }

  createHoverSound(volume = 1) {
    if (!this.context) return;

    const oscillator = this.context.createOscillator();
    const gainNode = this.context.createGain();
    
    oscillator.frequency.setValueAtTime(500, this.context.currentTime);
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0, this.context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.1 * this.volume * volume, this.context.currentTime + 0.02);
    gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.1);
    
    oscillator.connect(gainNode);
    gainNode.connect(this.context.destination);
    
    oscillator.start(this.context.currentTime);
    oscillator.stop(this.context.currentTime + 0.1);
  }

  createWooshSound(opening = true, volume = 1) {
    if (!this.context) return;

    const oscillator = this.context.createOscillator();
    const gainNode = this.context.createGain();
    
    if (opening) {
      oscillator.frequency.setValueAtTime(200, this.context.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(800, this.context.currentTime + 0.3);
    } else {
      oscillator.frequency.setValueAtTime(800, this.context.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(200, this.context.currentTime + 0.3);
    }
    
    oscillator.type = 'sawtooth';
    
    gainNode.gain.setValueAtTime(0, this.context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.15 * this.volume * volume, this.context.currentTime + 0.1);
    gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.3);
    
    oscillator.connect(gainNode);
    gainNode.connect(this.context.destination);
    
    oscillator.start(this.context.currentTime);
    oscillator.stop(this.context.currentTime + 0.3);
  }

  createNotificationSound(volume = 1) {
    if (!this.context) return;

    const frequencies = [523, 659, 523]; // C5, E5, C5
    frequencies.forEach((freq, index) => {
      const delay = index * 0.15;
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.frequency.setValueAtTime(freq, this.context.currentTime + delay);
      oscillator.type = 'square';
      
      gainNode.gain.setValueAtTime(0, this.context.currentTime + delay);
      gainNode.gain.linearRampToValueAtTime(0.2 * this.volume * volume, this.context.currentTime + delay + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + delay + 0.2);
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.start(this.context.currentTime + delay);
      oscillator.stop(this.context.currentTime + delay + 0.2);
    });
  }

  createErrorSound(volume = 1) {
    if (!this.context) return;

    const oscillator = this.context.createOscillator();
    const gainNode = this.context.createGain();
    
    oscillator.frequency.setValueAtTime(300, this.context.currentTime);
    oscillator.frequency.linearRampToValueAtTime(250, this.context.currentTime + 0.15);
    oscillator.frequency.linearRampToValueAtTime(300, this.context.currentTime + 0.3);
    oscillator.type = 'square';
    
    gainNode.gain.setValueAtTime(0, this.context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.2 * this.volume * volume, this.context.currentTime + 0.05);
    gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.3);
    
    oscillator.connect(gainNode);
    gainNode.connect(this.context.destination);
    
    oscillator.start(this.context.currentTime);
    oscillator.stop(this.context.currentTime + 0.3);
  }

  createExpireSound(volume = 1) {
    if (!this.context) return;

    const oscillator = this.context.createOscillator();
    const gainNode = this.context.createGain();
    
    oscillator.frequency.setValueAtTime(400, this.context.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(200, this.context.currentTime + 1.0);
    oscillator.type = 'triangle';
    
    gainNode.gain.setValueAtTime(0, this.context.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.25 * this.volume * volume, this.context.currentTime + 0.1);
    gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 1.0);
    
    oscillator.connect(gainNode);
    gainNode.connect(this.context.destination);
    
    oscillator.start(this.context.currentTime);
    oscillator.stop(this.context.currentTime + 1.0);
  }

  createRewardSound(volume = 1) {
    if (!this.context) return;

    const baseTime = this.context.currentTime;
    const melody = [523, 659, 784, 1047, 1319]; // C5, E5, G5, C6, E6
    
    melody.forEach((freq, index) => {
      const delay = index * 0.1;
      const oscillator = this.context.createOscillator();
      const gainNode = this.context.createGain();
      
      oscillator.frequency.setValueAtTime(freq, baseTime + delay);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0, baseTime + delay);
      gainNode.gain.linearRampToValueAtTime(0.3 * this.volume * volume, baseTime + delay + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.001, baseTime + delay + 0.4);
      
      oscillator.connect(gainNode);
      gainNode.connect(this.context.destination);
      
      oscillator.start(baseTime + delay);
      oscillator.stop(baseTime + delay + 0.4);
    });
  }
}

const soundManager = new SoundManager();

export default soundManager;