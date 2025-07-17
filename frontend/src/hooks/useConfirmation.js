import { useState } from 'react';

const useConfirmation = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [config, setConfig] = useState({});
  const [loading, setLoading] = useState(false);
  const [resolvePromise, setResolvePromise] = useState(null);

  const confirm = (options = {}) => {
    return new Promise((resolve) => {
      setConfig({
        title: options.title || "Подтверждение действия",
        message: options.message || "Вы уверены, что хотите выполнить это действие?",
        confirmText: options.confirmText || "Подтвердить",
        cancelText: options.cancelText || "Отмена",
        type: options.type || "default",
        ...options
      });
      setResolvePromise(() => resolve);
      setIsOpen(true);
    });
  };

  const handleConfirm = async () => {
    if (config.onConfirm) {
      setLoading(true);
      try {
        await config.onConfirm();
        setLoading(false);
        setIsOpen(false);
        if (resolvePromise) resolvePromise(true);
      } catch (error) {
        setLoading(false);
        console.error('Error in confirmation action:', error);
        // Не закрываем модальное окно при ошибке
      }
    } else {
      setIsOpen(false);
      if (resolvePromise) resolvePromise(true);
    }
  };

  const handleCancel = () => {
    setIsOpen(false);
    setLoading(false);
    if (resolvePromise) resolvePromise(false);
  };

  return {
    confirm,
    confirmationModal: {
      isOpen,
      onClose: handleCancel,
      onConfirm: handleConfirm,
      loading,
      ...config
    }
  };
};

export default useConfirmation;