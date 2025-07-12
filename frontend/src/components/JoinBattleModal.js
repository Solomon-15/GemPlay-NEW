import React, { useState } from 'react';
import { useGems } from './GemsContext';
import { useNotifications } from './NotificationContext';
import GemSelectionStep from './GemSelectionStep';
import MoveSelectionStep from './MoveSelectionStep';
import BattleResultStep from './BattleResultStep';

// Компоненты шагов (создадим их далее)
// import RevealStep from './RevealStep';

const JoinBattleModal = ({ bet, user, onClose, onUpdateUser }) => {
  // ВРЕМЕННЫЙ ЛОГ ДЛЯ ОТЛАДКИ
  const debugOnClose = (...args) => {
    console.log('🚨 JoinBattleModal onClose called!', { 
      stack: new Error().stack,
      args,
      timestamp: new Date().toISOString()
    });
    onClose(...args);
  };
  // Проверка обязательных пропсов
  if (!bet || !user || !onClose) {
    console.error('JoinBattleModal: Missing required props', { bet, user, onClose });
    return null;
  }

  // Основные константы
  const targetAmount = bet?.bet_amount || 0;
  const COMMISSION_RATE = 0.06; // 6%
  const commissionAmount = targetAmount * COMMISSION_RATE;

  // Состояние модального окна
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Таймер для автозакрытия (60 секунд)
  const [timeRemaining, setTimeRemaining] = useState(60);

  // Данные шагов
  const [selectedGems, setSelectedGems] = useState({});
  const [selectedMove, setSelectedMove] = useState('');
  const [battleResult, setBattleResult] = useState(null);
  
  // Состояние для анимированного обратного отсчета
  const [showCountdown, setShowCountdown] = useState(false);
  const [countdownNumber, setCountdownNumber] = useState(3);

  // Контексты
  const { gemsData = [], refreshInventory = () => {} } = useGems() || {};
  const { showSuccess, showError } = useNotifications() || {};

  // Таймер автозакрытия
  React.useEffect(() => {
    if (currentStep >= 3) {
      // Не запускаем таймер на шагах результата
      return;
    }
    
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          // Время истекло - закрываем модальное окно
          debugOnClose();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [currentStep]); // Перезапускаем при смене шага

  // Обработчик стратегий
  const handleStrategySelect = async (strategy) => {
    setLoading(true);
    
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/gems/calculate-combination`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          bet_amount: targetAmount,
          strategy: strategy
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка при расчете комбинации гемов');
      }
      
      const result = await response.json();
      
      if (result.success && result.combinations && Array.isArray(result.combinations)) {
        // Преобразуем ответ API в внутренний формат
        const autoSelected = {};
        result.combinations.forEach(combo => {
          if (combo && combo.type && combo.quantity) {
            autoSelected[combo.type] = combo.quantity;
          }
        });
        
        setSelectedGems(autoSelected);
        
        const strategyNames = { small: 'Small', smart: 'Smart', big: 'Big' };
        showSuccess(`${strategyNames[strategy]} стратегия: точная комбинация на сумму $${targetAmount.toFixed(2)}`);
      } else {
        showError(result.message || 'Недостаточно гемов для создания точной комбинации');
      }
    } catch (error) {
      console.error('Error with strategy selection:', error);
      showError(error.message || 'Ошибка при автоматическом подборе гемов');
    } finally {
      setLoading(false);
    }
  };

  // Конфигурация шагов
  const steps = [
    { id: 1, name: 'Gem Selection', description: 'Select your gems' },
    { id: 2, name: 'Move', description: 'Choose your move' },
    { id: 3, name: 'Battle', description: 'Battle result' },
    { id: 4, name: 'Reveal', description: 'Reveal move' }
  ];

  // Проверка доступности средств
  const availableBalance = (user?.virtual_balance || 0) - (user?.frozen_balance || 0);
  if (availableBalance < commissionAmount) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-surface-card border border-border-primary rounded-lg w-full max-w-md p-6">
          <h2 className="text-xl font-russo text-white mb-4">⚠️ Insufficient Funds</h2>
          <p className="text-text-secondary mb-4">
            You need at least ${commissionAmount.toFixed(2)} for commission (6%) to join this bet.
          </p>
          <p className="text-text-secondary mb-4">
            Available: ${availableBalance.toFixed(2)} | Required: ${commissionAmount.toFixed(2)}
          </p>
          <button
            onClick={debugOnClose}
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
            onClick={debugOnClose}
            className="w-full py-2 bg-red-600 text-white font-rajdhani font-bold rounded-lg hover:bg-red-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  // Навигация между шагами
  const goToNextStep = () => {
    if (currentStep === 2) {
      // На втором шаге "Start Battle!" должен запустить битву
      startBattle();
    } else if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
      // Сбрасываем таймер при переходе на новый шаг
      setTimeRemaining(60);
    }
  };

  const goToPrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      // Сбрасываем таймер при возврате на предыдущий шаг
      setTimeRemaining(60);
    }
  };

  // Запуск битвы с анимированным обратным отсчетом
  const startBattle = async () => {
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
    
    // Переходим к шагу результата
    setCurrentStep(3);
    
    try {
      // DEBUG: проверяем данные перед API вызовом
      console.log('🎮 Starting battle with:', {
        gameId: bet.id,
        selectedMove,
        selectedGems,
        user: user.id
      });
      
      // Вызов API для присоединения к игре
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/games/${bet.id}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          move: selectedMove,
          gems: selectedGems  // Добавляем выбранные гемы
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка при присоединении к игре');
      }
      
      const result = await response.json();
      
      // DEBUG: проверяем ответ API
      console.log('🎮 API Response:', result);
      
      // Определяем результат битвы
      const battleOutcome = result.winner_id === user.id ? 'win' : 
                           (result.winner_id ? 'lose' : 'draw');
      
      // DEBUG: Проверяем логику Rock Paper Scissors
      const playerMove = selectedMove;
      const opponentMove = result.creator_move;
      const expectedResult = getRPSResult(playerMove, opponentMove);
      
      console.log('🎮 Battle Logic Check:', {
        playerMove,
        opponentMove,
        apiResult: battleOutcome,
        expectedResult,
        winnerFromAPI: result.winner_id,
        currentUserId: user.id
      });
      
      // Сохраняем результат битвы
      setBattleResult({
        result: battleOutcome,
        opponentMove: result.creator_move,
        gameData: result
      });
      
      // Обновляем инвентарь и данные пользователя
      await refreshInventory();
      if (onUpdateUser) {
        onUpdateUser();
      }
      
      // Показываем уведомление о результате
      const resultText = battleOutcome === 'win' ? 'Победа!' : 
                        (battleOutcome === 'lose' ? 'Поражение!' : 'Ничья!');
      showSuccess(`Игра завершена! ${resultText}`);
      
    } catch (error) {
      console.error('Error starting battle:', error);
      showError(error.message || 'Ошибка при запуске битвы');
      setCurrentStep(2); // Возвращаемся к выбору хода при ошибке
    } finally {
      setLoading(false);
    }
  };

  // Рендер текущего шага
  const renderCurrentStep = () => {
    // Вычисляем общую стоимость выбранных гемов
    const totalGemValue = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
      const gem = gemsData.find(g => g.type === gemType);
      return sum + (gem ? gem.price * quantity : 0);
    }, 0);

    switch (currentStep) {
      case 1:
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
        return (
          <MoveSelectionStep
            targetAmount={targetAmount}
            totalGemValue={totalGemValue}
            selectedMove={selectedMove}
            onSelectedMoveChange={setSelectedMove}
          />
        );
      case 3:
        return (
          <BattleResultStep
            battleResult={battleResult}
            selectedMove={selectedMove}
            targetAmount={targetAmount}
            totalGemValue={totalGemValue}
            commissionAmount={commissionAmount}
            playerData={{
              player: user,
              opponent: battleResult?.gameData?.creator || { username: 'Opponent' }
            }}
            onClose={debugOnClose}
          />
        );
      case 4:
        // return <RevealStep ... />;
        return <div className="p-4 text-white">Reveal Step (TODO)</div>;
      default:
        return <div className="p-4 text-white">Unknown Step</div>;
    }
  };

  // Проверка возможности перехода на следующий шаг
  const canGoNext = () => {
    switch (currentStep) {
      case 1:
        // Проверить выбранные гемы и точность суммы
        const totalGemValue = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
          const gem = gemsData.find(g => g.type === gemType);
          return sum + (gem ? gem.price * quantity : 0);
        }, 0);
        
        return Object.keys(selectedGems).length > 0 && Math.abs(totalGemValue - targetAmount) <= 0.01;
      case 2:
        // Проверить выбранный ход
        return selectedMove !== '';
      default:
        return false;
    }
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
          {currentStep < 3 && (
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
            onClick={debugOnClose}
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
        {currentStep < 3 && timeRemaining <= 15 && (
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

        {/* Footer Navigation */}
        {currentStep < 3 && !loading && (
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