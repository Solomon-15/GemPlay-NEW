import { useEffect, useCallback } from 'react';
import soundManager from '../utils/SoundManager';

/**
 * Хук для работы с новой звуковой системой
 */
export const useSound = () => {
  // Инициализация AudioContext при первом взаимодействии пользователя
  useEffect(() => {
    const handleFirstInteraction = () => {
      if (soundManager.context && soundManager.context.state === 'suspended') {
        soundManager.context.resume();
      }
      // Удаляем обработчики после первого взаимодействия
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('keydown', handleFirstInteraction);
    };

    document.addEventListener('click', handleFirstInteraction);
    document.addEventListener('keydown', handleFirstInteraction);

    return () => {
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('keydown', handleFirstInteraction);
    };
  }, []);

  // Игровые звуки с поддержкой типов игр
  const gameAudio = {
    createBet: useCallback((gameType = 'ALL') => soundManager.playSound('создание_ставки', gameType), []),
    acceptBet: useCallback((gameType = 'ALL') => soundManager.playSound('принятие_ставки', gameType), []),
    selectMove: useCallback((gameType = 'ALL') => soundManager.playSound('выбор_хода', gameType), []),
    reveal: useCallback((gameType = 'ALL') => soundManager.playSound('reveal', gameType), []),
    victory: useCallback((gameType = 'ALL') => soundManager.playSound('победа', gameType), []),
    defeat: useCallback((gameType = 'ALL') => soundManager.playSound('поражение', gameType), []),
    draw: useCallback((gameType = 'ALL') => soundManager.playSound('ничья', gameType), [])
  };

  // Звуки действий с гемами
  const gemAudio = {
    buy: useCallback(() => soundManager.playSound('покупка_гема'), []),
    sell: useCallback(() => soundManager.playSound('продажа_гема'), []),
    gift: useCallback(() => soundManager.playSound('подарок_гемов'), [])
  };

  // Звуки интерфейса
  const uiAudio = {
    hover: useCallback(() => soundManager.playSound('hover'), []),
    modalOpen: useCallback(() => soundManager.playSound('открытие_модала'), []),
    modalClose: useCallback(() => soundManager.playSound('закрытие_модала'), []),
    notification: useCallback(() => soundManager.playSound('уведомление'), []),
    error: useCallback(() => soundManager.playSound('ошибка'), []),
    click: useCallback(() => soundManager.playSound('создание_ставки'), []) // Переиспользуем звук создания ставки для кликов
  };

  // Звуки системы
  const systemAudio = {
    timerExpire: useCallback(() => soundManager.playSound('таймер_reveal'), []),
    reward: useCallback(() => soundManager.playSound('награда'), [])
  };

  // Настройки звука
  const soundSettings = {
    isEnabled: useCallback(() => soundManager.enabled, []),
    getVolume: useCallback(() => soundManager.volume, []),
    setEnabled: useCallback((enabled) => soundManager.updateSettings(enabled, soundManager.volume), []),
    setVolume: useCallback((volume) => soundManager.updateSettings(soundManager.enabled, volume), []),
    reloadSounds: useCallback(() => soundManager.reloadSounds(), [])
  };

  // Совместимость с существующим API
  const playSound = {
    createBet: gameAudio.createBet,
    acceptBet: gameAudio.acceptBet,
    selectMove: gameAudio.selectMove,
    reveal: gameAudio.reveal,
    victory: gameAudio.victory,
    defeat: gameAudio.defeat,
    draw: gameAudio.draw,
    buyGem: gemAudio.buy,
    sellGem: gemAudio.sell,
    giftGem: gemAudio.gift,
    hover: uiAudio.hover,
    modalOpen: uiAudio.modalOpen,
    modalClose: uiAudio.modalClose,
    notification: uiAudio.notification,
    error: uiAudio.error,
    settings: uiAudio.click,
    timerExpire: systemAudio.timerExpire,
    reward: systemAudio.reward
  };

  return {
    // Группы звуков
    game: gameAudio,
    gem: gemAudio,
    ui: uiAudio,
    system: systemAudio,
    
    // Настройки
    settings: soundSettings,
    
    // Прямой доступ к playSound для совместимости
    playSound,
    
    // Новые функции
    playCoin: gemAudio.buy, // Алиас для совместимости
    playClick: uiAudio.click,
    playSuccess: gameAudio.victory,
    playModalClose: uiAudio.modalClose,
    playHover: uiAudio.hover
  };
};

/**
 * Хук для автоматического добавления звука при наведении на элементы
 */
export const useHoverSound = (enabled = true) => {
  const { ui } = useSound();

  const hoverProps = enabled ? {
    onMouseEnter: ui.hover
  } : {};

  return hoverProps;
};

/**
 * Хук для звуков модальных окон
 */
export const useModalSound = () => {
  const { ui } = useSound();

  return {
    onOpen: ui.modalOpen,
    onClose: ui.modalClose
  };
};

/**
 * Хук для звуков игрового процесса с автоматическими эффектами
 */
export const useGameSound = (gameResult) => {
  const { game } = useSound();

  useEffect(() => {
    if (gameResult) {
      switch (gameResult.toLowerCase()) {
        case 'win':
        case 'victory':
          game.victory();
          break;
        case 'lose':
        case 'defeat':
          game.defeat();
          break;
        case 'draw':
        case 'tie':
          game.draw();
          break;
      }
    }
  }, [gameResult, game]);

  return game;
};