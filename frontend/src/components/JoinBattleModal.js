import React, { useState, useEffect } from 'react';
import { useGems } from './GemsContext';
import { useNotifications } from './NotificationContext';
import { calculateGemCombination } from '../utils/gemCombinationAlgorithms';
import GemSelectionStep from './GemSelectionStep';
import MoveSelectionStep from './MoveSelectionStep';
import BattleResultStep from './BattleResultStep';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';

const JoinBattleModal = ({ bet, user, onClose, onUpdateUser }) => {
  // Проверка обязательных пропсов
  if (!bet || !user || !onClose) {
    console.error('JoinBattleModal: Missing required props', { bet, user, onClose });
    return null;
  }

  // Основные константы
  const targetAmount = bet?.bet_amount || 0;
  const COMMISSION_RATE = 0.03; // 3%
  const isBotGame = bet?.is_bot_game || false; // Определяем, является ли это игрой с ботом
  const commissionAmount = isBotGame ? 0 : targetAmount * COMMISSION_RATE; // Для игр с ботами комиссия = 0

  // НОВАЯ АСИНХРОННАЯ АРХИТЕКТУРА - 3 шага для лучшего UX
  const [currentStep, setCurrentStep] = useState(1); // 1: выбор гемов, 2: выбор хода, 3: результат
  const [loading, setLoading] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(60); // 1-минутный таймер
  
  // Состояние countdown 3-2-1
  const [showCountdown, setShowCountdown] = useState(false);
  const [countdownNumber, setCountdownNumber] = useState(3);

  // Данные игрока
  const [selectedGems, setSelectedGems] = useState({});
  const [selectedMove, setSelectedMove] = useState('');
  const [battleResult, setBattleResult] = useState(null);
  const [hasJoinedGame, setHasJoinedGame] = useState(false); // Отслеживаем, присоединился ли игрок

  // Контексты
  const { gemsData = [], refreshInventory = () => {} } = useGems() || {};
  const { showSuccess, showError } = useNotifications() || {};

  // Конфигурация ходов
  const moves = [
    { id: 'rock', name: 'Rock', icon: '/Rock.svg' },
    { id: 'paper', name: 'Paper', icon: '/Paper.svg' },
    { id: 'scissors', name: 'Scissors', icon: '/Scissors.svg' }
  ];

  // ЛОГИКА ПРИСОЕДИНЕНИЯ К БИТВЕ
  const joinBattle = async () => {
    setLoading(true);
    
    try {
      console.log('🎮 === ASYNC BATTLE JOIN ===');
      console.log('🎮 Joining battle:', {
        gameId: bet.id,
        selectedMove: selectedMove,
        selectedGems: selectedGems,
        userId: user.id
      });
      
      // Присоединяемся к игре - система автоматически определит результат
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/games/${bet.id}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          move: selectedMove,
          gems: selectedGems
        })
      });
      
      // Отмечаем, что игрок присоединился к игре
      setHasJoinedGame(true);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка при присоединении к игре');
      }
      
      const result = await response.json();
      console.log('🎮 Join game response:', result);
      
      let battleOutcome = null;
      
      // Игра завершается мгновенно, API возвращает результат игры напрямую
      if (result.game_id && result.winner_id !== undefined) {
        console.log('🎮 Game completed immediately');
        
        battleOutcome = result.winner_id === user.id ? 'win' : 
                       (result.winner_id ? 'lose' : 'draw');
        
        // Сохраняем результат битвы
        setBattleResult({
          result: battleOutcome,
          opponentMove: result.creator_move,
          gameData: result
        });
        
      } else {
        throw new Error(`Неожиданная структура ответа API. Ожидались поля game_id и winner_id.`);
      }
      
      // Обновляем инвентарь и данные пользователя
      await refreshInventory();
      if (onUpdateUser) {
        onUpdateUser();
      }
      
      // 🔄 АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ LOBBY ПОСЛЕ ПРИСОЕДИНЕНИЯ К ИГРЕ
      const globalRefresh = getGlobalLobbyRefresh();
      globalRefresh.triggerLobbyRefresh();
      console.log('⚔️ Battle joined/completed - triggering lobby refresh');
      
      // Переходим к результату (шаг 3)
      setCurrentStep(3);
      
      // Показываем уведомление о результате
      const resultText = battleOutcome === 'win' ? 'Victory!' : 
                        (battleOutcome === 'lose' ? 'Defeat!' : 'Draw!');
      showSuccess(`Battle completed! ${resultText}`);
      
    } catch (error) {
      console.error('🚨 Async battle join error:', error);
      showError(error.message || 'Ошибка при присоединении к битве');
    } finally {
      setLoading(false);
    }
  };

  // Валидация перед запуском битвы
  const validateBeforeBattle = () => {
    // Проверяем выбор хода
    if (!selectedMove) {
      showError('Please select your move');
      return false;
    }
    
    // Проверяем выбор гемов
    if (Object.keys(selectedGems).length === 0) {
      showError('Please select gems to match opponent\'s bet');
      return false;
    }
    
    // Проверяем точность суммы гемов
    const totalGemValue = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
      const gem = gemsData.find(g => g.type === gemType);
      return sum + (gem ? gem.price * quantity : 0);
    }, 0);
    
    if (Math.abs(totalGemValue - targetAmount) > 0.01) {
      showError(`Selected gems value ($${totalGemValue.toFixed(2)}) must match opponent's bet ($${targetAmount.toFixed(2)})`);
      return false;
    }
    
    // Проверяем доступность гемов в инвентаре
    for (const [gemType, quantity] of Object.entries(selectedGems)) {
      const gem = gemsData.find(g => g.type === gemType);
      if (!gem) {
        showError(`Invalid gem type: ${gemType}`);
        return false;
      }
      
      if (gem.available_quantity < quantity) {
        showError(`Insufficient ${gem.name} gems. Available: ${gem.available_quantity}, Required: ${quantity}`);
        return false;
      }
    }
    
    // Проверяем комиссию против общего баланса (только для игр с людьми)
    if (!isBotGame) {
      const commissionRequired = targetAmount * 0.06;
      const totalBalance = user?.virtual_balance || 0;
      const frozenBalance = user?.frozen_balance || 0;
      const availableForSpending = totalBalance - frozenBalance;
      
      if (availableForSpending < commissionRequired) {
        showError(`Insufficient balance for commission. Required: $${commissionRequired.toFixed(2)}, Available: $${availableForSpending.toFixed(2)}`);
        return false;
      }
    }
    
    return true;
  };

  // Запуск битвы с анимированным обратным отсчетом 3-2-1
  const startBattle = async () => {
    // ВАЛИДАЦИЯ ДО COUNTDOWN - ЭТО КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ
    if (!validateBeforeBattle()) {
      return;
    }
    
    setLoading(true);
    
    // Показываем анимированный обратный отсчет 3-2-1
    setShowCountdown(true);
    setCountdownNumber(3);
    
    // Обратный отсчет с анимацией
    await new Promise(resolve => {
      let count = 3;
      const countdownInterval = setInterval(() => {
        if (count <= 1) {
          clearInterval(countdownInterval);
          setShowCountdown(false);
          resolve();
        } else {
          count--;
          setCountdownNumber(count);
        }
      }, 1000);
    });
    
    // Запускаем асинхронную битву
    await joinBattle();
  };

  // Таймер автозакрытия (1 минута) - только на первых двух шагах
  useEffect(() => {
    if (currentStep >= 3) {
      // Не запускаем таймер на шаге результата
      return;
    }
    
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          // Время истекло - закрываем модальное окно
          onClose();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [currentStep, onClose]);

  // Обработчик стратегий - NEW FRONTEND IMPLEMENTATION
  const handleStrategySelect = (strategy) => {
    setLoading(true);
    
    try {
      // Use new frontend algorithms
      const result = calculateGemCombination(strategy, gemsData, targetAmount);
      
      if (result.success) {
        // Convert result to internal format
        const autoSelected = {};
        result.combination.forEach(item => {
          autoSelected[item.type] = item.quantity;
        });
        
        setSelectedGems(autoSelected);
        
        const strategyNames = { small: 'Small', smart: 'Smart', big: 'Big' };
        showSuccess(result.message || `${strategyNames[strategy]} strategy: exact combination for $${targetAmount.toFixed(2)}`);
      } else {
        showError(result.message || 'Insufficient gems to create exact combination');
      }
    } catch (error) {
      console.error('Error with strategy selection:', error);
      showError(error.message || 'Error with automatic gem selection');
    } finally {
      setLoading(false);
    }
  };

  // Конфигурация шагов - 3 отдельных шага
  const steps = [
    { id: 1, name: 'Gem Selection', description: 'Select your gems' },
    { id: 2, name: 'Move Selection', description: 'Choose your move' },
    { id: 3, name: 'Battle Result', description: 'Battle result' }
  ];

  // Проверка доступности средств для оплаты комиссии (только для игр с людьми)
  const totalBalance = user?.virtual_balance || 0;
  const frozenBalance = user?.frozen_balance || 0; 
  const availableForSpending = totalBalance - frozenBalance;
  
  if (!isBotGame && availableForSpending < commissionAmount) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-surface-card border border-border-primary rounded-lg w-full max-w-md p-6">
          <h2 className="text-xl font-russo text-white mb-4">⚠️ Insufficient Funds</h2>
          <p className="text-text-secondary mb-4">
            You need at least ${commissionAmount.toFixed(2)} for commission (3%) to join this bet.
          </p>
          <p className="text-text-secondary mb-4">
            Balance: ${totalBalance.toFixed(2)} | Frozen: ${frozenBalance.toFixed(2)} | Available: ${availableForSpending.toFixed(2)}
          </p>
          <button
            onClick={onClose}
            className="w-full py-2 bg-red-600 text-white font-rajdhani font-bold rounded-lg hover:bg-red-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  // Проверка доступности гемов
  const totalAvailableGemValue = gemsData.reduce((sum, gem) => 
    sum + (gem.available_quantity * gem.price), 0
  );
  
  if (totalAvailableGemValue < targetAmount) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-surface-card border border-border-primary rounded-lg w-full max-w-md p-6">
          <h2 className="text-xl font-russo text-white mb-4">⚠️ Insufficient Gems</h2>
          <p className="text-text-secondary mb-4">
            You don't have enough gems to match this bet amount of ${targetAmount.toFixed(2)}.
          </p>
          <p className="text-text-secondary mb-4">
            Your total gem value: ${totalAvailableGemValue.toFixed(2)}
          </p>
          <button
            onClick={onClose}
            className="w-full py-2 bg-red-600 text-white font-rajdhani font-bold rounded-lg hover:bg-red-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  // Рендер текущего шага - 3 отдельных шага
  const renderCurrentStep = () => {
    // Вычисляем общую стоимость выбранных гемов
    const totalGemValue = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
      const gem = gemsData.find(g => g.type === gemType);
      return sum + (gem ? gem.price * quantity : 0);
    }, 0);

    switch (currentStep) {
      case 1:
        // Шаг 1: Выбор гемов
        return (
          <GemSelectionStep
            targetAmount={targetAmount}
            commissionAmount={commissionAmount}
            selectedGems={selectedGems}
            onSelectedGemsChange={setSelectedGems}
            gemsData={gemsData}
            loading={loading}
            onStrategySelect={handleStrategySelect}
            showError={showError}
          />
        );
      case 2:
        // Шаг 2: Выбор хода
        return (
          <MoveSelectionStep
            targetAmount={targetAmount}
            totalGemValue={totalGemValue}
            selectedMove={selectedMove}
            onSelectedMoveChange={setSelectedMove}
          />
        );
      case 3:
        // Шаг 3: Результат битвы
        return (
          <BattleResultStep
            battleResult={battleResult}
            selectedMove={selectedMove}
            targetAmount={targetAmount}
            totalGemValue={totalGemValue}
            commissionAmount={commissionAmount}
            playerData={{
              player: user,
              opponent: bet?.creator || battleResult?.gameData?.creator || { username: 'Opponent' }
            }}
            onClose={onClose}
          />
        );
      default:
        return <div className="p-4 text-white">Unknown Step</div>;
    }
  };

  // Проверка возможности перехода к следующему шагу
  const canGoNext = () => {
    const totalGemValue = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
      const gem = gemsData.find(g => g.type === gemType);
      return sum + (gem ? gem.price * quantity : 0);
    }, 0);
    
    switch (currentStep) {
      case 1:
        // Шаг 1: Проверяем что гемы выбраны и сумма точная
        return Object.keys(selectedGems).length > 0 && 
               Math.abs(totalGemValue - targetAmount) <= 0.01;
      case 2:
        // Шаг 2: Проверяем что ход выбран
        return selectedMove !== '';
      default:
        return false;
    }
  };

  // Навигация между шагами
  const goToNextStep = () => {
    if (currentStep === 2) {
      // На шаге 2 кнопка "Next" запускает битву
      startBattle();
    } else if (canGoNext()) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const goToPrevStep = () => {
    setCurrentStep(prev => Math.max(1, prev - 1));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
      {/* Анимированный обратный отсчет 3-2-1 */}
      {showCountdown && (
        <div className="fixed inset-0 z-60 flex items-center justify-center bg-black bg-opacity-95 backdrop-blur-sm">
          <div className="text-center">
            <div 
              key={countdownNumber}
              className="countdown-number text-white font-russo text-9xl transform transition-all duration-500"
              style={{
                filter: 'drop-shadow(0 0 30px rgba(255, 255, 255, 0.8))'
              }}
            >
              {countdownNumber}
            </div>
            <div className="text-white font-rajdhani text-2xl mt-8 opacity-90 animate-pulse">
              ⚔️ Starting Battle...
            </div>
            
            {/* Дополнительные визуальные эффекты */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <div className="w-96 h-96 border-2 border-white border-opacity-20 rounded-full animate-ping"></div>
                <div className="absolute inset-4 border border-accent-primary border-opacity-40 rounded-full animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div 
        className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-primary">
          <h2 className="text-white font-russo text-xl">Join Battle</h2>
          
          {/* Timer - только на первых двух шагах */}
          {currentStep <= 2 && (
            <div className={`flex items-center space-x-2 ${
              timeRemaining <= 15 ? 'text-red-400' : 'text-yellow-400'
            }`}>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className={`font-rajdhani font-bold text-lg ${
                timeRemaining <= 15 ? 'animate-pulse' : ''
              }`}>
                {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
              </span>
            </div>
          )}
          
          <button
            type="button"
            onClick={onClose}
            className="text-text-secondary hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Progress Steps */}
        <div className="p-4 border-b border-border-primary">
          <div className="flex items-center space-x-2">
            {steps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className={`flex-1 flex items-center space-x-2 ${
                  currentStep >= step.id ? 'text-accent-primary' : 'text-text-secondary'
                }`}>
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    currentStep >= step.id ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary'
                  }`}>
                    {step.id}
                  </div>
                  <span className="text-xs font-rajdhani hidden sm:block">{step.name}</span>
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-8 h-0.5 ${
                    currentStep > step.id ? 'bg-accent-primary' : 'bg-surface-sidebar'
                  }`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Time Warning - показываем когда остается мало времени */}
        {currentStep <= 2 && timeRemaining <= 15 && (
          <div className="px-4 py-2 bg-red-900 bg-opacity-20 border-b border-red-600">
            <div className="flex items-center space-x-2 text-red-400">
              <svg className="w-4 h-4 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="text-sm font-rajdhani font-bold animate-pulse">
                Warning: Only {timeRemaining} seconds remaining!
              </span>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-96">
          {renderCurrentStep()}
        </div>

        {/* Footer Navigation - только на первых двух шагах */}
        {currentStep <= 2 && (
          <div className="p-4 border-t border-border-primary">
            <div className="flex space-x-3">
              {currentStep > 1 && (
                <button
                  type="button"
                  onClick={goToPrevStep}
                  disabled={loading}
                  className="px-4 py-2 bg-surface-sidebar text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300 disabled:opacity-50"
                >
                  Back
                </button>
              )}
              
              <button
                type="button"
                onClick={goToNextStep}
                disabled={loading || !canGoNext()}
                className="flex-1 px-4 py-2 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:scale-105 transition-all duration-300 disabled:opacity-50"
              >
                {currentStep === 2 ? 'Start Battle!' : 'Next'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JoinBattleModal;