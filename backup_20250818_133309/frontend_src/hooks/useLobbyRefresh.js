import { useCallback, useRef } from 'react';

export const useLobbyRefresh = () => {
  const refreshCallbacks = useRef(new Set());

  const registerRefreshCallback = useCallback((callback) => {
    refreshCallbacks.current.add(callback);
    
    return () => {
      refreshCallbacks.current.delete(callback);
    };
  }, []);

  const triggerLobbyRefresh = useCallback(() => {
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