import React, { useState } from 'react';
import { useGems } from './GemsContext';
import { useNotifications } from './NotificationContext';
import GemSelectionStep from './GemSelectionStep';
import MoveSelectionStep from './MoveSelectionStep';
import BattleResultStep from './BattleResultStep';

// Компоненты шагов (создадим их далее)
// import RevealStep from './RevealStep';

const JoinBattleModal = ({ bet, user, onClose, onUpdateUser }) => {
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

  // Данные шагов
  const [selectedGems, setSelectedGems] = useState({});
  const [selectedMove, setSelectedMove] = useState('');
  const [battleResult, setBattleResult] = useState(null);

  // Контексты
  const { gemsData = [], refreshInventory = () => {} } = useGems() || {};
  const { showSuccess, showError } = useNotifications() || {};

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

  // Навигация между шагами
  const goToNextStep = () => {
    if (currentStep === 2) {
      // На втором шаге "Start Battle!" должен запустить битву
      startBattle();
    } else if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const goToPrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Запуск битвы - реальная API логика
  const startBattle = async () => {
    setLoading(true);
    setCurrentStep(3); // Переход к шагу с результатом битвы
    
    try {
      // Вызов API для присоединения к игре
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/games/${bet.id}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          move: selectedMove
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка при присоединении к игре');
      }
      
      const result = await response.json();
      
      // Определяем результат битвы
      const battleOutcome = result.winner_id === user.id ? 'win' : 
                           (result.winner_id ? 'lose' : 'draw');
      
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
            onClose={onClose}
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
      <div 
        className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-primary">
          <h2 className="text-white font-russo text-xl">Join Battle</h2>
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