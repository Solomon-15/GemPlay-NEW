// Utility functions for currency formatting and virtual economy

/**
 * Format currency with proper separators
 * @param {number} amount - Amount to format
 * @param {boolean} showCents - Whether to show cents (default: false)
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount, showCents = false) => {
  if (typeof amount !== 'number' || isNaN(amount)) {
    return showCents ? '0,00' : '0';
  }
  
  // Round down (floor) for gem values to ensure integer display
  const roundedAmount = showCents ? amount : Math.floor(amount);
  
  const options = {
    minimumFractionDigits: showCents ? 2 : 0,
    maximumFractionDigits: showCents ? 2 : 0,
    useGrouping: true
  };
  
  return roundedAmount.toLocaleString('en-US', options).replace(/,/g, ' ').replace('.', ',');
};

/**
 * Format currency with $ symbol
 * @param {number} amount - Amount to format
 * @param {boolean} showCents - Whether to show cents (default: false)
 * @returns {string} Formatted currency string with $ symbol
 */
export const formatCurrencyWithSymbol = (amount, showCents = false) => {
  return `$${formatCurrency(amount, showCents)}`;
};

/**
 * Calculate commission amount
 * @param {number} amount - Base amount
 * @param {number} percentage - Commission percentage (e.g., 6 for 6%)
 * @returns {number} Commission amount
 */
export const calculateCommission = (amount, percentage) => {
  return (amount * percentage) / 100;
};

/**
 * Calculate total cost including commission
 * @param {number} baseAmount - Base amount
 * @param {number} commissionPercentage - Commission percentage
 * @returns {object} Object with baseAmount, commission, and total
 */
export const calculateTotalWithCommission = (baseAmount, commissionPercentage) => {
  const commission = calculateCommission(baseAmount, commissionPercentage);
  return {
    baseAmount,
    commission,
    total: baseAmount + commission
  };
};

/**
 * Calculate gem total value
 * @param {Array} gems - Array of gem objects with type, quantity, and price
 * @param {boolean} availableOnly - If true, calculate only available (non-frozen) gems
 * @returns {number} Total value
 */
export const calculateGemValue = (gems, availableOnly = false) => {
  return gems.reduce((total, gem) => {
    const quantity = availableOnly ? 
      (gem.quantity - (gem.frozen_quantity || 0)) : 
      gem.quantity;
    return total + (quantity * gem.price);
  }, 0);
};

/**
 * Validate if user has sufficient balance for operation
 * @param {object} user - User object with virtual_balance and frozen_balance
 * @param {number} requiredAmount - Required amount
 * @returns {object} Validation result with isValid and message
 */
export const validateBalance = (user, requiredAmount) => {
  const availableBalance = user.virtual_balance - (user.frozen_balance || 0);
  
  if (availableBalance < requiredAmount) {
    return {
      isValid: false,
      message: `Insufficient balance. Available: $${formatCurrency(availableBalance)}, Required: $${formatCurrency(requiredAmount)}`
    };
  }
  
  return {
    isValid: true,
    message: 'Balance sufficient'
  };
};

/**
 * Validate daily limit usage
 * @param {object} user - User object with daily_limit_used and daily_limit_max
 * @param {number} requestedAmount - Amount user wants to add
 * @returns {object} Validation result
 */
export const validateDailyLimit = (user, requestedAmount) => {
  const remainingLimit = user.daily_limit_max - user.daily_limit_used;
  
  if (requestedAmount > remainingLimit) {
    return {
      isValid: false,
      message: `Daily limit exceeded. Remaining: $${formatCurrency(remainingLimit)}`,
      remainingLimit
    };
  }
  
  return {
    isValid: true,
    message: 'Within daily limit',
    remainingLimit
  };
};

/**
 * Auto-select gems to match target amount
 * @param {Array} availableGems - Array of available gems with quantity and price
 * @param {number} targetAmount - Target amount to match
 * @returns {object} Selected gems and total value
 */
export const autoSelectGems = (availableGems, targetAmount) => {
  // Sort gems by price (ascending) for efficient selection
  const sortedGems = [...availableGems]
    .filter(gem => gem.quantity > gem.frozen_quantity)
    .sort((a, b) => a.price - b.price);
  
  const selectedGems = {};
  let currentTotal = 0;
  let remainingAmount = targetAmount;
  
  // First pass: try to match exactly
  for (const gem of sortedGems) {
    const availableQuantity = gem.quantity - gem.frozen_quantity;
    const maxPossible = Math.floor(remainingAmount / gem.price);
    const toUse = Math.min(availableQuantity, maxPossible);
    
    if (toUse > 0) {
      selectedGems[gem.type] = toUse;
      const value = toUse * gem.price;
      currentTotal += value;
      remainingAmount -= value;
      
      if (remainingAmount <= 0) break;
    }
  }
  
  // If we're still short, try to get as close as possible
  if (remainingAmount > 0 && currentTotal < targetAmount) {
    for (const gem of sortedGems) {
      const availableQuantity = gem.quantity - gem.frozen_quantity;
      const alreadyUsed = selectedGems[gem.type] || 0;
      const canUseMore = availableQuantity - alreadyUsed;
      
      if (canUseMore > 0 && gem.price <= remainingAmount) {
        selectedGems[gem.type] = (selectedGems[gem.type] || 0) + 1;
        currentTotal += gem.price;
        remainingAmount -= gem.price;
        
        if (remainingAmount <= 0) break;
      }
    }
  }
  
  return {
    selectedGems,
    totalValue: currentTotal,
    remainingAmount: Math.max(0, targetAmount - currentTotal)
  };
};

/**
 * Format time remaining for bet expiration
 * @param {Date} expiresAt - Expiration date
 * @returns {object} Formatted time and status
 */
export const formatTimeRemaining = (expiresAt) => {
  const now = new Date();
  const timeLeft = expiresAt - now;
  
  if (timeLeft <= 0) {
    return {
      status: 'expired',
      display: 'Expired',
      color: 'text-red-400'
    };
  }
  
  const hours = Math.floor(timeLeft / (1000 * 60 * 60));
  const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
  
  let status = 'normal';
  let color = 'text-green-400';
  
  if (hours <= 1) {
    status = 'urgent';
    color = 'text-red-400';
  } else if (hours <= 3) {
    status = 'warning';
    color = 'text-yellow-400';
  }
  
  const display = hours > 0 ? 
    `${hours}h ${minutes}m` : 
    `${minutes}m`;
  
  return {
    status,
    display,
    color,
    hours,
    minutes
  };
};

// Constants for the virtual economy
export const ECONOMY_CONFIG = {
  COMMISSION: {
    BET: 6, // 6% commission on bets
    GIFT: 3, // 3% commission on gifts
    TRANSACTION: 0 // No transaction fees for buy/sell
  },
  LIMITS: {
    DAILY_DEPOSIT: 1000, // $1000 daily limit
    MIN_BET: 1, // $1 minimum bet
    MAX_BET: 3000, // $3000 maximum bet
    MIN_GIFT: 1 // $1 minimum gift
  },
  BET_EXPIRY: 24 * 60 * 60 * 1000, // 24 hours in milliseconds
  STARTING_BALANCE: 1000 // Default starting balance
};