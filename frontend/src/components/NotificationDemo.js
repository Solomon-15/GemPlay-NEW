import React from 'react';
import { useNotifications } from './NotificationContext';

const NotificationDemo = () => {
  const { 
    showSuccess, 
    showError, 
    showWarning, 
    showInfo,
    showSuccessRU,
    showErrorRU,
    showWarningRU,
    showInfoRU 
  } = useNotifications();

  const handleBetCreated = () => {
    showSuccess('Bet created! $6.00 (6%) frozen until game completion.', { duration: 7000 });
  };

  const handleBetCreatedRU = () => {
    showSuccessRU('Ставка создана! $6.00 (6%) заморожено до завершения игры.', { duration: 7000 });
  };

  const handleGameWon = () => {
    showSuccess('Congratulations! You won the game and earned $25.50!', { duration: 6000 });
  };

  const handleGameWonRU = () => {
    showSuccessRU('Поздравляем! Вы выиграли игру и получили $25.50!', { duration: 6000 });
  };

  const handleInsufficientFunds = () => {
    showError('Insufficient funds. Please add balance to your account.', { duration: 5000 });
  };

  const handleInsufficientFundsRU = () => {
    showErrorRU('Недостаточно средств. Пожалуйста, пополните баланс.', { duration: 5000 });
  };

  const handleGameTimeout = () => {
    showWarning('Game will timeout in 30 seconds. Please make your move!', { duration: 4000 });
  };

  const handleGameTimeoutRU = () => {
    showWarningRU('Игра завершится через 30 секунд. Сделайте свой ход!', { duration: 4000 });
  };

  const handleSystemMaintenance = () => {
    showInfo('System maintenance scheduled for tonight at 2 AM UTC.', { duration: 8000 });
  };

  const handleSystemMaintenanceRU = () => {
    showInfoRU('Плановое обслуживание системы сегодня в 02:00 UTC.', { duration: 8000 });
  };

  return (
    <div className="p-8 space-y-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-russo text-white mb-8">Notification System Demo</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* English Notifications */}
          <div className="bg-surface-card p-6 rounded-lg border border-border-primary">
            <h2 className="text-xl font-russo text-accent-primary mb-4">English (User Interface)</h2>
            <div className="space-y-3">
              <button
                onClick={handleBetCreated}
                className="w-full px-4 py-2 bg-success rounded-lg text-white font-rajdhani hover:bg-success/80 transition-colors"
              >
                Show Bet Created (Success)
              </button>
              
              <button
                onClick={handleGameWon}
                className="w-full px-4 py-2 bg-success rounded-lg text-white font-rajdhani hover:bg-success/80 transition-colors"
              >
                Show Game Won (Success)
              </button>
              
              <button
                onClick={handleInsufficientFunds}
                className="w-full px-4 py-2 bg-error rounded-lg text-white font-rajdhani hover:bg-error/80 transition-colors"
              >
                Show Insufficient Funds (Error)
              </button>
              
              <button
                onClick={handleGameTimeout}
                className="w-full px-4 py-2 bg-warning rounded-lg text-bg-primary font-rajdhani hover:bg-warning/80 transition-colors"
              >
                Show Game Timeout (Warning)
              </button>
              
              <button
                onClick={handleSystemMaintenance}
                className="w-full px-4 py-2 bg-info rounded-lg text-white font-rajdhani hover:bg-info/80 transition-colors"
              >
                Show System Info (Info)
              </button>
            </div>
          </div>

          {/* Russian Notifications */}
          <div className="bg-surface-card p-6 rounded-lg border border-border-primary">
            <h2 className="text-xl font-russo text-accent-primary mb-4">Russian (Admin Panel)</h2>
            <div className="space-y-3">
              <button
                onClick={handleBetCreatedRU}
                className="w-full px-4 py-2 bg-success rounded-lg text-white font-rajdhani hover:bg-success/80 transition-colors"
              >
                Показать создание ставки (Успех)
              </button>
              
              <button
                onClick={handleGameWonRU}
                className="w-full px-4 py-2 bg-success rounded-lg text-white font-rajdhani hover:bg-success/80 transition-colors"
              >
                Показать выигрыш (Успех)
              </button>
              
              <button
                onClick={handleInsufficientFundsRU}
                className="w-full px-4 py-2 bg-error rounded-lg text-white font-rajdhani hover:bg-error/80 transition-colors"
              >
                Показать нехватку средств (Ошибка)
              </button>
              
              <button
                onClick={handleGameTimeoutRU}
                className="w-full px-4 py-2 bg-warning rounded-lg text-bg-primary font-rajdhani hover:bg-warning/80 transition-colors"
              >
                Показать таймаут игры (Предупреждение)
              </button>
              
              <button
                onClick={handleSystemMaintenanceRU}
                className="w-full px-4 py-2 bg-info rounded-lg text-white font-rajdhani hover:bg-info/80 transition-colors"
              >
                Показать системную информацию (Информация)
              </button>
            </div>
          </div>
        </div>

        <div className="mt-8 bg-surface-card p-6 rounded-lg border border-border-primary">
          <h3 className="text-lg font-russo text-accent-primary mb-4">Usage Examples</h3>
          <div className="space-y-4 text-text-secondary font-roboto">
            <div>
              <h4 className="text-white font-medium mb-2">In React Components:</h4>
              <pre className="bg-surface-sidebar p-3 rounded text-sm overflow-x-auto">
{`import { useNotifications } from './NotificationContext';

const MyComponent = () => {
  const { showSuccess, showError, showWarning, showInfo } = useNotifications();
  
  const handleSuccess = () => {
    showSuccess('Operation completed successfully!');
  };
  
  const handleError = () => {
    showError('Something went wrong!');
  };
  
  // For admin panel (Russian)
  const handleSuccessRU = () => {
    showSuccessRU('Операция выполнена успешно!');
  };
};`}
              </pre>
            </div>
            
            <div>
              <h4 className="text-white font-medium mb-2">Features:</h4>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>Auto-dismiss after 5 seconds (configurable)</li>
                <li>Manual dismiss with X button</li>
                <li>Slide-in animation from right</li>
                <li>Different icons for each notification type</li>
                <li>Green border styling matching the app theme</li>
                <li>Support for both English and Russian</li>
                <li>Responsive design</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationDemo;