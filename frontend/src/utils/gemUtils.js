// Utility functions for gem-related operations and formatting
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Cache for gem prices to avoid repeated API calls
let gemPricesCache = null;
let cacheTimestamp = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

/**
 * Fetch gem prices from admin panel
 * @returns {Promise<Array>} Array of gem objects with prices
 */
export const fetchGemPrices = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API}/admin/gems`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    if (response.data && response.data.gems) {
      return response.data.gems;
    }
    return [];
  } catch (error) {
    console.error('Error fetching gem prices:', error);
    return [];
  }
};

/**
 * Get cached gem prices or fetch fresh ones
 * @returns {Promise<Array>} Array of gem objects with prices
 */
export const getGemPrices = async () => {
  const now = Date.now();
  
  // Return cached data if it's still fresh
  if (gemPricesCache && cacheTimestamp && (now - cacheTimestamp < CACHE_DURATION)) {
    return gemPricesCache;
  }
  
  // Fetch fresh data
  gemPricesCache = await fetchGemPrices();
  cacheTimestamp = now;
  
  return gemPricesCache;
};

/**
 * Clear gem prices cache (useful when gems are updated in admin panel)
 */
export const clearGemPricesCache = () => {
  gemPricesCache = null;
  cacheTimestamp = null;
};

/**
 * Convert dollar amount to gem display format
 * Uses $1 = 1 gem conversion and rounds to whole number
 * @param {number} dollarAmount - Dollar amount to convert
 * @returns {string} Formatted gem display (e.g., "15 Gems")
 */
export const formatDollarsAsGems = (dollarAmount) => {
  if (typeof dollarAmount !== 'number' || isNaN(dollarAmount)) {
    return '0 Gems';
  }
  
  // Since $1 = 1 gem, we convert directly and round to whole number
  const gemAmount = Math.round(dollarAmount);
  
  // Return singular or plural form
  return gemAmount === 1 ? '1 Gem' : `${gemAmount} Gems`;
};

/**
 * Convert dollar amount to just the gem number (without "Gems" text)
 * @param {number} dollarAmount - Dollar amount to convert
 * @returns {string} Just the number (e.g., "15")
 */
export const formatDollarsAsGemNumber = (dollarAmount) => {
  if (typeof dollarAmount !== 'number' || isNaN(dollarAmount)) {
    return '0';
  }
  
  return Math.round(dollarAmount).toString();
};

/**
 * Calculate total value of a gem combination
 * @param {Object} gemCombination - Object with gem types as keys and quantities as values
 * @param {Array} gemPrices - Array of gem price objects
 * @returns {number} Total dollar value
 */
export const calculateGemCombinationValue = (gemCombination, gemPrices) => {
  if (!gemCombination || !gemPrices) return 0;
  
  let totalValue = 0;
  
  for (const [gemType, quantity] of Object.entries(gemCombination)) {
    const gemInfo = gemPrices.find(gem => gem.name.toLowerCase() === gemType.toLowerCase());
    if (gemInfo && quantity > 0) {
      totalValue += gemInfo.price * quantity;
    }
  }
  
  return totalValue;
};

/**
 * Format a gem combination for display
 * @param {Object} gemCombination - Object with gem types as keys and quantities as values  
 * @returns {string} Formatted display (e.g., "2 Ruby + 3 Emerald")
 */
export const formatGemCombination = (gemCombination) => {
  if (!gemCombination || typeof gemCombination !== 'object') {
    return '—';
  }
  
  const parts = [];
  for (const [gemType, quantity] of Object.entries(gemCombination)) {
    if (quantity > 0) {
      parts.push(`${quantity} ${gemType}`);
    }
  }
  
  return parts.length > 0 ? parts.join(' + ') : '—';
};

/**
 * Get gem display color based on gem type
 * @param {string} gemType - Type of gem
 * @returns {string} CSS color class
 */
export const getGemColor = (gemType) => {
  const colorMap = {
    'ruby': 'text-red-400',
    'amber': 'text-yellow-400', 
    'topaz': 'text-orange-400',
    'emerald': 'text-green-400',
    'aquamarine': 'text-cyan-400',
    'sapphire': 'text-blue-400',
    'magic': 'text-purple-400'
  };
  
  return colorMap[gemType?.toLowerCase()] || 'text-gray-400';
};

/**
 * Enhanced bet amount formatter that uses gem prices
 * This is the main formatter that should be used throughout the app
 * @param {number|Object} betData - Either dollar amount or bet object with gem combination
 * @param {Array} gemPrices - Array of gem prices (optional, will fetch if not provided)
 * @returns {Promise<string>} Formatted gem display
 */
export const formatBetAmountAsGems = async (betData, gemPrices = null) => {
  try {
    // If no gem prices provided, fetch them
    if (!gemPrices) {
      gemPrices = await getGemPrices();
    }
    
    // If betData is just a number (dollar amount)
    if (typeof betData === 'number') {
      return formatDollarsAsGems(betData);
    }
    
    // If betData is an object with gem combination
    if (betData && typeof betData === 'object') {
      // Check if it has bet_amount field
      if (betData.bet_amount !== undefined) {
        return formatDollarsAsGems(betData.bet_amount);
      }
      
      // Check if it has gem combination fields
      if (betData.bet_gems || betData.gems) {
        const gems = betData.bet_gems || betData.gems;
        const totalValue = calculateGemCombinationValue(gems, gemPrices);
        return formatDollarsAsGems(totalValue);
      }
    }
    
    return '0 Gems';
  } catch (error) {
    console.error('Error formatting bet amount as gems:', error);
    return '0 Gems';
  }
};

/**
 * Preload gem prices for better performance
 * Call this on app startup or when gems might be needed
 */
export const preloadGemPrices = async () => {
  await getGemPrices();
};

// Constants
export const GEM_CONSTANTS = {
  DOLLAR_TO_GEM_RATIO: 1, // $1 = 1 gem
  DEFAULT_GEMS: ['Ruby', 'Amber', 'Topaz', 'Emerald', 'Aquamarine', 'Sapphire', 'Magic'],
  CACHE_DURATION: CACHE_DURATION
};