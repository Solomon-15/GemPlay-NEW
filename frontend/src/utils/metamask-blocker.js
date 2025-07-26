// Блокировка автоматического подключения к MetaMask
if (typeof window !== 'undefined' && window.ethereum) {
  console.log('⚠️ MetaMask detected - blocking automatic connection');
  
  // Переопределяем функцию connect в MetaMask
  if (window.ethereum.connect) {
    window.ethereum.connect = function() {
      console.log('🚫 MetaMask connection blocked');
      return Promise.reject(new Error('MetaMask connection disabled'));
    };
  }
  
  // Блокируем события
  if (window.ethereum.on) {
    const originalOn = window.ethereum.on;
    window.ethereum.on = function(event, handler) {
      if (event === 'connect' || event === 'accountsChanged') {
        console.log(`🚫 MetaMask event "${event}" blocked`);
        return;
      }
      return originalOn.call(this, event, handler);
    };
  }
  
  // Блокируем request
  if (window.ethereum.request) {
    const originalRequest = window.ethereum.request;
    window.ethereum.request = function(params) {
      if (params && params.method === 'eth_requestAccounts') {
        console.log('🚫 MetaMask account request blocked');
        return Promise.reject(new Error('MetaMask account request disabled'));
      }
      return originalRequest.call(this, params);
    };
  }
}

console.log('✅ MetaMask blocker loaded');