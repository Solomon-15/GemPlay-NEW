import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import Sidebar from "./components/Sidebar";
import Lobby from "./components/Lobby";
import MyBets from "./components/MyBets";
import Profile from "./components/Profile";
import Shop from "./components/Shop";
import Inventory from "./components/Inventory";
import Leaderboard from "./components/Leaderboard";
import History from "./components/History";
import CreateGame from "./components/CreateGame";
import GameLobby from "./components/GameLobby";
import SecurityMonitoring from "./components/SecurityMonitoring";
import AdminPanel from "./components/AdminPanel";
import BalanceDisplay from "./components/BalanceDisplay";
import NotificationProvider from "./components/NotificationContext";
import { GemsProvider } from './components/GemsContext';
import NotificationContainer from "./components/NotificationContainer";
import NotificationDemo from "./components/NotificationDemo";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Login Component
const LoginForm = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    gender: 'male'
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        // Login
        console.log('🔐 Attempting login for:', formData.email);
        const response = await axios.post(`${API}/auth/login`, {
          email: formData.email,
          password: formData.password
        });
        
        console.log('🎉 Login successful. Response:', response.data);
        localStorage.setItem('token', response.data.access_token);
        if (response.data.refresh_token) {
          localStorage.setItem('refresh_token', response.data.refresh_token);
          console.log('🔄 Refresh token saved');
        }
        console.log('💾 Token saved to localStorage');
        onLogin(response.data.user);
      } else {
        // Register
        const response = await axios.post(`${API}/auth/register`, {
          username: formData.username,
          email: formData.email,
          password: formData.password,
          gender: formData.gender
        });
        
        alert(`Registration successful! Verification token: ${response.data.verification_token}`);
        
        // Auto verify for demo
        await axios.post(`${API}/auth/verify-email`, {
          token: response.data.verification_token
        });
        
        // Auto login after verification
        const loginResponse = await axios.post(`${API}/auth/login`, {
          email: formData.email,
          password: formData.password
        });
        
        localStorage.setItem('token', loginResponse.data.access_token);
        if (loginResponse.data.refresh_token) {
          localStorage.setItem('refresh_token', loginResponse.data.refresh_token);
        }
        onLogin(loginResponse.data.user);
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-primary flex items-center justify-center p-8">
      <div className="bg-surface-card border border-border-primary rounded-xl p-8 max-w-md w-full">
        <h1 className="font-russo text-3xl text-accent-primary text-center mb-2">
          GemPlay
        </h1>
        <p className="font-roboto text-text-secondary text-center mb-6">
          PvP NFT Gem Battle Game
        </p>
        
        <div className="flex mb-6">
          <button
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 px-4 rounded-l-lg font-rajdhani font-bold transition-colors ${
              isLogin ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary'
            }`}
          >
            LOGIN
          </button>
          <button
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 px-4 rounded-r-lg font-rajdhani font-bold transition-colors ${
              !isLogin ? 'bg-accent-primary text-white' : 'bg-surface-sidebar text-text-secondary'
            }`}
          >
            REGISTER
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <>
              <input
                type="text"
                placeholder="Username"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                className="w-full px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
                required
              />
              <select
                value={formData.gender}
                onChange={(e) => setFormData({...formData, gender: e.target.value})}
                className="w-full px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </>
          )}
          
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            className="w-full px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
            required
          />
          
          <input
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            className="w-full px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto"
            required
          />
          
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-accent text-white font-rajdhani font-bold text-lg rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? 'LOADING...' : (isLogin ? 'LOGIN' : 'REGISTER')}
          </button>
        </form>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('lobby');
  const [isAdminPanelOpen, setIsAdminPanelOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('token');
    const refreshToken = localStorage.getItem('refresh_token');
    console.log('🔍 Checking auth status. Token exists:', !!token, 'Refresh token exists:', !!refreshToken);
    
    if (token) {
      try {
        console.log('📡 Making request to /api/auth/me with token:', token.substring(0, 20) + '...');
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        console.log('✅ Auth check successful. User:', response.data);
        setUser(response.data);
      } catch (error) {
        console.error('❌ Auth check failed:', error.response?.status, error.response?.data || error.message);
        
        // If token is expired and we have a refresh token, try to refresh
        if (error.response?.status === 401 && refreshToken) {
          console.log('🔄 Attempting to refresh token...');
          try {
            const refreshResponse = await axios.post(`${API}/auth/refresh?refresh_token=${refreshToken}`);
            
            console.log('✅ Token refreshed successfully');
            localStorage.setItem('token', refreshResponse.data.access_token);
            if (refreshResponse.data.refresh_token) {
              localStorage.setItem('refresh_token', refreshResponse.data.refresh_token);
            }
            setUser(refreshResponse.data.user);
            return; // Exit early, we're good now
          } catch (refreshError) {
            console.error('❌ Token refresh failed:', refreshError.response?.data || refreshError.message);
          }
        }
        
        console.log('🗑️ Removing invalid tokens');
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
      }
    } else {
      console.log('🔒 No token found in localStorage');
    }
    setLoading(false);
  };

  const handleLogin = (userData) => {
    console.log('🚀 handleLogin called with userData:', userData);
    setUser(userData);
    console.log('✅ User state updated');
  };

  const handleOpenAdminPanel = () => {
    setIsAdminPanelOpen(true);
  };

  const handleCloseAdminPanel = () => {
    setIsAdminPanelOpen(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setCurrentView('lobby');
    setIsAdminPanelOpen(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-primary flex items-center justify-center">
        <div className="text-white text-xl font-roboto">Загрузка...</div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <NotificationProvider>
      <GemsProvider>
        {/* Если открыта админ панель, показываем только её */}
        {isAdminPanelOpen ? (
          <AdminPanel user={user} onClose={handleCloseAdminPanel} />
        ) : (
          <div className="min-h-screen bg-gradient-primary flex">
            {/* Sidebar */}
            <Sidebar 
              currentView={currentView}
              setCurrentView={setCurrentView}
              user={user}
              isCollapsed={sidebarCollapsed}
              setIsCollapsed={setSidebarCollapsed}
              onOpenAdminPanel={handleOpenAdminPanel}
              onLogout={handleLogout}
            />

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-h-screen">
              {/* Top Bar - Sticky Header */}
              <nav className="sticky top-0 z-40 bg-surface-sidebar border-b border-border-primary p-4 flex-shrink-0">
                <div className="flex items-center justify-between">
                  {/* Desktop: Page Title Only */}
                  <div className="hidden md:block">
                    <h1 className="text-xl font-russo text-text-primary capitalize">
                      {currentView === 'my-bets' ? 'My Bets' : 
                       currentView === 'game-lobby' ? 'Game Lobby' : 
                       currentView === 'create-game' ? 'Create Game' : 
                       currentView === 'notification-demo' ? 'Notification Demo' : 
                       currentView}
                    </h1>
                  </div>

                  {/* Mobile: Empty space */}
                  <div className="md:hidden"></div>

                  {/* Desktop: Balance Display */}
                  <div className="hidden md:block">
                    <BalanceDisplay user={user} onUpdateUser={checkAuthStatus} />
                  </div>

                  {/* Mobile: Profile Avatar */}
                  <div className="md:hidden">
                    <button
                      onClick={() => setCurrentView('profile')}
                      className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                        currentView === 'profile' 
                          ? 'bg-gradient-to-r from-green-600 to-green-700 ring-2 ring-accent-primary' 
                          : 'bg-gradient-to-r from-green-600 to-green-700 hover:ring-2 hover:ring-accent-primary/50'
                      }`}
                    >
                      <span className="font-russo text-white text-sm">
                        {user.username.charAt(0).toUpperCase()}
                      </span>
                    </button>
                  </div>
                </div>
              </nav>

              {/* Page Content */}
              <div className="flex-1 overflow-auto pb-20 md:pb-0">
                {/* Mobile responsive wrapper */}
                <div className="min-w-0 px-4 md:px-0">
                {currentView === 'lobby' && (
                  <Lobby user={user} onUpdateUser={checkAuthStatus} setCurrentView={setCurrentView} />
                )}
                {currentView === 'my-bets' && (
                  <MyBets user={user} onUpdateUser={checkAuthStatus} />
                )}
                {currentView === 'profile' && (
                  <Profile user={user} onUpdateUser={checkAuthStatus} />
                )}
                {currentView === 'shop' && (
                  <Shop user={user} onUpdateUser={checkAuthStatus} />
                )}
                {currentView === 'inventory' && (
                  <Inventory user={user} onUpdateUser={checkAuthStatus} />
                )}
                {currentView === 'create-game' && (
                  <CreateGame user={user} onUpdateUser={checkAuthStatus} />
                )}
                {currentView === 'game-lobby' && (
                  <GameLobby user={user} onUpdateUser={checkAuthStatus} />
                )}
                {currentView === 'leaderboard' && (
                  <Leaderboard user={user} onUpdateUser={checkAuthStatus} />
                )}
                {currentView === 'history' && (
                  <History user={user} onUpdateUser={checkAuthStatus} />
                )}
                {currentView === 'notification-demo' && (
                  <NotificationDemo />
                )}
                {currentView === 'monitoring' && (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') && (
                  <SecurityMonitoring user={user} />
                )}
              </div>
            </div>
            
            {/* Notification Container */}
            <NotificationContainer />
          </div>
        )}
      </GemsProvider>
    </NotificationProvider>
  );
}

export default App;