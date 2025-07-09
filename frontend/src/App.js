import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import Shop from "./components/Shop";
import Inventory from "./components/Inventory";
import SecurityMonitoring from "./components/SecurityMonitoring";

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
        const response = await axios.post(`${API}/auth/login`, {
          email: formData.email,
          password: formData.password
        });
        
        localStorage.setItem('token', response.data.access_token);
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
  const [currentView, setCurrentView] = useState('shop');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  };

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setCurrentView('shop');
  };

  const handleClaimDailyBonus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/auth/daily-bonus`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert(response.data.message);
      checkAuthStatus(); // Refresh user data
    } catch (error) {
      alert(error.response?.data?.detail || 'Error claiming daily bonus');
    }
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
    <div className="min-h-screen bg-gradient-primary">
      {/* Navigation */}
      <nav className="bg-surface-sidebar border-b border-border-primary p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <h1 className="font-russo text-2xl text-accent-primary">GemPlay</h1>
            
            <div className="flex space-x-4">
              <button
                onClick={() => setCurrentView('shop')}
                className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
                  currentView === 'shop' 
                    ? 'bg-accent-primary text-white' 
                    : 'text-text-secondary hover:text-white'
                }`}
              >
                SHOP
              </button>
              
              <button
                onClick={() => setCurrentView('inventory')}
                className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
                  currentView === 'inventory' 
                    ? 'bg-accent-primary text-white' 
                    : 'text-text-secondary hover:text-white'
                }`}
              >
                INVENTORY
              </button>

              {/* Admin Monitoring Section */}
              {user.role === 'ADMIN' || user.role === 'SUPER_ADMIN' ? (
                <button
                  onClick={() => setCurrentView('monitoring')}
                  className={`px-4 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
                    currentView === 'monitoring' 
                      ? 'bg-red-600 text-white' 
                      : 'text-red-400 hover:text-white'
                  }`}
                >
                  🛡️ МОНИТОРИНГ
                </button>
              ) : null}
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="font-roboto text-text-secondary text-sm">Welcome, {user.username}</p>
              <p className="font-rajdhani text-green-400 font-bold">
                ${user.virtual_balance?.toFixed(2) || '0.00'}
              </p>
            </div>
            
            <button
              onClick={handleClaimDailyBonus}
              className="px-4 py-2 bg-gradient-accent text-white font-rajdhani font-bold rounded-lg hover:opacity-90 transition-opacity text-sm"
            >
              DAILY BONUS
            </button>
            
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white font-rajdhani font-bold rounded-lg hover:bg-red-700 transition-colors text-sm"
            >
              LOGOUT
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="min-h-screen">
        {currentView === 'shop' && (
          <Shop user={user} onUpdateUser={checkAuthStatus} />
        )}
        {currentView === 'inventory' && (
          <Inventory user={user} onUpdateUser={checkAuthStatus} />
        )}
        {currentView === 'monitoring' && (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') && (
          <SecurityMonitoring user={user} />
        )}
      </div>
    </div>
  );
}

export default App;