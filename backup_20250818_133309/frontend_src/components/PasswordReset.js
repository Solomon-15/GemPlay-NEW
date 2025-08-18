import React, { useState } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const PasswordReset = ({ onBackToLogin }) => {
  const [step, setStep] = useState('request'); // 'request' or 'confirm'
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const showSuccess = (msg) => {
    setMessage(msg);
    setError('');
  };

  const showError = (msg) => {
    setError(msg);
    setMessage('');
  };

  const handleRequestReset = async (e) => {
    e.preventDefault();
    if (!email.trim()) {
      showError('Введите email адрес');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/request-password-reset`, {
        email: email.trim()
      });

      showSuccess('Если email существует в системе, на него отправлено письмо для сброса пароля');
      setStep('confirm');
    } catch (error) {
      console.error('Password reset request error:', error);
      showError(error.response?.data?.detail || 'Произошла ошибка при отправке запроса');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmReset = async (e) => {
    e.preventDefault();
    
    if (!token.trim()) {
      showError('Введите токен из письма');
      return;
    }
    
    if (!newPassword) {
      showError('Введите новый пароль');
      return;
    }
    
    if (newPassword.length < 8) {
      showError('Пароль должен содержать минимум 8 символов');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      showError('Пароли не совпадают');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/reset-password`, {
        token: token.trim(),
        new_password: newPassword
      });

      showSuccess('Пароль успешно изменён! Теперь вы можете войти с новым паролем');
      setTimeout(() => {
        onBackToLogin();
      }, 2000);
    } catch (error) {
      console.error('Password reset error:', error);
      showError(error.response?.data?.detail || 'Произошла ошибка при сбросе пароля');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'request') {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-accent-primary font-rajdhani mb-2">
              GemPlay
            </h1>
            <h2 className="text-2xl font-semibold text-white font-rajdhani mb-6">
              Восстановление пароля
            </h2>
            <p className="text-text-secondary text-sm">
              Введите ваш email адрес, и мы отправим вам ссылку для сброса пароля
            </p>
          </div>

          {/* Success/Error Messages */}
          {message && (
            <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4 mb-4">
              <p className="text-green-300 text-sm font-roboto">{message}</p>
            </div>
          )}
          {error && (
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 mb-4">
              <p className="text-red-300 text-sm font-roboto">{error}</p>
            </div>
          )}

          <form onSubmit={handleRequestReset} className="space-y-6">
            <div>
              <label htmlFor="email" className="sr-only">
                Email адрес
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
                placeholder="Email адрес"
                required
                disabled={loading}
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className={`w-full py-3 px-4 font-bold text-sm font-rajdhani rounded-lg transition-colors ${
                  loading
                    ? 'bg-gray-600 text-gray-300 cursor-not-allowed'
                    : 'bg-accent-primary text-white hover:bg-accent-primary/90'
                }`}
              >
                {loading ? 'ОТПРАВКА...' : 'ОТПРАВИТЬ ССЫЛКУ'}
              </button>
            </div>

            <div className="text-center">
              <button
                type="button"
                onClick={onBackToLogin}
                className="text-accent-primary hover:text-accent-primary/80 font-roboto text-sm font-medium"
              >
                ← Вернуться к входу
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-primary flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-accent-primary font-rajdhani mb-2">
            GemPlay
          </h1>
          <h2 className="text-2xl font-semibold text-white font-rajdhani mb-6">
            Новый пароль
          </h2>
          <p className="text-text-secondary text-sm">
            Введите токен из письма и новый пароль
          </p>
        </div>

        {/* Success/Error Messages */}
        {message && (
          <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4 mb-4">
            <p className="text-green-300 text-sm font-roboto">{message}</p>
          </div>
        )}
        {error && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 mb-4">
            <p className="text-red-300 text-sm font-roboto">{error}</p>
          </div>
        )}

        <form onSubmit={handleConfirmReset} className="space-y-6">
          <div>
            <label htmlFor="token" className="sr-only">
              Токен из письма
            </label>
            <input
              id="token"
              name="token"
              type="text"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="w-full px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
              placeholder="Токен из письма"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="new-password" className="sr-only">
              Новый пароль
            </label>
            <input
              id="new-password"
              name="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
              placeholder="Новый пароль (минимум 8 символов)"
              required
              disabled={loading}
              minLength={8}
            />
          </div>

          <div>
            <label htmlFor="confirm-password" className="sr-only">
              Подтверждение пароля
            </label>
            <input
              id="confirm-password"
              name="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-white font-roboto focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-accent-primary"
              placeholder="Подтвердите новый пароль"
              required
              disabled={loading}
              minLength={8}
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3 px-4 font-bold text-sm font-rajdhani rounded-lg transition-colors ${
                loading
                  ? 'bg-gray-600 text-gray-300 cursor-not-allowed'
                  : 'bg-accent-primary text-white hover:bg-accent-primary/90'
              }`}
            >
              {loading ? 'СОХРАНЕНИЕ...' : 'ИЗМЕНИТЬ ПАРОЛЬ'}
            </button>
          </div>

          <div className="text-center space-y-2">
            <button
              type="button"
              onClick={() => setStep('request')}
              className="block mx-auto text-text-secondary hover:text-white font-roboto text-sm"
            >
              ← Запросить новое письмо
            </button>
            <button
              type="button"
              onClick={onBackToLogin}
              className="block mx-auto text-accent-primary hover:text-accent-primary/80 font-roboto text-sm font-medium"
            >
              ← Вернуться к входу
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PasswordReset;