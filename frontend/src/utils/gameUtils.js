// Shared utilities for game components
export const GAME_MOVES = [
  { value: 'rock', label: 'Камень', icon: '🪨' },
  { value: 'paper', label: 'Бумага', icon: '📄' },
  { value: 'scissors', label: 'Ножницы', icon: '✂️' }
];

export const GAME_CONSTANTS = {
  MIN_BET: 1,
  MAX_BET: 3000,
  COMMISSION_RATE: 0.06 // 6%
};

/**
 * Format gems bet object into readable string
 */
export const formatGemsBet = (betGems) => {
  if (!betGems || typeof betGems !== 'object') return 'Нет ставок';
  
  return Object.entries(betGems)
    .filter(([_, quantity]) => quantity > 0)
    .map(([type, quantity]) => `${type}: ${quantity}`)
    .join(', ');
};

/**
 * Get time ago string in Russian
 */
export const getTimeAgo = (dateString) => {
  if (!dateString) return 'Неизвестно';
  
  const now = new Date();
  const gameTime = new Date(dateString);
  const diffInMinutes = Math.floor((now - gameTime) / (1000 * 60));
  
  if (diffInMinutes < 1) return 'Только что';
  if (diffInMinutes < 60) return `${diffInMinutes} мин назад`;
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} ч назад`;
  return `${Math.floor(diffInMinutes / 1440)} дн назад`;
};

/**
 * Calculate total bet amount from selected gems
 */
export const calculateTotalBetAmount = (selectedGems, gems) => {
  let total = 0;
  for (const [gemType, quantity] of Object.entries(selectedGems)) {
    const gem = gems.find(g => g.type === gemType);
    if (gem && quantity > 0) {
      total += gem.price * quantity;
    }
  }
  return total;
};

/**
 * Calculate commission amount
 */
export const calculateCommission = (betAmount) => {
  return betAmount * GAME_CONSTANTS.COMMISSION_RATE;
};

/**
 * Validate bet amount and gems selection
 */
export const validateBet = (selectedGems, gems, balance) => {
  const totalBet = calculateTotalBetAmount(selectedGems, gems);
  const commission = calculateCommission(totalBet);
  
  if (totalBet < GAME_CONSTANTS.MIN_BET) {
    return `Минимальная ставка $${GAME_CONSTANTS.MIN_BET}`;
  }
  
  if (totalBet > GAME_CONSTANTS.MAX_BET) {
    return `Максимальная ставка $${GAME_CONSTANTS.MAX_BET}`;
  }
  
  if (balance && balance.virtual_balance < commission) {
    return `Недостаточно средств для комиссии: $${commission.toFixed(2)}`;
  }
  
  const hasValidGems = Object.values(selectedGems).some(qty => qty > 0);
  if (!hasValidGems) {
    return 'Выберите хотя бы один гем для ставки';
  }
  
  return null;
};

/**
 * Check if user can join a game
 */
export const canJoinGame = (game, userId) => {
  return (
    game.status === 'WAITING' &&
    game.creator_id !== userId &&
    !game.opponent_id
  );
};

/**
 * Filter gems with zero quantity
 */
export const filterValidGems = (selectedGems) => {
  const betGems = {};
  for (const [gemType, quantity] of Object.entries(selectedGems)) {
    if (quantity > 0) {
      betGems[gemType] = quantity;
    }
  }
  return betGems;
};