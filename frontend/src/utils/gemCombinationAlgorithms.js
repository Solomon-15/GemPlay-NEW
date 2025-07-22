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
 * Advanced fallback algorithm using dynamic programming
 * @param {Array} availableGems - Available gems with quantities
 * @param {number} targetAmount - Target amount to achieve
 * @returns {Object} { success: boolean, combination: Array }
 */
const findExactCombinationDP = (availableGems, targetAmount) => {
  const targetCents = Math.round(targetAmount * 100); // Work with cents for precision
  
  // Create array of all possible gem units
  const gemUnits = [];
  for (const gem of availableGems) {
    const priceCents = Math.round(gem.price * 100);
    for (let i = 0; i < gem.availableQuantity; i++) {
      gemUnits.push({
        type: gem.type,
        name: gem.name,
        price: gem.price,
        priceCents: priceCents,
        icon: gem.icon,
        color: gem.color
      });
    }
  }
  
  // DP table: dp[i] = True if we can make amount i
  const dp = new Array(targetCents + 1).fill(false);
  dp[0] = true;
  
  // parent[i] = gem index used to achieve amount i
  const parent = new Array(targetCents + 1).fill(-1);
  
  // Fill DP table
  for (let i = 0; i < gemUnits.length; i++) {
    const unit = gemUnits[i];
    const priceCents = unit.priceCents;
    
    // Go backwards to avoid using same unit multiple times
    for (let amount = targetCents; amount >= priceCents; amount--) {
      if (dp[amount - priceCents] && !dp[amount]) {
        dp[amount] = true;
        parent[amount] = i;
      }
    }
  }
  
  // If exact amount not achievable
  if (!dp[targetCents]) {
    return { success: false, combination: [] };
  }
  
  // Reconstruct solution
  const usedUnits = [];
  let currentAmount = targetCents;
  
  while (currentAmount > 0 && parent[currentAmount] !== -1) {
    const gemIndex = parent[currentAmount];
    const unit = gemUnits[gemIndex];
    usedUnits.push(unit);
    currentAmount -= unit.priceCents;
  }
  
  // Convert to combination format
  const gemCounts = {};
  for (const unit of usedUnits) {
    const gemType = unit.type;
    if (!gemCounts[gemType]) {
      gemCounts[gemType] = 0;
    }
    gemCounts[gemType]++;
  }
  
  const combination = Object.entries(gemCounts).map(([gemType, quantity]) => {
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
  
  return { success: true, combination };
};
/**
 * Get available gems with proper validation and logging
 */
const getAvailableGems = (gemsData) => {
  const availableGems = gemsData
    .filter(gem => gem.available_quantity > 0)
    .map(gem => ({
      type: gem.type,
      name: gem.name,
      price: gem.price,
      availableQuantity: gem.available_quantity, // Use actual available quantity
      totalQuantity: gem.quantity, // Add total for debugging
      frozenQuantity: gem.frozen_quantity, // Add frozen for debugging
      icon: gem.icon,
      color: gem.color
    }));
  
  // Debug logging
  console.log('Available gems for strategy:', availableGems.map(g => 
    `${g.name}: ${g.availableQuantity}/${g.totalQuantity} available (${g.frozenQuantity} frozen)`
  ));
  
  return availableGems;
};

/**
 * 🔴 SMALL STRATEGY - Use more cheap gems
 * Prioritizes cheapest gems first, but adapts when cheap gems run out
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
  
  // FLEXIBLE GREEDY ALGORITHM: use cheapest gems first, adapt when needed
  while (remaining > 0) {
    let foundGem = false;
    
    // Try to find the cheapest gem that fits
    for (const gem of sortedGems) {
      const currentUsed = selectedGems[gem.type] || 0;
      
      // ENHANCED VALIDATION: Check if we can use this gem
      if (currentUsed < gem.availableQuantity && gem.price <= remaining) {
        selectedGems[gem.type] = currentUsed + 1;
        remaining -= gem.price;
        foundGem = true;
        
        // Debug log for tracking
        console.log(`Small Strategy: Using ${gem.name} #${currentUsed + 1}/${gem.availableQuantity}, remaining: $${remaining.toFixed(2)}`);
        break;
      }
    }
    
    // If no exact gem found, try to use larger gems to finish
    if (!foundGem) {
      // Try to find any gem that can cover the remaining amount exactly
      let exactMatch = false;
      for (const gem of sortedGems) {
        const currentUsed = selectedGems[gem.type] || 0;
        if (currentUsed < gem.availableQuantity && gem.price === remaining) {
          selectedGems[gem.type] = currentUsed + 1;
          remaining = 0;
          exactMatch = true;
          console.log(`Small Strategy: Found exact match with ${gem.name} #${currentUsed + 1}/${gem.availableQuantity}`);
          break;
        }
      }
      
      if (!exactMatch) {
        // Try advanced DP algorithm as fallback
        console.log('Small Strategy: Trying DP algorithm as fallback');
        const dpResult = findExactCombinationDP(availableGems, targetAmount);
        if (dpResult.success) {
          return {
            success: true,
            combination: dpResult.combination.sort((a, b) => a.price - b.price),
            message: `Small strategy: Found exact combination for $${targetAmount.toFixed(2)}`
          };
        }
        
        // No solution possible - provide detailed error
        console.error('Small Strategy: No solution found', {
          targetAmount,
          availableGems: availableGems.map(g => `${g.name}: ${g.availableQuantity}`),
          selectedSoFar: selectedGems,
          remainingNeeded: remaining
        });
        
        return {
          success: false,
          combination: [],
          message: "Not enough gems in inventory to create this bet amount. Try a lower amount or purchase more gems."
        };
      }
    }
  }
  
  // Convert to combination format with FINAL VALIDATION
  const combination = Object.entries(selectedGems).map(([gemType, quantity]) => {
    const gemInfo = availableGems.find(g => g.type === gemType);
    
    // CRITICAL CHECK: Ensure we don't exceed available quantity
    if (quantity > gemInfo.availableQuantity) {
      console.error(`VALIDATION ERROR: Trying to use ${quantity} ${gemType} but only ${gemInfo.availableQuantity} available`);
      throw new Error(`Cannot use ${quantity} ${gemType}, only ${gemInfo.availableQuantity} available in inventory`);
    }
    
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
  
  // FINAL AMOUNT VALIDATION
  if (Math.abs(totalValue - targetAmount) > 0.01) {
    console.error(`AMOUNT MISMATCH: Target ${targetAmount}, got ${totalValue}`);
    return {
      success: false,
      combination: [],
      message: `Amount calculation error: expected $${targetAmount.toFixed(2)}, got $${totalValue.toFixed(2)}`
    };
  }
  
  return {
    success: true,
    combination: combination.sort((a, b) => a.price - b.price), // Sort by price for display
    message: `Small strategy: Found exact combination for $${totalValue.toFixed(2)}`
  };
};

/**
 * 🟢 SMART STRATEGY - Balanced mid-range gems
 * Tries 60% mid, 30% low, 10% high but adapts flexibly when needed
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

  const selectedGems = {};
  let remaining = targetAmount;

  // Helper function to select gems from a category
  const selectFromCategory = (gems, maxToSpend) => {
    let spent = 0;
    
    while (remaining > 0 && spent < maxToSpend && gems.length > 0) {
      let foundGem = false;
      
      for (const gem of gems) {
        const currentUsed = selectedGems[gem.type] || 0;
        
        if (currentUsed < gem.availableQuantity && gem.price <= remaining && gem.price <= (maxToSpend - spent)) {
          selectedGems[gem.type] = currentUsed + 1;
          remaining -= gem.price;
          spent += gem.price;
          foundGem = true;
          break;
        }
      }
      
      if (!foundGem) break;
    }
    
    return spent;
  };

  // FLEXIBLE APPROACH: Try ideal distribution first, then adapt
  
  // Phase 1: Try ideal distribution
  const targetMid = targetAmount * 0.6;   // 60%
  const targetLow = targetAmount * 0.3;   // 30% 
  const targetHigh = targetAmount * 0.1;  // 10%

  selectFromCategory(categorizedGems.mid, targetMid);
  selectFromCategory(categorizedGems.low, targetLow);
  selectFromCategory(categorizedGems.high, targetHigh);

  // Phase 2: If still have remaining amount, use ANY available gems flexibly
  if (remaining > 0) {
    // Try all categories in order of preference for Smart: mid first, then low, then high
    const allGemsOrdered = [
      ...categorizedGems.mid,
      ...categorizedGems.low, 
      ...categorizedGems.high
    ];
    
    while (remaining > 0) {
      let foundGem = false;
      
      for (const gem of allGemsOrdered) {
        const currentUsed = selectedGems[gem.type] || 0;
        
        if (currentUsed < gem.availableQuantity && gem.price <= remaining) {
          selectedGems[gem.type] = currentUsed + 1;
          remaining -= gem.price;
          foundGem = true;
          break;
        }
      }
      
      if (!foundGem) {
        // Try to find exact match with any remaining gem
        for (const gem of allGemsOrdered) {
          const currentUsed = selectedGems[gem.type] || 0;
          if (currentUsed < gem.availableQuantity && gem.price === remaining) {
            selectedGems[gem.type] = currentUsed + 1;
            remaining = 0;
            foundGem = true;
            break;
          }
        }
        
        if (!foundGem) break;
      }
    }
  }

  // Check if we achieved the exact target
  if (remaining > 0) {
    // Try advanced DP algorithm as fallback
    const dpResult = findExactCombinationDP(availableGems, targetAmount);
    if (dpResult.success) {
      return {
        success: true,
        combination: dpResult.combination.sort((a, b) => a.price - b.price),
        message: `Smart strategy: Found balanced combination for $${targetAmount.toFixed(2)}`
      };
    }
    
    return {
      success: false,
      combination: [],
      message: "Not enough gems in inventory to form this bet. Please adjust your balance or select manually."
    };
  }

  // Convert to combination format with FINAL VALIDATION
  const combination = Object.entries(selectedGems).map(([gemType, quantity]) => {
    const gemInfo = availableGems.find(g => g.type === gemType);
    
    // CRITICAL CHECK: Ensure we don't exceed available quantity
    if (quantity > gemInfo.availableQuantity) {
      console.error(`VALIDATION ERROR: Trying to use ${quantity} ${gemType} but only ${gemInfo.availableQuantity} available`);
      throw new Error(`Cannot use ${quantity} ${gemType}, only ${gemInfo.availableQuantity} available in inventory`);
    }
    
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
  
  // FINAL AMOUNT VALIDATION
  if (Math.abs(totalValue - targetAmount) > 0.01) {
    console.error(`AMOUNT MISMATCH: Target ${targetAmount}, got ${totalValue}`);
    return {
      success: false,
      combination: [],
      message: `Amount calculation error: expected $${targetAmount.toFixed(2)}, got $${totalValue.toFixed(2)}`
    };
  }

  return {
    success: true,
    combination: combination.sort((a, b) => a.price - b.price), // Sort by price for display
    message: `Smart strategy: Found balanced combination for $${totalValue.toFixed(2)}`
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
      // Try to find exact match with any remaining gem
      for (const gem of sortedGems) {
        const currentUsed = selectedGems[gem.type] || 0;
        if (currentUsed < gem.availableQuantity && gem.price === remaining) {
          selectedGems[gem.type] = currentUsed + 1;
          remaining = 0;
          foundGem = true;
          break;
        }
      }
      
      if (!foundGem) {
        // Try advanced DP algorithm as fallback
        const dpResult = findExactCombinationDP(availableGems, targetAmount);
        if (dpResult.success) {
          return {
            success: true,
            combination: dpResult.combination.sort((a, b) => a.price - b.price),
            message: `Big strategy: Found combination with fewest gems for $${targetAmount.toFixed(2)}`
          };
        }
        
        return {
          success: false,
          combination: [],
          message: "Not enough gems in inventory to form this bet. Please adjust your balance or select manually."
        };
      }
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