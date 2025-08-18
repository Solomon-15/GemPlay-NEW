import React, { useState } from 'react';

const InputModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = "Введите значение",
  message = "Пожалуйста, введите требуемое значение:",
  placeholder = "Введите значение...",
  confirmText = "Подтвердить",
  cancelText = "Отмена",
  type = "text", // text, number
  min,
  max,
  loading = false
}) => {
  const [value, setValue] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const validateInput = (inputValue) => {
    if (!inputValue.trim()) {
      return 'Поле не может быть пустым';
    }
    
    if (type === 'number') {
      const num = parseFloat(inputValue);
      if (isNaN(num)) {
        return 'Введите корректное число';
      }
      if (min !== undefined && num < min) {
        return `Значение должно быть не менее ${min}`;
      }
      if (max !== undefined && num > max) {
        return `Значение должно быть не более ${max}`;
      }
    }
    
    return null;
  };

  const handleSubmit = () => {
    const validationError = validateInput(value);
    if (validationError) {
      setError(validationError);
      return;
    }
    
    onConfirm(type === 'number' ? parseFloat(value) : value);
    setValue('');
    setError('');
  };

  const handleClose = () => {
    setValue('');
    setError('');
    onClose();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-75 transition-opacity"
        onClick={handleBackdropClick}
      />
      
      {/* Modal */}
      <div className="relative bg-surface-card border border-accent-primary border-opacity-30 rounded-lg shadow-xl max-w-md w-full mx-4 transform transition-all">
        {/* Header */}
        <div className="p-6">
          <div className="flex items-center">
            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-accent-primary bg-opacity-10 sm:mx-0 sm:h-10 sm:w-10">
              <span className="text-xl text-accent-primary">
                ✏️
              </span>
            </div>
            <div className="ml-4 text-left">
              <h3 className="text-lg leading-6 font-rajdhani font-bold text-white">
                {title}
              </h3>
            </div>
          </div>
          
          {/* Message */}
          <div className="mt-4">
            <div className="text-sm text-text-secondary font-roboto leading-relaxed mb-4">
              {message}
            </div>
            
            {/* Input */}
            <div className="space-y-2">
              <input
                type={type}
                value={value}
                onChange={(e) => {
                  setValue(e.target.value);
                  setError(''); // Сброс ошибки при изменении
                }}
                onKeyPress={handleKeyPress}
                placeholder={placeholder}
                min={min}
                max={max}
                className="w-full px-3 py-2 border border-border-primary bg-surface-primary text-white rounded-md focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent font-roboto"
                autoFocus
              />
              
              {/* Error message */}
              {error && (
                <p className="text-red-400 text-xs font-roboto mt-1">
                  {error}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 py-4 bg-surface-sidebar bg-opacity-50 rounded-b-lg flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-3 space-y-3 space-y-reverse sm:space-y-0">
          <button
            type="button"
            onClick={handleClose}
            disabled={loading}
            className="w-full sm:w-auto px-4 py-2 border border-border-primary text-text-secondary bg-surface-primary hover:bg-surface-sidebar focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-primary focus:ring-offset-surface-card rounded-md transition-colors font-roboto font-medium disabled:opacity-50"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading || !value.trim()}
            className="w-full sm:w-auto px-4 py-2 border border-transparent rounded-md shadow-sm text-white font-roboto font-medium bg-accent-primary hover:bg-accent-primary/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-primary focus:ring-offset-surface-card transition-colors disabled:opacity-50"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Обработка...
              </div>
            ) : (
              confirmText
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default InputModal;