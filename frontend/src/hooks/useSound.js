import { useEffect, useCallback } from 'react';
import { soundSystem, playSound } from '../utils/soundSystem';

/**
 * Хук для работы со звуковыми эффектами
 */
export const useSound = () => {
  // Инициализация AudioContext при первом взаимодействии пользователя
  useEffect(() => {
    const handleFirstInteraction = () => {
      if (soundSystem.context && soundSystem.context.state === 'suspended') {
        soundSystem.context.resume();
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

  // Игровые звуки
  const gameAudio = {
    createBet: useCallback(() => playSound.createBet(), []),
    acceptBet: useCallback(() => playSound.acceptBet(), []),
    selectMove: useCallback(() => playSound.selectMove(), []),
    reveal: useCallback(() => playSound.reveal(), []),
    victory: useCallback(() => playSound.victory(), []),
    defeat: useCallback(() => playSound.defeat(), []),
    draw: useCallback(() => playSound.draw(), [])
  };

  // Звуки действий с гемами
  const gemAudio = {
    buy: useCallback(() => playSound.buyGem(), []),
    sell: useCallback(() => playSound.sellGem(), []),
    gift: useCallback(() => playSound.giftGem(), [])
  };

  // Звуки интерфейса
  const uiAudio = {
    hover: useCallback(() => playSound.hover(), []),
    modalOpen: useCallback(() => playSound.modalOpen(), []),
    modalClose: useCallback(() => playSound.modalClose(), []),
    notification: useCallback(() => playSound.notification(), []),
    error: useCallback(() => playSound.error(), []),
    settings: useCallback(() => playSound.settings(), [])
  };

  // Звуки системы
  const systemAudio = {
    timerTick: useCallback(() => playSound.timerTick(), []),
    timerExpire: useCallback(() => playSound.timerExpire(), []),
    reward: useCallback(() => playSound.reward(), [])
  };

  // Настройки звука
  const soundSettings = {
    isEnabled: useCallback(() => soundSystem.getEnabled(), []),
    getVolume: useCallback(() => soundSystem.getVolume(), []),
    getVolumeLevel: useCallback(() => soundSystem.getVolumeLevel(), []),
    setEnabled: useCallback((enabled) => soundSystem.setEnabled(enabled), []),
    setVolume: useCallback((volume) => soundSystem.setVolume(volume), []),
    setVolumeLevel: useCallback((level) => soundSystem.setVolumeLevel(level), [])
  };

  return {
    // Группы звуков
    game: gameAudio,
    gem: gemAudio,
    ui: uiAudio,
    system: systemAudio,
    
    // Настройки
    settings: soundSettings,
    
    // Прямой доступ к playSound для особых случаев
    playSound
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