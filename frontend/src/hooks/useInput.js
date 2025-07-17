import { useState } from 'react';

const useInput = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [config, setConfig] = useState({});
  const [loading, setLoading] = useState(false);
  const [resolvePromise, setResolvePromise] = useState(null);

  const prompt = (options = {}) => {
    return new Promise((resolve) => {
      setConfig({
        title: options.title || "Введите значение",
        message: options.message || "Пожалуйста, введите требуемое значение:",
        placeholder: options.placeholder || "Введите значение...",
        confirmText: options.confirmText || "Подтвердить",
        cancelText: options.cancelText || "Отмена",
        type: options.type || "text",
        min: options.min,
        max: options.max,
        ...options
      });
      setResolvePromise(() => resolve);
      setIsOpen(true);
    });
  };

  const handleConfirm = async (value) => {
    if (config.onConfirm) {
      setLoading(true);
      try {
        await config.onConfirm(value);
        setLoading(false);
        setIsOpen(false);
        if (resolvePromise) resolvePromise(value);
      } catch (error) {
        setLoading(false);
        console.error('Error in input action:', error);
        // Не закрываем модальное окно при ошибке
      }
    } else {
      setIsOpen(false);
      if (resolvePromise) resolvePromise(value);
    }
  };

  const handleCancel = () => {
    setIsOpen(false);
    setLoading(false);
    if (resolvePromise) resolvePromise(null);
  };

  return {
    prompt,
    inputModal: {
      isOpen,
      onClose: handleCancel,
      onConfirm: handleConfirm,
      loading,
      ...config
    }
  };
};

export default useInput;