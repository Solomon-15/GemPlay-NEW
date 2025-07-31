import { useCallback } from 'react';
import { useGems } from '../components/GemsContext';

/**
 * Centralized data refresh hook
 * Ensures both user auth status and gems inventory are updated simultaneously
 * to prevent data desynchronization issues
 */
export const useDataRefresh = (onUpdateUser, showNotifications = false) => {
  const { refreshInventory } = useGems();

  const refreshAllData = useCallback(async () => {
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