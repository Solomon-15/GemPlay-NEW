
const ConfirmationModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = "Подтверждение действия",
  message = "Вы уверены, что хотите выполнить это действие?",
  confirmText = "Подтвердить",
  cancelText = "Отмена",
  type = "default", // default, danger, warning, success
  loading = false
}) => {
  if (!isOpen) return null;

  const getTypeStyles = () => {
    switch (type) {
      case 'danger':
        return {
          confirmButton: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
          icon: '⚠️',
          iconBg: 'bg-red-100',
          iconColor: 'text-red-600'
        };
      case 'warning':
        return {
          confirmButton: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
          icon: '⚠️',
          iconBg: 'bg-yellow-100',
          iconColor: 'text-yellow-600'
        };
      case 'success':
        return {
          confirmButton: 'bg-green-600 hover:bg-green-700 focus:ring-green-500',
          icon: '✓',
          iconBg: 'bg-green-100',
          iconColor: 'text-green-600'
        };
      default:
        return {
          confirmButton: 'bg-accent-primary hover:bg-accent-primary/80 focus:ring-accent-primary',
          icon: '?',
          iconBg: 'bg-accent-primary/10',
          iconColor: 'text-accent-primary'
        };
    }
  };

  const typeStyles = getTypeStyles();

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
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
        {/* Header with icon */}
        <div className="p-6">
          <div className="flex items-center">
            <div className={`mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full ${typeStyles.iconBg} sm:mx-0 sm:h-10 sm:w-10`}>
              <span className={`text-xl ${typeStyles.iconColor}`}>
                {typeStyles.icon}
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
            <div className="text-sm text-text-secondary font-roboto leading-relaxed">
              {message}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 py-4 bg-surface-sidebar bg-opacity-50 rounded-b-lg flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-3 space-y-3 space-y-reverse sm:space-y-0">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="w-full sm:w-auto px-4 py-2 border border-border-primary text-text-secondary bg-surface-primary hover:bg-surface-sidebar focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent-primary focus:ring-offset-surface-card rounded-md transition-colors font-roboto font-medium disabled:opacity-50"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className={`w-full sm:w-auto px-4 py-2 border border-transparent rounded-md shadow-sm text-white font-roboto font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-surface-card transition-colors disabled:opacity-50 ${typeStyles.confirmButton}`}
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Выполняется...
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

export default ConfirmationModal;