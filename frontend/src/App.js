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
import AdminPanel from "./components/AdminPanel";
import HeaderPortfolio from "./components/HeaderPortfolio";
import MobileHeader from "./components/MobileHeader";
import NotificationProvider from "./components/NotificationContext";
import { GemsProvider } from './components/GemsContext';
import NotificationContainer from "./components/NotificationContainer";
import './utils/metamask-blocker'; // Блокировка MetaMask

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
        <div className="flex flex-col items-center mb-2">
          <img 
            src="/gems/gem-green.svg" 
            alt="GemPlay Logo" 
            className="w-16 h-16 mb-4"
          />
          <h1 className="font-russo text-3xl text-accent-primary text-center">
            GemPlay
          </h1>
        </div>
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
    console.log('🔓 Opening admin panel. Current user:', user);
    console.log('🔍 Token exists:', !!localStorage.getItem('token'));
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
        <div className="text-white text-xl font-roboto">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <NotificationProvider>
      <GemsProvider>
        {/* If admin panel is open, show only it */}
        {isAdminPanelOpen ? (
          <AdminPanel user={user} onClose={handleCloseAdminPanel} />
        ) : (
          <div className="min-h-screen bg-gradient-primary flex">
            {/* Desktop Sidebar - Hidden on Mobile */}
            <div className="hidden md:block">
              <Sidebar 
                currentView={currentView}
                setCurrentView={setCurrentView}
                user={user}
                isCollapsed={sidebarCollapsed}
                setIsCollapsed={setSidebarCollapsed}
                onOpenAdminPanel={handleOpenAdminPanel}
                onLogout={handleLogout}
              />
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-h-screen">
              {/* Top Bar - Sticky Header (hidden on mobile) */}
              <nav className="sticky top-0 z-40 bg-surface-sidebar border-b border-border-primary p-4 flex-shrink-0 hidden md:block">
                <div className="flex items-center justify-between">
                  {/* Desktop: Page Title Only */}
                  <div className="block">
                    <h1 className="text-xl font-russo text-text-primary capitalize">
                      {currentView === 'my-bets' ? 'My Bets' : 
                       currentView === 'game-lobby' ? 'Game Lobby' : 
                       currentView === 'create-game' ? 'Create Game' : 
                       currentView}
                    </h1>
                  </div>

                  {/* Header Portfolio - Desktop only */}
                  <div className="block">
                    <HeaderPortfolio user={user} />
                  </div>
                </div>
              </nav>

              {/* Mobile Header */}
              <MobileHeader 
                currentView={currentView}
                setCurrentView={setCurrentView}
                user={user}
                onOpenAdminPanel={handleOpenAdminPanel}
                onLogout={handleLogout}
                totalBalance={user ? (user.virtual_balance || 0) + (user.frozen_balance || 0) : 0}
              />

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
                  <Profile 
                    user={user} 
                    onUpdateUser={checkAuthStatus} 
                    setCurrentView={setCurrentView}
                    onOpenAdminPanel={handleOpenAdminPanel}
                    onLogout={handleLogout}
                  />
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

                </div>
              </div>
            </div>
            
            {/* Mobile Bottom Navigation */}
            <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-surface-sidebar border-t border-border-primary">
              <div className="flex items-center justify-around py-2 px-4">
                {/* Lobby */}
                <button
                  onClick={() => setCurrentView('lobby')}
                  className={`flex flex-col items-center py-2 px-3 rounded-lg transition-all duration-300 ${
                    currentView === 'lobby' 
                      ? 'text-accent-primary bg-accent-primary/10' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                </button>

                {/* My Bets */}
                <button
                  onClick={() => setCurrentView('my-bets')}
                  className={`flex flex-col items-center py-2 px-3 rounded-lg transition-all duration-300 ${
                    currentView === 'my-bets' 
                      ? 'text-accent-primary bg-accent-primary/10' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
                  </svg>
                </button>

                {/* Shop */}
                <button
                  onClick={() => setCurrentView('shop')}
                  className={`flex flex-col items-center py-2 px-3 rounded-lg transition-all duration-300 ${
                    currentView === 'shop' 
                      ? 'text-accent-primary bg-accent-primary/10' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l-1 12H6L5 9z" />
                  </svg>
                </button>

                {/* Inventory */}
                <button
                  onClick={() => setCurrentView('inventory')}
                  className={`flex flex-col items-center py-2 px-3 rounded-lg transition-all duration-300 ${
                    currentView === 'inventory' 
                      ? 'text-accent-primary bg-accent-primary/10' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </button>

                {/* Leaderboard */}
                <button
                  onClick={() => setCurrentView('leaderboard')}
                  className={`flex flex-col items-center py-2 px-3 rounded-lg transition-all duration-300 ${
                    currentView === 'leaderboard' 
                      ? 'text-accent-primary bg-accent-primary/10' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </button>
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