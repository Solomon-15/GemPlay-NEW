/**
 * Utility function to format time with user's timezone offset
 */
export const formatTimeWithOffset = (dateString, timezoneOffset = 0) => {
  const date = new Date(dateString);
  // Apply user's timezone offset directly (assume dateString is UTC)
  const adjustedTime = new Date(date.getTime() + (timezoneOffset * 3600000));
  return adjustedTime.toLocaleString();
};

/**
 * Format time as date with user's timezone offset
 */
export const formatDateWithOffset = (dateString, timezoneOffset = 0) => {
  const date = new Date(dateString);
  // Apply user's timezone offset directly (assume dateString is UTC)
  const adjustedTime = new Date(date.getTime() + (timezoneOffset * 3600000));
  return adjustedTime.toLocaleDateString();
};

/**
 * Format time as HH:MM:SS with user's timezone offset
 */
export const formatTimeOnlyWithOffset = (dateString, timezoneOffset = 0) => {
  const date = new Date(dateString);
  // Apply user's timezone offset directly (assume dateString is UTC)
  const adjustedTime = new Date(date.getTime() + (timezoneOffset * 3600000));
  
  const hours = adjustedTime.getHours().toString().padStart(2, '0');
  const minutes = adjustedTime.getMinutes().toString().padStart(2, '0');
  const seconds = adjustedTime.getSeconds().toString().padStart(2, '0');
  
  return `${hours}:${minutes}:${seconds}`;
};