/**
 * Utility function to format time with user's timezone offset
 */
export const formatTimeWithOffset = (dateString, timezoneOffset = 0) =&gt; {
  const date = new Date(dateString);
  // Apply user's timezone offset directly (assume dateString is UTC)
  const adjustedTime = new Date(date.getTime() + (timezoneOffset * 3600000));
  return adjustedTime.toLocaleString();
};

/**
 * Format time as date with user's timezone offset
 */
export const formatDateWithOffset = (dateString, timezoneOffset = 0) =&gt; {
  const date = new Date(dateString);
  // Apply user's timezone offset directly (assume dateString is UTC)
  const adjustedTime = new Date(date.getTime() + (timezoneOffset * 3600000));
  return adjustedTime.toLocaleDateString();
};

/**
 * Format time as HH:MM:SS with user's timezone offset
 */
export const formatTimeOnlyWithOffset = (dateString, timezoneOffset = 0) =&gt; {
  const date = new Date(dateString);
  // Apply user's timezone offset directly (assume dateString is UTC)
  const adjustedTime = new Date(date.getTime() + (timezoneOffset * 3600000));
  
  const hours = adjustedTime.getHours().toString().padStart(2, '0');
  const minutes = adjustedTime.getMinutes().toString().padStart(2, '0');
  const seconds = adjustedTime.getSeconds().toString().padStart(2, '0');
  
  return `${hours}:${minutes}:${seconds}`;
};

/**
 * Format datetime as dd.mm.yyyy, HH:MM:SS with optional timezone offset (hours)
 */
export const formatDateTimeDDMMYYYYHHMMSS = (dateString, timezoneOffset = null) =&gt; {
  const raw = new Date(dateString);
  const d = timezoneOffset === null ? raw : new Date(raw.getTime() + timezoneOffset * 3600000);
  const dd = d.getDate().toString().padStart(2, '0');
  const mm = (d.getMonth() + 1).toString().padStart(2, '0');
  const yyyy = d.getFullYear();
  const hh = d.getHours().toString().padStart(2, '0');
  const min = d.getMinutes().toString().padStart(2, '0');
  const ss = d.getSeconds().toString().padStart(2, '0');
  return `${dd}.${mm}.${yyyy}, ${hh}:${min}:${ss}`;
};