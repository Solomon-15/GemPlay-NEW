import axios from 'axios';
import { API } from './api';

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

// Request interceptor to add token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle 401s and auto-refresh tokens
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Token refresh in progress, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return axios(originalRequest);
        }).catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!refreshToken) {
        // No refresh token, force logout
        handleLogout();
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API}/auth/refresh`, { refresh_token: refreshToken }, {
          headers: { 'Content-Type': 'application/json' }
        });
        
        const { access_token, refresh_token: newRefreshToken } = response.data;
        
        // Store new tokens
        localStorage.setItem('token', access_token);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }
        
        // Update default header
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        // Process queued requests
        processQueue(null, access_token);
        
        // Retry original request
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return axios(originalRequest);
        
      } catch (refreshError) {
        // Refresh failed, force logout
        processQueue(refreshError, null);
        handleLogout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    return Promise.reject(error);
  }
);

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  
  // Show notification
  if (window.showErrorRU) {
    window.showErrorRU('Сессия истекла. Пожалуйста, войдите снова.');
  }
  
  // Redirect to login - trigger app logout
  if (window.location.pathname !== '/') {
    window.location.reload();
  }
};

export { axios as axiosWithAuth };
export default axios;