/**
 * Общий API utility для работы с backend
 * Централизованное управление URL и конфигурацией API
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

/**
 * Получить токен авторизации из localStorage
 */
export const getAuthToken = () => {
  return localStorage.getItem('token');
};

/**
 * Получить заголовки для авторизованных запросов
 */
export const getAuthHeaders = () => {
  const token = getAuthToken();
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
};

/**
 * Конфигурация для axios запросов с авторизацией
 */
export const getApiConfig = () => {
  return {
    headers: getAuthHeaders()
  };
};

export default API;