/**
 * NEW GEM COMBINATION ALGORITHMS - COMPLETE REFACTOR
 * 
 * All algorithms work strictly with inventory data and respect available quantities.
 * No backend dependency - pure frontend logic.
 */

// Gem price categories
const GEM_CATEGORIES = {
  LOW: ['Ruby', 'Amber'],           // $1, $2
  MID: ['Topaz', 'Emerald', 'Aquamarine'],  // $5, $10, $25
  HIGH: ['Sapphire', 'Magic']       // $50, $100
};

/**
 * Get available gems from inventory data with proper sorting
 * @param {Array} gemsData - Raw gems data from context
 * @returns {Array} Processed available gems
 */
const getAvailableGems = (gemsData) => {
  return gemsData
    .filter(gem => gem.available_quantity > 0)
    .map(gem => ({
      type: gem.type,
      name: gem.name,
      price: gem.price,
      availableQuantity: gem.available_quantity,
      icon: gem.icon,
      color: gem.color
    }));
};

/**
 * 🔴 SMALL STRATEGY - Use more cheap gems
 * Prioritizes cheapest gems first (Ruby, Amber, then others in ascending price order)
 * 
 * @param {Array} gemsData - Gems inventory data
 * @param {number} targetAmount - Target bet amount
 * @returns {Object} { success: boolean, combination: Array, message: string }
 */
export const calculateSmallStrategy = (gemsData, targetAmount) => {
  const availableGems = getAvailableGems(gemsData);
  
  if (availableGems.length === 0) {
    return {
      success: false,
      combination: [],
      message: "No gems available in inventory."
    };
  }

  // Sort by price ascending (cheapest first)
  const sortedGems = [...availableGems].sort((a, b) => a.price - b.price);
  
  let remaining = targetAmount;
  const selectedGems = {};
  
  // Greedy algorithm: use cheapest gems first
  while (remaining > 0) {
    let foundGem = false;
    
    for (const gem of sortedGems) {
      const currentUsed = selectedGems[gem.type] || 0;
      
      // Check if we can use this gem (has quantity and fits in remaining amount)
      if (currentUsed < gem.availableQuantity && gem.price <= remaining) {
        selectedGems[gem.type] = currentUsed + 1;
        remaining -= gem.price;
        foundGem = true;
        break;
      }
    }
    
    // If no gem can be used, we can't reach the target
    if (!foundGem) {
      return {
        success: false,
        combination: [],
        message: "Not enough gems in inventory to form this bet. Please adjust your balance or select manually."
      };
    }
  }
  
  // Convert to combination format
  const combination = Object.entries(selectedGems).map(([gemType, quantity]) => {
    const gemInfo = availableGems.find(g => g.type === gemType);
    return {
      type: gemType,
      name: gemInfo.name,
      price: gemInfo.price,
      quantity: quantity,
      totalValue: gemInfo.price * quantity,
      icon: gemInfo.icon,
      color: gemInfo.color
    };
  });
  
  const totalValue = combination.reduce((sum, item) => sum + item.totalValue, 0);
  
  return {
    success: true,
    combination: combination.sort((a, b) => a.price - b.price), // Sort by price for display
    message: `Small strategy: Found exact combination for $${totalValue.toFixed(2)}`
  };
};

/**
 * 🟢 SMART STRATEGY - Balanced mid-range gems
 * Distribution: ~60% mid-range, ~30% low, ~10% high (by value)
 * 
 * @param {Array} gemsData - Gems inventory data
 * @param {number} targetAmount - Target bet amount
 * @returns {Object} { success: boolean, combination: Array, message: string }
 */
