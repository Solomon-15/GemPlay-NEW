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
  
  // Состояние ожидания результата (polling)
  const [isWaitingForResult, setIsWaitingForResult] = useState(false);

  // Контексты
  const { gemsData = [], refreshInventory = () => {} } = useGems() || {};
  const { showSuccess, showError } = useNotifications() || {};

  // Функция polling для ожидания завершения игры
  const pollGameResult = async (gameId, maxAttempts = 30) => {
    console.log('🔄 Starting game polling:', { gameId, maxAttempts });
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        console.log(`🔄 Polling attempt ${attempt}/${maxAttempts}`);
        
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/games/${gameId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        if (!response.ok) {
          console.warn(`⚠️ Polling attempt ${attempt} failed:`, response.status);
          continue;
        }
        
        const gameData = await response.json();
        console.log(`🔄 Polling result ${attempt}:`, {
          status: gameData.status,
          hasWinnerId: 'winner_id' in gameData,
          hasCreatorMove: 'creator_move' in gameData,
          hasJoinerMove: 'joiner_move' in gameData
        });
        
        // Проверяем, завершена ли игра
        if (gameData.status === 'COMPLETED' || gameData.status === 'FINISHED') {
          console.log('✅ Game completed! Final data:', gameData);
          return gameData;
        }
        
        // Ждем 2 секунды перед следующей попыткой
        await new Promise(resolve => setTimeout(resolve, 2000));
        
      } catch (error) {
        console.error(`🚨 Polling attempt ${attempt} error:`, error);
      }
    }
    
    console.error('🚨 Polling timeout - game did not complete in time');
    throw new Error('Game did not complete in time. Please check the game manually.');
  };

  // Функция для проверки логики Rock Paper Scissors
  const getRPSResult = (playerMove, opponentMove) => {
    console.log('🎯 RPS Logic Check:', {
      input: {
        player: playerMove,
        opponent: opponentMove
      }
    });
    
    // Нормализуем ходы к нижнему регистру
    const player = playerMove?.toLowerCase();
    const opponent = opponentMove?.toLowerCase();
    
    // Проверяем ничью
    if (player === opponent) {
      console.log('🎯 RPS Result: DRAW (same moves)');
      return 'draw';
    }
    
    // Правила Rock-Paper-Scissors
    // rock > scissors, scissors > paper, paper > rock
    const winningCombos = {
      'rock': 'scissors',     // rock beats scissors
      'scissors': 'paper',    // scissors beats paper  
      'paper': 'rock'         // paper beats rock
    };
    
    const playerWins = winningCombos[player] === opponent;
    const result = playerWins ? 'win' : 'lose';
    
    console.log('🎯 RPS Result:', {
      player: player,
      opponent: opponent, 
      playerBeats: winningCombos[player],
      playerWins: playerWins,
      result: result,
      explanation: playerWins ? 
        `${player} beats ${opponent}` : 
        `${opponent} beats ${player}`
    });
    
    return result;
  };

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
      console.log('🎮 === STARTING BATTLE DEBUG ===');
      console.log('🎮 Pre-API Check:', {
        gameId: bet.id,
        selectedMove: selectedMove,
        selectedGems: selectedGems,
        userId: user.id,
        userName: user.username,
        betData: bet
      });
      
      const apiUrl = `${process.env.REACT_APP_BACKEND_URL}/api/games/${bet.id}/join`;
      const requestBody = {
        move: selectedMove,
        gems: selectedGems
      };
      
      console.log('🎮 API Request:', {
        url: apiUrl,
        method: 'POST',
        body: requestBody
      });
      
      // Вызов API для присоединения к игре
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(requestBody)
      });
      
      console.log('🎮 API Response Status:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        console.log('🚨 API Error Response:', {
          status: response.status,
          statusText: response.statusText,
          errorData: errorData,
          possibleCauses: [
            'User already in another game',
            'Game not found',
            'Game already completed',
            'Invalid move or gems'
          ]
        });
        throw new Error(errorData.detail || 'Ошибка при присоединении к игре');
      }

      // Переменная для финального результата
      let result;
      
      const joinResult = await response.json();
      
      // DEBUG: подробный анализ JOIN ответа API
      console.log('🎮 === JOIN API SUCCESS RESPONSE ===');
      console.log('🎮 Join API Response:', joinResult);
      console.log('🎮 Join Response Analysis:', {
        hasWinnerId: 'winner_id' in joinResult,
        status: joinResult.status,
        hasMessage: 'message' in joinResult,
        needsPolling: joinResult.status === 'REVEAL' || joinResult.status === 'WAITING'
      });
      
      // Если игра еще не завершена - начинаем polling
      if (joinResult.status === 'REVEAL' || joinResult.status === 'WAITING') {
        console.log('🔄 Game not completed yet, starting polling...');
        
        // Показываем индикатор ожидания
        setIsWaitingForResult(true);
        showSuccess('Game joined! Waiting for opponent to reveal...');
        
        // Ждем завершения игры через polling
        const finalGameData = await pollGameResult(bet.id);
        
        // Скрываем индикатор ожидания
        setIsWaitingForResult(false);
        
        // Анализируем финальные данные
        console.log('🎮 === FINAL GAME DATA ===');
        console.log('🎮 Final Game Data:', finalGameData);
        
        // Используем финальные данные вместо JOIN результата
        result = finalGameData;
        
      } else {
        // Игра уже завершена сразу после JOIN
        console.log('🎮 Game completed immediately after join');
        result = joinResult;
      }
      
      // Определяем ходы игроков из финальных данных
      const playerMove = selectedMove;
      const opponentMove = result.creator_move || result.opponent_move;
      
      console.log('🎮 === FINAL MOVES ANALYSIS ===');
      console.log('🎮 Final Moves Analysis:', {
        playerMove: playerMove,
        opponentMove: opponentMove,
        userId: user.id,
        winnerId: result.winner_id,
        creatorId: result.creator_id || result.creator?.id,
        gameStatus: result.status,
        hasValidMoves: !!playerMove && !!opponentMove
      });
      
      // Проверяем, что у нас есть все необходимые данные
      if (!opponentMove) {
        console.error('🚨 Missing opponent move in final result!');
        throw new Error('Game completed but opponent move is missing');
      }
      
      // Проверяем логику RPS на клиенте
      const clientRPSResult = getRPSResult(playerMove, opponentMove);
      
      // Определяем результат битвы по API
      const apiResult = result.winner_id === user.id ? 'win' : 
                       (result.winner_id ? 'lose' : 'draw');
      
      console.log('🎮 === BATTLE RESULT COMPARISON ===');
      console.log('🎮 Results Comparison:', {
        apiResult: apiResult,
        clientRPSResult: clientRPSResult,
        match: apiResult === clientRPSResult,
        winnerFromAPI: result.winner_id,
        currentUserId: user.id,
        isUserWinner: result.winner_id === user.id,
        explanation: apiResult === clientRPSResult ? 'MATCH ✅' : 'MISMATCH ⚠️'
      });
      
      if (apiResult !== clientRPSResult) {
        console.warn('⚠️ MISMATCH: API result differs from client RPS logic!');
        console.warn('⚠️ This could indicate a server-side logic issue');
      } else {
        console.log('✅ Results match! RPS logic is consistent');
      }
      
      const battleOutcome = apiResult; // Используем результат API
      
      // Сохраняем результат битвы
      setBattleResult({
        result: battleOutcome,
        opponentMove: opponentMove,
        gameData: result
      });
      
      console.log('🎮 === FINAL BATTLE RESULT ===');
      console.log('🎮 Final Result Saved:', {
        result: battleOutcome,
        playerMove: playerMove,
        opponentMove: opponentMove,
        gameId: result.id || bet.id,
        timestamp: new Date().toISOString()
      });
      console.log('🎮 === END BATTLE DEBUG ===');
      
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
      console.error('🚨 === BATTLE ERROR ===');
      console.error('🚨 Error Details:', {
        message: error.message,
        stack: error.stack,
        gameId: bet.id,
        userId: user.id,
        selectedMove: selectedMove,
        timestamp: new Date().toISOString(),
        isPollingTimeout: error.message.includes('did not complete in time'),
        isPossibleServerIssue: error.message.includes('Missing opponent move')
      });
      
      // Разные сообщения в зависимости от типа ошибки
      if (error.message.includes('did not complete in time')) {
        showError('Game is taking longer than expected. Please check the lobby for updates.');
      } else if (error.message.includes('Missing opponent move')) {
        showError('Game completed but data is incomplete. Please refresh and check results.');
      } else {
        showError(error.message || 'Ошибка при запуске битвы');
      }
      
      console.error('🚨 === END ERROR ===');
      
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
        // Если ждем результат - показываем индикатор ожидания
        if (isWaitingForResult) {
          return (
            <div className="p-8 text-center space-y-6">
              <div className="text-white font-russo text-2xl mb-4">
                ⚔️ Battle in Progress
              </div>
              
              <div className="flex justify-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-accent-primary"></div>
              </div>
              
              <div className="text-text-secondary">
                <div className="font-rajdhani text-lg mb-2">Waiting for opponent to reveal...</div>
                <div className="text-sm">This may take up to 60 seconds</div>
              </div>
              
              <div className="bg-surface-sidebar rounded-lg p-4">
                <div className="text-white font-rajdhani font-bold mb-2">Your Move</div>
                <div className="flex justify-center">
                  <img 
                    src={moves.find(m => m.id === selectedMove)?.icon} 
                    alt={selectedMove} 
                    className="w-12 h-12" 
                  />
                </div>
                <div className="text-accent-primary font-rajdhani capitalize font-bold mt-2">
                  {moves.find(m => m.id === selectedMove)?.name}
                </div>
              </div>
            </div>
          );
        }
        
        // Показываем результат только когда получили финальные данные
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