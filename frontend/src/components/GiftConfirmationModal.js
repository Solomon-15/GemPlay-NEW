import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import { formatDollarAmount, formatGemValue } from '../utils/economy';
import { getGlobalLobbyRefresh } from '../hooks/useLobbyRefresh';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const useCommissionSettings = () => {
  const [settings, setSettings] = React.useState({ bet_commission_rate: 3.0, gift_commission_rate: 3.0 });
  React.useEffect(() => {
    const fetchSettings = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`${API}/admin/profit/commission-settings`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.data) setSettings(res.data);
      } catch (e) {
        // keep defaults
      }
    };
    fetchSettings();
  }, []);
  return settings;
};

const GiftConfirmationModal = ({ 
  isOpen, 
  onClose, 
  gemType, 
  quantity, 
  gemPrice, 
  senderName, 
  senderEmail,
  onGiftSuccess 
}) => {
  const { showSuccess, showError } = useNotifications();
  const [recipientIdentifier, setRecipientIdentifier] = useState('');
  const [recipientInfo, setRecipientInfo] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isGifting, setIsGifting] = useState(false);
  const [searchTimer, setSearchTimer] = useState(null);

  const totalValue = gemPrice * quantity;
  const commission = totalValue * 0.03; // 3% комиссия
  const finalValue = totalValue; // Получатель получает полную стоимость

  const searchRecipient = async (identifier) => {
    if (!identifier.trim()) {
      setRecipientInfo(null);
      return;
    }

    setIsValidating(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/users/search?query=${encodeURIComponent(identifier)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data && response.data.length > 0) {
        setRecipientInfo(response.data[0]);
      } else {
        setRecipientInfo(null);
      }
    } catch (error) {
      console.error('Error searching recipient:', error);
      setRecipientInfo(null);
    } finally {
      setIsValidating(false);
    }
  };

  useEffect(() => {
    if (searchTimer) {
      clearTimeout(searchTimer);
    }

    const timer = setTimeout(() => {
      searchRecipient(recipientIdentifier);
    }, 500);

    setSearchTimer(timer);

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [recipientIdentifier]);

  const handleGift = async () => {
    if (!recipientInfo) {
      showError('Please select a valid recipient');
      return;
    }

    if (recipientInfo.email === senderEmail) {
      showError('Cannot send a gift to yourself');
      return;
    }

    setIsGifting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/gems/gift?recipient_email=${recipientInfo.email}&gem_type=${gemType}&quantity=${quantity}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      showSuccess(`You sent a gift to ${recipientInfo.username}. A commission of ${formatDollarAmount(commission)} has been deducted from your balance.`);
      
      const globalRefresh = getGlobalLobbyRefresh();
      globalRefresh.triggerLobbyRefresh();
      
      if (onGiftSuccess) {
        onGiftSuccess();
      }
      
      onClose();
    } catch (error) {
      showError(error.response?.data?.detail || 'Error sending gift');
    } finally {
      setIsGifting(false);
    }
  };

  // Lock body scroll when modal is open (prevents background jumps)
  useEffect(() => {
    if (!isOpen) return;
    const { body } = document;
    const prevOverflow = body.style.overflow;
    const prevPaddingRight = body.style.paddingRight;
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
    if (scrollbarWidth > 0) body.style.paddingRight = `${scrollbarWidth}px`;
    body.style.overflow = 'hidden';
    return () => {
      body.style.overflow = prevOverflow || 'unset';
      body.style.paddingRight = prevPaddingRight || '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onWheel={(e)=>e.stopPropagation()} onTouchMove={(e)=>e.stopPropagation()}>
      <div className="bg-surface-card border border-accent-primary border-opacity-30 rounded-lg p-6 max-w-md w-full" role="dialog" aria-modal="true">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="font-russo text-xl text-accent-primary">🎁 Gift Confirmation</h3>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Sender Info */}
        <div className="mb-4 p-3 bg-surface-sidebar rounded-lg">
          <div className="text-sm text-text-secondary mb-1">From:</div>
          <div className="text-white font-rajdhani font-semibold">{senderName} ({senderEmail})</div>
        </div>

        {/* Recipient Search */}
        <div className="mb-4">
          <label className="block text-sm text-text-secondary mb-2">
            To (email or username):
          </label>
          <div className="relative">
            <input
              type="text"
              value={recipientIdentifier}
              onChange={(e) => setRecipientIdentifier(e.target.value)}
              placeholder="Enter recipient's email or username..."
              className="w-full px-3 py-2 bg-surface-sidebar border border-border-primary rounded-lg text-white focus:border-accent-primary focus:outline-none"
            />
            {isValidating && (
              <div className="absolute right-3 top-2.5">
                <div className="w-4 h-4 border-2 border-accent-primary border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}
          </div>
          
          {/* Recipient Info */}
          {recipientInfo && (
            <div className="mt-2 p-3 bg-green-900 bg-opacity-20 border border-green-500 border-opacity-30 rounded-lg">
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <div>
                  <div className="text-green-400 font-medium">{recipientInfo.username}</div>
                  <div className="text-xs text-text-secondary">{recipientInfo.email}</div>
                </div>
              </div>
            </div>
          )}
          
          {recipientIdentifier && !recipientInfo && !isValidating && (
            <div className="mt-2 p-3 bg-red-900 bg-opacity-20 border border-red-500 border-opacity-30 rounded-lg">
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                <div className="text-red-400 text-sm">User not found</div>
              </div>
            </div>
          )}
        </div>

        {/* Gift Details */}
        <div className="mb-6 p-4 bg-surface-sidebar rounded-lg">
          <h4 className="font-rajdhani font-bold text-white mb-3">Gift Details:</h4>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">Gem:</span>
              <span className="text-white font-medium">{quantity}x {gemType}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-text-secondary">Value:</span>
              <span className="text-white font-medium">{formatGemValue(totalValue)}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-text-secondary">Commission (3%):</span>
              <span className="text-orange-400 font-medium">-{formatDollarAmount(commission)}</span>
            </div>
            
            <div className="border-t border-border-primary pt-2 mt-2">
              <div className="flex justify-between">
                <span className="text-text-secondary">Recipient will receive:</span>
                <span className="text-green-400 font-bold">{quantity}x {gemType} ({formatGemValue(finalValue)})</span>
              </div>
            </div>
          </div>
        </div>

        {/* Warning */}
        <div className="mb-6 p-3 bg-yellow-900 bg-opacity-20 border border-yellow-500 border-opacity-30 rounded-lg">
          <div className="flex items-start space-x-2">
            <svg className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <div className="text-yellow-400 text-sm">
              <div className="font-medium mb-1">Warning!</div>
              <div>This action cannot be undone. Make sure you've entered the correct recipient.</div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-surface-sidebar border border-border-primary rounded-lg text-text-secondary hover:text-white hover:border-accent-primary transition-colors font-rajdhani font-medium"
          >
            Cancel
          </button>
          
          <button
            onClick={handleGift}
            disabled={!recipientInfo || isGifting}
            className={`flex-1 px-4 py-3 rounded-lg font-rajdhani font-bold transition-colors ${
              recipientInfo && !isGifting
                ? 'bg-accent-primary hover:bg-accent-primary/80 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isGifting ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Sending...</span>
              </div>
            ) : (
              'Confirm Gift'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default GiftConfirmationModal;