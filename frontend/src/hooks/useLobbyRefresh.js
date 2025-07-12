import { useCallback, useRef } from 'react';

// Глобальный хук для обновления Lobby в реальном времени
export const useLobbyRefresh = () => {
  const refreshCallbacks = useRef(new Set());

  const registerRefreshCallback = useCallback((callback) => {
    refreshCallbacks.current.add(callback);
    
    // Возвращаем функцию для отписки
    return () => {
      refreshCallbacks.current.delete(callback);
    };
  }, []);

  const triggerLobbyRefresh = useCallback(() => {
    // Вызываем все зарегистрированные колбэки для обновления
    refreshCallbacks.current.forEach(callback => {
      try {
        callback();
      } catch (error) {
        console.error('Error in lobby refresh callback:', error);
      }
    });
  }, []);

  return {
    registerRefreshCallback,
    triggerLobbyRefresh
  };
};

// Глобальный экземпляр для использования во всем приложении
let globalLobbyRefresh = null;

export const getGlobalLobbyRefresh = () => {
  if (!globalLobbyRefresh) {
    const refreshCallbacks = new Set();

    globalLobbyRefresh = {
      registerRefreshCallback: (callback) => {
        refreshCallbacks.add(callback);
        return () => {
          refreshCallbacks.delete(callback);
        };
      },
      
      triggerLobbyRefresh: () => {
        refreshCallbacks.forEach(callback => {
          try {
            callback();
          } catch (error) {
            console.error('Error in global lobby refresh callback:', error);
          }
        });
      }
    };
  }
  
  return globalLobbyRefresh;
};