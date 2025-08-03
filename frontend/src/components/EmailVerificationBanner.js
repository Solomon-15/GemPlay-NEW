import React, { useState } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';

const API = process.env.REACT_APP_BACKEND_URL;

const EmailVerificationBanner = ({ userEmail, onVerificationSent }) => {
  const [loading, setLoading] = useState(false);
  const { showSuccess, showError } = useNotifications();

  const handleResendVerification = async () => {
    if (!userEmail) {
      showError('Email адрес не найден');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/resend-verification`, {
        email: userEmail
      });

      showSuccess('Письмо подтверждения отправлено повторно. Проверьте вашу почту.');
      
      if (onVerificationSent) {
        onVerificationSent();
      }
    } catch (error) {
      console.error('Resend verification error:', error);
      showError(error.response?.data?.detail || 'Не удалось отправить письмо подтверждения');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4 mb-6">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-yellow-400 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-yellow-300 font-rajdhani">
            Требуется подтверждение email
          </h3>
          <p className="text-sm text-yellow-200 mt-1 font-roboto">
            Мы отправили письмо подтверждения на{' '}
            <span className="font-medium text-yellow-100">{userEmail}</span>.
            Пожалуйста, проверьте вашу почту (включая папку "Спам") и перейдите по ссылке для активации аккаунта.
          </p>
          <div className="mt-3">
            <button
              type="button"
              onClick={handleResendVerification}
              disabled={loading}
              className={`text-sm font-medium font-roboto rounded-md px-3 py-1.5 transition-colors ${
                loading
                  ? 'bg-gray-600 text-gray-300 cursor-not-allowed'
                  : 'bg-yellow-600 text-white hover:bg-yellow-700'
              }`}
            >
              {loading ? 'Отправка...' : 'Отправить повторно'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailVerificationBanner;