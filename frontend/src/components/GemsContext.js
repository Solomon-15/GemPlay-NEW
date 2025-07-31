import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GemsContext = createContext();

export const useGems = () => {
  const context = useContext(GemsContext);
  if (!context) {
    throw new Error('useGems must be used within a GemsProvider');
  }
  return context;
};

export const GemsProvider = ({ children }) => {
  const [gemsData, setGemsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchInventoryData();
    
    const globalRefresh = getGlobalLobbyRefresh();
    const unregister = globalRefresh.registerRefreshCallback(() => {
      console.log('💎 GemsContext auto-refresh triggered by global operation');
      fetchInventoryData();
    });
    
    return () => {
      unregister();
    };
  }, []);

  // Single source of truth: Inventory API only
  const fetchInventoryData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        console.warn('No token found, using default gem definitions');
        setGemsData(getDefaultGemDefinitions());
        setLoading(false);
        return;
      }

      // PRIMARY SOURCE: Get actual inventory from backend
      const inventoryResponse = await axios.get(`${API}/gems/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const userGems = inventoryResponse.data || [];
      console.log('💎 Raw inventory data received:', userGems.length, 'gems');
      
      // Get gem definitions for types/prices
      const definitionsResponse = await axios.get(`${API}/gems/definitions`);
      const definitions = definitionsResponse.data || [];
      console.log('💎 Raw definitions data received:', definitions.length, 'definitions');
      
      // Create complete gem data structure
      const completeGemsData = definitions.map(def => {
        const userGem = userGems.find(gem => gem.type === def.type);
        
        const gemData = {
          // Core gem definition
          type: def.type,
          name: def.name,
          price: def.price,
          color: def.color,
          icon: getGemIconPath(def.type),
          rarity: def.rarity,
          
          // User's inventory data (ONLY source of truth)
          quantity: userGem ? userGem.quantity : 0,
          frozen_quantity: userGem ? userGem.frozen_quantity : 0,
          available_quantity: userGem ? (userGem.quantity - userGem.frozen_quantity) : 0,
          
          // Computed values
          total_value: userGem ? (userGem.quantity * def.price) : 0,
          available_value: userGem ? ((userGem.quantity - userGem.frozen_quantity) * def.price) : 0,
          frozen_value: userGem ? (userGem.frozen_quantity * def.price) : 0,
          
          // Status flags
          has_gems: userGem ? userGem.quantity > 0 : false,
          has_available: userGem ? (userGem.quantity - userGem.frozen_quantity) > 0 : false,
          
          // Metadata
          last_updated: userGem ? userGem.updated_at : null
        };
        
        // Log critical gem data for debugging
        if (def.type === 'Magic') {
          console.log(`💎 Magic gem data constructed:`, {
            total: gemData.quantity,
            frozen: gemData.frozen_quantity,
            available: gemData.available_quantity,
            userGemExists: !!userGem,
            rawUserGem: userGem
          });
        }
        
        return gemData;
      });
      
      setGemsData(completeGemsData);
      setLastUpdate(new Date());
      setLoading(false);
      
    } catch (error) {
      console.error('Error fetching inventory data:', error);
      
      // Fallback to definitions only if inventory fails
      try {
        const definitionsResponse = await axios.get(`${API}/gems/definitions`);
        const definitions = definitionsResponse.data || [];
        
        const fallbackData = definitions.map(def => ({
          type: def.type,
          name: def.name,
          price: def.price,
          color: def.color,
          icon: getGemIconPath(def.type),
          rarity: def.rarity,
          quantity: 0,
          frozen_quantity: 0,
          available_quantity: 0,
          total_value: 0,
          available_value: 0,
          frozen_value: 0,
          has_gems: false,
          has_available: false,
          last_updated: null
        }));
        
        setGemsData(fallbackData);
      } catch (defError) {
        console.error('Error fetching gem definitions:', defError);
        setGemsData(getDefaultGemDefinitions());
      }
      
      setLoading(false);
    }
  };

  // Default gem definitions with proper icon paths
  const getDefaultGemDefinitions = () => [
    { 
      type: 'Ruby', name: 'Ruby', price: 1, color: '#ef4444', 
      icon: '/gems/gem-red.svg', rarity: 'common',
      quantity: 0, frozen_quantity: 0, available_quantity: 0,
      total_value: 0, available_value: 0, frozen_value: 0,
      has_gems: false, has_available: false, last_updated: null
    },
    { 
      type: 'Amber', name: 'Amber', price: 2, color: '#f97316', 
      icon: '/gems/gem-orange.svg', rarity: 'common',
      quantity: 0, frozen_quantity: 0, available_quantity: 0,
      total_value: 0, available_value: 0, frozen_value: 0,
      has_gems: false, has_available: false, last_updated: null
    },
    { 
      type: 'Topaz', name: 'Topaz', price: 5, color: '#eab308', 
      icon: '/gems/gem-yellow.svg', rarity: 'uncommon',
      quantity: 0, frozen_quantity: 0, available_quantity: 0,
      total_value: 0, available_value: 0, frozen_value: 0,
      has_gems: false, has_available: false, last_updated: null
    },
    { 
      type: 'Emerald', name: 'Emerald', price: 10, color: '#22c55e', 
      icon: '/gems/gem-green.svg', rarity: 'rare',
      quantity: 0, frozen_quantity: 0, available_quantity: 0,
      total_value: 0, available_value: 0, frozen_value: 0,
      has_gems: false, has_available: false, last_updated: null
    },
    { 
      type: 'Aquamarine', name: 'Aquamarine', price: 25, color: '#06b6d4', 
      icon: '/gems/gem-cyan.svg', rarity: 'epic',
      quantity: 0, frozen_quantity: 0, available_quantity: 0,
      total_value: 0, available_value: 0, frozen_value: 0,
      has_gems: false, has_available: false, last_updated: null
    },
    { 
      type: 'Sapphire', name: 'Sapphire', price: 50, color: '#3b82f6', 
      icon: '/gems/gem-blue.svg', rarity: 'legendary',
      quantity: 0, frozen_quantity: 0, available_quantity: 0,
      total_value: 0, available_value: 0, frozen_value: 0,
      has_gems: false, has_available: false, last_updated: null
    },
    { 
      type: 'Magic', name: 'Magic', price: 100, color: '#a855f7', 
      icon: '/gems/gem-purple.svg', rarity: 'mythic',
      quantity: 0, frozen_quantity: 0, available_quantity: 0,
      total_value: 0, available_value: 0, frozen_value: 0,
      has_gems: false, has_available: false, last_updated: null
    }
  ];

  // Helper function to get correct icon path for gem type
  const getGemIconPath = (gemType) => {
    const iconMap = {
      'Ruby': '/gems/gem-red.svg',
      'Amber': '/gems/gem-orange.svg',
      'Topaz': '/gems/gem-yellow.svg',
      'Emerald': '/gems/gem-green.svg',
      'Aquamarine': '/gems/gem-cyan.svg',
      'Sapphire': '/gems/gem-blue.svg',
      'Magic': '/gems/gem-purple.svg'
    };
    return iconMap[gemType] || '/gems/gem-red.svg';
  };

  // CRITICAL: All operations must verify against current inventory
  const getGemByType = (gemType) => {
    return gemsData.find(gem => gem.type === gemType || gem.name === gemType);
  };

  const getGemValue = (gemType) => {
    const gem = getGemByType(gemType);
    return gem ? gem.price : 0;
  };

  const getGemIcon = (gemType) => {
    const gem = getGemByType(gemType);
    return gem ? gem.icon : '/gems/gem-red.svg';
  };

  // Get only available (non-frozen) gems for operations
  const getAvailableGems = () => {
    return gemsData.filter(gem => gem.has_available);
  };

  // Get all gems with quantities (including frozen)
  const getAllGemsWithQuantity = () => {
    return gemsData.filter(gem => gem.has_gems);
  };

  // Sort gems by price (ascending or descending)
  const getSortedGems = (orderBy = 'price', order = 'asc') => {
    const sortedGems = [...gemsData].sort((a, b) => {
      if (order === 'asc') {
        return a[orderBy] - b[orderBy];
      } else {
        return b[orderBy] - a[orderBy];
      }
    });
    return sortedGems;
  };

  // Calculate total portfolio value from inventory
  const getTotalPortfolioValue = () => {
    return gemsData.reduce((total, gem) => total + gem.total_value, 0);
  };

  // Calculate available (non-frozen) portfolio value
  const getAvailablePortfolioValue = () => {
    return gemsData.reduce((total, gem) => total + gem.available_value, 0);
  };

  // Calculate frozen portfolio value
  const getFrozenPortfolioValue = () => {
    return gemsData.reduce((total, gem) => total + gem.frozen_value, 0);
  };

  // CRITICAL: Refresh inventory data after any gem operation
  const refreshInventory = async () => {
    await fetchInventoryData();
  };

  // Check if user has enough gems for a specific operation
  // CRITICAL FIX: Always validate against current fresh data
  const validateGemOperation = (requiredGems) => {
    // Force fresh data check by using current gemsData directly
    const currentTimestamp = Date.now();
    console.log(`💎 Validating gem operation at ${currentTimestamp}:`, requiredGems);
    
    for (const [gemType, requiredQuantity] of Object.entries(requiredGems)) {
      const gem = gemsData.find(g => g.type === gemType || g.name === gemType);
      
      if (!gem) {
        console.error(`❌ Unknown gem type: ${gemType}`);
        return { valid: false, error: `Unknown gem type: ${gemType}` };
      }
      
      console.log(`💎 ${gemType}: Required ${requiredQuantity}, Available ${gem.available_quantity} (Total: ${gem.quantity}, Frozen: ${gem.frozen_quantity})`);
      
      if (gem.available_quantity < requiredQuantity) {
        const error = `Insufficient ${gemType} gems. Available: ${gem.available_quantity}, Required: ${requiredQuantity}`;
        console.error(`❌ ${error}`);
        return { 
          valid: false, 
          error 
        };
      }
    }
    
    console.log('✅ Gem operation validation passed');
    return { valid: true };
  };

  const contextValue = {
    // Raw inventory data (ONLY source of truth)
    gemsData,
    loading,
    lastUpdate,
    
    // Alias for backward compatibility
    gemsDefinitions: gemsData,
    
    // Core gem operations
    getGemByType,
    getGemValue,
    getGemIcon,
    
    // Filtered data
    getAvailableGems,
    getAllGemsWithQuantity,
    getSortedGems,
    
    // Portfolio calculations
    getTotalPortfolioValue,
    getAvailablePortfolioValue,
    getFrozenPortfolioValue,
    
    // Operations
    refreshInventory,
    validateGemOperation,
    
    // Icon helper
    getGemIconPath
  };

  return (
    <GemsContext.Provider value={contextValue}>
      {children}
    </GemsContext.Provider>
  );
};

export default GemsContext;