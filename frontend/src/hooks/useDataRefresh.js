import { useCallback, useRef } from 'react';
import { useGems } from '../components/GemsContext';

/**
 * Centralized data refresh hook
 * Ensures both user auth status and gems inventory are updated simultaneously
 * to prevent data desynchronization issues
 */
export const useDataRefresh = (onUpdateUser, showNotifications = false) => {
  const { refreshInventory } = useGems();
  const lastRefreshTime = useRef(0);
  const THROTTLE_DELAY = 1000; // Prevent calls more than once per second

  const refreshAllData = useCallback(async () => {
    // Throttle to prevent excessive calls
    const now = Date.now();
    if (now - lastRefreshTime.current < THROTTLE_DELAY) {
      if (showNotifications) {
        console.log('🔄 Data refresh throttled (too frequent)');
      }
      return true;
    }
    lastRefreshTime.current = now;
    
    // Only log when explicitly requested
    if (showNotifications) {
      console.log('🔄 Starting centralized data refresh...');
    }
    
    try {
      // Execute both refreshes in parallel for better performance
      const promises = [];
      
      // Refresh user data (balance, user info, etc.)
      if (onUpdateUser) {
        promises.push(Promise.resolve(onUpdateUser()));
      }
      
      // Refresh gems inventory data
      promises.push(refreshInventory());
      
      await Promise.all(promises);
      
      // Only log when explicitly requested
      if (showNotifications) {
        console.log('✅ Centralized data refresh completed successfully');
      }
      
      return true;
    } catch (error) {
      console.error('❌ Error during centralized data refresh:', error);
      return false;
    }
  }, [onUpdateUser, refreshInventory, showNotifications]);

  const refreshWithDelay = useCallback(async (delay = 500) => {
    await refreshAllData();
    
    // Additional refresh after delay to ensure all backend operations are reflected
    setTimeout(async () => {
      await refreshAllData();
      // Only log when explicitly requested
      if (showNotifications) {
        console.log('🔄 Delayed data refresh completed');
      }
    }, delay);
  }, [refreshAllData, showNotifications]);

  return {
    refreshAllData,
    refreshWithDelay
  };
};

export default useDataRefresh;