export const calculateSmartStrategy = (gemsData, targetAmount) => {
  const availableGems = getAvailableGems(gemsData);
  
  if (availableGems.length === 0) {
    return {
      success: false,
      combination: [],
      message: "No gems available in inventory."
    };
  }

  // Categorize available gems
  const categorizedGems = {
    low: availableGems.filter(gem => GEM_CATEGORIES.LOW.includes(gem.type)),
    mid: availableGems.filter(gem => GEM_CATEGORIES.MID.includes(gem.type)),
    high: availableGems.filter(gem => GEM_CATEGORIES.HIGH.includes(gem.type))
  };

  // Sort each category appropriately
  categorizedGems.low.sort((a, b) => a.price - b.price);
  categorizedGems.mid.sort((a, b) => a.price - b.price);
  categorizedGems.high.sort((a, b) => b.price - a.price); // High gems: expensive first

  // Calculate target amounts for each category
  const targetMid = targetAmount * 0.6;   // 60%
  const targetLow = targetAmount * 0.3;   // 30%
  const targetHigh = targetAmount * 0.1;  // 10%

  const selectedGems = {};
  let totalSelected = 0;

  // Helper function to select gems from a category
  const selectFromCategory = (gems, targetValue) => {
    let remaining = targetValue;
    let selected = 0;
    
    while (remaining > 0 && gems.length > 0) {
      let foundGem = false;
      
      for (const gem of gems) {
        const currentUsed = selectedGems[gem.type] || 0;
        
        if (currentUsed < gem.availableQuantity && gem.price <= remaining) {
          selectedGems[gem.type] = currentUsed + 1;
          remaining -= gem.price;
          selected += gem.price;
          foundGem = true;
          break;
        }
      }
      
      if (!foundGem) break;
    }
    
    return selected;
  };

  // 1. Try to select mid-range gems (60%)
  totalSelected += selectFromCategory(categorizedGems.mid, targetMid);

  // 2. Try to select low-range gems (30%)
  totalSelected += selectFromCategory(categorizedGems.low, targetLow);

  // 3. Try to select high-range gems (10%)
  totalSelected += selectFromCategory(categorizedGems.high, targetHigh);

  // 4. Fill remaining amount with any available gems
  const remainingAmount = targetAmount - totalSelected;
  if (remainingAmount > 0) {
    const allAvailable = [...categorizedGems.mid, ...categorizedGems.low, ...categorizedGems.high]
      .sort((a, b) => a.price - b.price); // Prefer cheaper gems for filling
    
    selectFromCategory(allAvailable, remainingAmount);
  }

  // Check if we reached the exact target
  const currentTotal = Object.entries(selectedGems).reduce((sum, [gemType, quantity]) => {
    const gemInfo = availableGems.find(g => g.type === gemType);
    return sum + (gemInfo.price * quantity);
  }, 0);

  if (Math.abs(currentTotal - targetAmount) > 0.01) {
    return {
      success: false,
      combination: [],
      message: "Not enough gems in inventory to form this bet. Please adjust your balance or select manually."
    };
  }

  // Convert to combination format
  const combination = Object.entries(selectedGems).map(([gemType, quantity]) => {
    const gemInfo = availableGems.find(g => g.type === gemType);
    return {
      type: gemType,
      name: gemInfo.name,
      price: gemInfo.price,
      quantity: quantity,
      totalValue: gemInfo.price * quantity,
      icon: gemInfo.icon,
      color: gemInfo.color
    };
  });

  return {
    success: true,
    combination: combination.sort((a, b) => a.price - b.price), // Sort by price for display
    message: `Smart strategy: Found balanced combination for $${currentTotal.toFixed(2)}`
  };
};

/**
 * 🟣 BIG STRATEGY - Use fewer expensive gems
 * Prioritizes most expensive gems first (Magic, Sapphire, then others in descending price order)
 * 
 * @param {Array} gemsData - Gems inventory data
 * @param {number} targetAmount - Target bet amount
 * @returns {Object} { success: boolean, combination: Array, message: string }
 */
export const calculateBigStrategy = (gemsData, targetAmount) => {
  const availableGems = getAvailableGems(gemsData);
  
  if (availableGems.length === 0) {
    return {
      success: false,
      combination: [],
      message: "No gems available in inventory."
    };
  }

  // Sort by price descending (most expensive first)
  const sortedGems = [...availableGems].sort((a, b) => b.price - a.price);
  
  let remaining = targetAmount;
  const selectedGems = {};
  
  // Greedy algorithm: use most expensive gems first
  while (remaining > 0) {
    let foundGem = false;
    
    for (const gem of sortedGems) {
      const currentUsed = selectedGems[gem.type] || 0;
      
      // Check if we can use this gem (has quantity and fits in remaining amount)
      if (currentUsed < gem.availableQuantity && gem.price <= remaining) {
        selectedGems[gem.type] = currentUsed + 1;
        remaining -= gem.price;
        foundGem = true;
        break;
      }
    }
    
    // If no gem can be used, we can't reach the target
    if (!foundGem) {
      return {
        success: false,
        combination: [],
        message: "Not enough gems in inventory to form this bet. Please adjust your balance or select manually."
      };
    }
  }
  
  // Convert to combination format
  const combination = Object.entries(selectedGems).map(([gemType, quantity]) => {
    const gemInfo = availableGems.find(g => g.type === gemType);
    return {
      type: gemType,
      name: gemInfo.name,
      price: gemInfo.price,
      quantity: quantity,
      totalValue: gemInfo.price * quantity,
      icon: gemInfo.icon,
      color: gemInfo.color
    };
  });
  
  const totalValue = combination.reduce((sum, item) => sum + item.totalValue, 0);
  
  return {
    success: true,
    combination: combination.sort((a, b) => a.price - b.price), // Sort by price for display
    message: `Big strategy: Found combination with fewest gems for $${totalValue.toFixed(2)}`
  };
};

/**
 * Main strategy selector function
 * @param {string} strategy - 'small', 'smart', or 'big'
 * @param {Array} gemsData - Gems inventory data
 * @param {number} targetAmount - Target bet amount
 * @returns {Object} Strategy result
 */
export const calculateGemCombination = (strategy, gemsData, targetAmount) => {
  switch (strategy) {
    case 'small':
      return calculateSmallStrategy(gemsData, targetAmount);
    case 'smart':
      return calculateSmartStrategy(gemsData, targetAmount);
    case 'big':
      return calculateBigStrategy(gemsData, targetAmount);
    default:
      return {
        success: false,
        combination: [],
        message: "Invalid strategy selected."
      };
  }
};