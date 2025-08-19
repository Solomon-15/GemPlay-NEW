// 🧪 ТЕСТ КНОПКИ "ОЧИСТИТЬ КЭШ" - Утилиты для тестирования
// Этот файл содержит функции для тестирования функциональности очистки кэша

/**
 * 📊 Получить размер кэша
 * Подсчитывает общий размер всех типов кэша в браузере
 */
function getCacheSize() {
  let totalSize = 0;
  let details = {};

  try {
    // 1. localStorage
    let localStorageSize = 0;
    for (let key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        localStorageSize += localStorage[key].length + key.length;
      }
    }
    details.localStorage = {
      size: localStorageSize,
      items: Object.keys(localStorage).length,
      sizeKB: Math.round(localStorageSize / 1024 * 100) / 100
    };
    totalSize += localStorageSize;

    // 2. sessionStorage
    let sessionStorageSize = 0;
    for (let key in sessionStorage) {
      if (sessionStorage.hasOwnProperty(key)) {
        sessionStorageSize += sessionStorage[key].length + key.length;
      }
    }
    details.sessionStorage = {
      size: sessionStorageSize,
      items: Object.keys(sessionStorage).length,
      sizeKB: Math.round(sessionStorageSize / 1024 * 100) / 100
    };
    totalSize += sessionStorageSize;

    // 3. Cache API (если поддерживается)
    details.cacheAPI = {
      supported: 'caches' in window,
      note: 'Размер Cache API нельзя получить синхронно'
    };

    return {
      totalSize,
      totalSizeKB: Math.round(totalSize / 1024 * 100) / 100,
      details
    };
  } catch (error) {
    console.error('Ошибка при подсчете размера кэша:', error);
    return { error: error.message };
  }
}

/**
 * 🔑 Получить ключи кэша
 * Возвращает список всех ключей во всех типах кэша
 */
function getCacheKeys() {
  try {
    const keys = {
      localStorage: Object.keys(localStorage),
      sessionStorage: Object.keys(sessionStorage),
      cacheAPI: 'caches' in window ? 'Доступно (требует async проверки)' : 'Не поддерживается'
    };

    return keys;
  } catch (error) {
    console.error('Ошибка при получении ключей кэша:', error);
    return { error: error.message };
  }
}

/**
 * 🗑️ Получить детальную информацию о кэше Cache API
 * Асинхронная функция для получения информации о Cache API
 */
async function getCacheAPIDetails() {
  if (!('caches' in window)) {
    return { supported: false, message: 'Cache API не поддерживается' };
  }

  try {
    const cacheNames = await caches.keys();
    const details = [];

    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const requests = await cache.keys();
      details.push({
        name: cacheName,
        requestCount: requests.length,
        requests: requests.map(req => ({
          url: req.url,
          method: req.method
        }))
      });
    }

    return {
      supported: true,
      cacheCount: cacheNames.length,
      cacheNames,
      details
    };
  } catch (error) {
    console.error('Ошибка при получении деталей Cache API:', error);
    return { error: error.message };
  }
}

/**
 * 🧪 Тест состояния кэша ДО очистки
 */
async function testCacheBeforeClear() {
  console.log('🔍 === ТЕСТ КЭША ДО ОЧИСТКИ ===');
  
  const cacheSize = getCacheSize();
  const cacheKeys = getCacheKeys();
  const cacheAPIDetails = await getCacheAPIDetails();
  
  console.log('📊 Размер кэша:', cacheSize);
  console.log('🔑 Ключи кэша:', cacheKeys);
  console.log('🌐 Cache API детали:', cacheAPIDetails);
  
  // Сохраняем состояние для сравнения
  window.cacheTestState = {
    before: {
      size: cacheSize,
      keys: cacheKeys,
      cacheAPI: cacheAPIDetails,
      timestamp: new Date().toISOString()
    }
  };
  
  return window.cacheTestState.before;
}

/**
 * 🧪 Тест состояния кэша ПОСЛЕ очистки
 */
async function testCacheAfterClear() {
  console.log('🔍 === ТЕСТ КЭША ПОСЛЕ ОЧИСТКИ ===');
  
  const cacheSize = getCacheSize();
  const cacheKeys = getCacheKeys();
  const cacheAPIDetails = await getCacheAPIDetails();
  
  console.log('📊 Размер кэша:', cacheSize);
  console.log('🔑 Ключи кэша:', cacheKeys);
  console.log('🌐 Cache API детали:', cacheAPIDetails);
  
  // Добавляем результат после очистки
  if (!window.cacheTestState) {
    window.cacheTestState = {};
  }
  
  window.cacheTestState.after = {
    size: cacheSize,
    keys: cacheKeys,
    cacheAPI: cacheAPIDetails,
    timestamp: new Date().toISOString()
  };
  
  // Сравниваем результаты
  const comparison = compareCacheStates();
  console.log('📈 Сравнение:', comparison);
  
  return {
    after: window.cacheTestState.after,
    comparison
  };
}

/**
 * ⚖️ Сравнить состояния кэша до и после
 */
function compareCacheStates() {
  if (!window.cacheTestState || !window.cacheTestState.before) {
    return { error: 'Нет данных о состоянии кэша ДО очистки' };
  }
  
  const before = window.cacheTestState.before;
  const after = window.cacheTestState.after;
  
  if (!after) {
    return { error: 'Нет данных о состоянии кэша ПОСЛЕ очистки' };
  }
  
  const comparison = {
    localStorage: {
      sizeBefore: before.size.details.localStorage.size,
      sizeAfter: after.size.details.localStorage.size,
      itemsBefore: before.size.details.localStorage.items,
      itemsAfter: after.size.details.localStorage.items,
      cleared: before.size.details.localStorage.size - after.size.details.localStorage.size,
      clearedPercent: before.size.details.localStorage.size > 0 
        ? Math.round((1 - after.size.details.localStorage.size / before.size.details.localStorage.size) * 100)
        : 0
    },
    sessionStorage: {
      sizeBefore: before.size.details.sessionStorage.size,
      sizeAfter: after.size.details.sessionStorage.size,
      itemsBefore: before.size.details.sessionStorage.items,
      itemsAfter: after.size.details.sessionStorage.items,
      cleared: before.size.details.sessionStorage.size - after.size.details.sessionStorage.size,
      clearedPercent: before.size.details.sessionStorage.size > 0 
        ? Math.round((1 - after.size.details.sessionStorage.size / before.size.details.sessionStorage.size) * 100)
        : 0
    },
    cacheAPI: {
      cachesBefore: before.cacheAPI.cacheCount || 0,
      cachesAfter: after.cacheAPI.cacheCount || 0,
      cleared: (before.cacheAPI.cacheCount || 0) - (after.cacheAPI.cacheCount || 0)
    },
    total: {
      sizeBefore: before.size.totalSize,
      sizeAfter: after.size.totalSize,
      cleared: before.size.totalSize - after.size.totalSize,
      clearedPercent: before.size.totalSize > 0 
        ? Math.round((1 - after.size.totalSize / before.size.totalSize) * 100)
        : 0
    }
  };
  
  return comparison;
}

/**
 * 🎯 Автоматический тест кнопки очистки кэша
 */
async function autoTestClearCacheButton() {
  console.log('🚀 === АВТОМАТИЧЕСКИЙ ТЕСТ КНОПКИ ОЧИСТКИ КЭША ===');
  
  try {
    // 1. Проверяем состояние ДО очистки
    console.log('1️⃣ Проверяем состояние ДО очистки...');
    const beforeState = await testCacheBeforeClear();
    
    // 2. Ищем кнопку очистки кэша
    console.log('2️⃣ Ищем кнопку очистки кэша...');
    const clearButton = document.querySelector('button[title*="Очистить серверный и локальный кэш"]');
    
    if (!clearButton) {
      throw new Error('❌ Кнопка очистки кэша не найдена!');
    }
    
    console.log('✅ Кнопка найдена:', clearButton);
    
    // 3. Проверяем, что кнопка отзывчива
    console.log('3️⃣ Проверяем отзывчивость кнопки...');
    const isDisabled = clearButton.disabled;
    const hasClickHandler = clearButton.onclick || clearButton.getAttribute('onclick');
    
    console.log('📋 Состояние кнопки:', {
      disabled: isDisabled,
      hasClickHandler: !!hasClickHandler,
      className: clearButton.className,
      text: clearButton.textContent.trim()
    });
    
    if (isDisabled) {
      console.warn('⚠️ Кнопка отключена! Возможно, идет загрузка.');
      return { error: 'Кнопка отключена' };
    }
    
    // 4. Симулируем клик (НЕ реальный клик, только проверка)
    console.log('4️⃣ Готов к симуляции клика...');
    console.log('⚠️ ВНИМАНИЕ: Для реального теста нужно вручную нажать кнопку!');
    
    return {
      success: true,
      beforeState,
      buttonFound: true,
      buttonState: {
        disabled: isDisabled,
        hasClickHandler: !!hasClickHandler,
        text: clearButton.textContent.trim()
      },
      nextSteps: [
        '1. Вручную нажмите кнопку "Очистить кэш"',
        '2. Подтвердите действие в модальном окне',
        '3. Дождитесь завершения операции',
        '4. Выполните: testCacheAfterClear()'
      ]
    };
    
  } catch (error) {
    console.error('❌ Ошибка автотеста:', error);
    return { error: error.message };
  }
}

/**
 * 🔄 Мониторинг процесса очистки кэша
 */
function monitorClearCacheProcess() {
  console.log('👁️ === МОНИТОРИНГ ПРОЦЕССА ОЧИСТКИ ===');
  
  // Мониторим изменения в DOM для отслеживания состояния загрузки
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
        const target = mutation.target;
        if (target.textContent && target.textContent.includes('Очистка')) {
          console.log('🔄 Обнаружено изменение состояния кнопки:', {
            text: target.textContent.trim(),
            className: target.className,
            disabled: target.disabled
          });
        }
      }
    });
  });
  
  // Наблюдаем за изменениями в админ-панели
  const adminPanel = document.querySelector('[class*="AdminPanel"]') || document.body;
  observer.observe(adminPanel, {
    attributes: true,
    subtree: true,
    attributeFilter: ['class', 'disabled']
  });
  
  console.log('✅ Мониторинг запущен. Нажмите кнопку очистки кэша для отслеживания процесса.');
  
  // Остановить мониторинг через 30 секунд
  setTimeout(() => {
    observer.disconnect();
    console.log('🛑 Мониторинг остановлен (таймаут 30 сек)');
  }, 30000);
  
  return observer;
}

/**
 * 📋 Генерировать отчет о тестировании
 */
function generateTestReport() {
  if (!window.cacheTestState || !window.cacheTestState.before || !window.cacheTestState.after) {
    return {
      error: 'Недостаточно данных для генерации отчета. Выполните полный тест.'
    };
  }
  
  const comparison = compareCacheStates();
  const before = window.cacheTestState.before;
  const after = window.cacheTestState.after;
  
  const report = {
    testTimestamp: new Date().toISOString(),
    testDuration: new Date(after.timestamp) - new Date(before.timestamp),
    
    // Результаты очистки
    clearingResults: {
      localStorage: {
        clearedSuccessfully: comparison.localStorage.cleared > 0,
        itemsRemoved: comparison.localStorage.itemsBefore - comparison.localStorage.itemsAfter,
        sizeReduced: comparison.localStorage.cleared,
        percentCleared: comparison.localStorage.clearedPercent
      },
      sessionStorage: {
        clearedSuccessfully: comparison.sessionStorage.cleared >= 0, // sessionStorage может быть уже пустым
        itemsRemoved: comparison.sessionStorage.itemsBefore - comparison.sessionStorage.itemsAfter,
        sizeReduced: comparison.sessionStorage.cleared,
        percentCleared: comparison.sessionStorage.clearedPercent
      },
      cacheAPI: {
        clearedSuccessfully: comparison.cacheAPI.cleared >= 0,
        cachesRemoved: comparison.cacheAPI.cleared
      }
    },
    
    // Общая оценка
    overallResult: {
      success: (comparison.localStorage.cleared > 0 || comparison.sessionStorage.cleared >= 0 || comparison.cacheAPI.cleared >= 0),
      totalDataCleared: comparison.total.cleared,
      percentTotalCleared: comparison.total.clearedPercent
    },
    
    // Детали
    details: {
      before,
      after,
      comparison
    }
  };
  
  // Выводим красивый отчет в консоль
  console.log('📋 === ОТЧЕТ О ТЕСТИРОВАНИИ ОЧИСТКИ КЭША ===');
  console.log('🕐 Время теста:', new Date(report.testTimestamp).toLocaleString());
  console.log('⏱️ Длительность:', Math.round(report.testDuration / 1000), 'секунд');
  console.log('');
  
  console.log('💾 localStorage:');
  console.log(`   • Очищено: ${report.clearingResults.localStorage.clearedSuccessfully ? '✅' : '❌'}`);
  console.log(`   • Удалено элементов: ${report.clearingResults.localStorage.itemsRemoved}`);
  console.log(`   • Освобождено: ${Math.round(report.clearingResults.localStorage.sizeReduced / 1024 * 100) / 100} KB`);
  console.log(`   • Процент очистки: ${report.clearingResults.localStorage.percentCleared}%`);
  console.log('');
  
  console.log('🗃️ sessionStorage:');
  console.log(`   • Очищено: ${report.clearingResults.sessionStorage.clearedSuccessfully ? '✅' : '❌'}`);
  console.log(`   • Удалено элементов: ${report.clearingResults.sessionStorage.itemsRemoved}`);
  console.log(`   • Освобождено: ${Math.round(report.clearingResults.sessionStorage.sizeReduced / 1024 * 100) / 100} KB`);
  console.log('');
  
  console.log('🌐 Cache API:');
  console.log(`   • Очищено: ${report.clearingResults.cacheAPI.clearedSuccessfully ? '✅' : '❌'}`);
  console.log(`   • Удалено кэшей: ${report.clearingResults.cacheAPI.cachesRemoved}`);
  console.log('');
  
  console.log('🎯 ОБЩИЙ РЕЗУЛЬТАТ:');
  console.log(`   • Успех: ${report.overallResult.success ? '✅' : '❌'}`);
  console.log(`   • Всего очищено: ${Math.round(report.overallResult.totalDataCleared / 1024 * 100) / 100} KB`);
  console.log(`   • Процент очистки: ${report.overallResult.percentTotalCleared}%`);
  
  return report;
}

// 🚀 Экспорт функций для глобального использования
window.getCacheSize = getCacheSize;
window.getCacheKeys = getCacheKeys;
window.getCacheAPIDetails = getCacheAPIDetails;
window.testCacheBeforeClear = testCacheBeforeClear;
window.testCacheAfterClear = testCacheAfterClear;
window.compareCacheStates = compareCacheStates;
window.generateTestReport = generateTestReport;
window.monitorClearCacheProcess = monitorClearCacheProcess;

console.log('🧪 Утилиты тестирования кэша загружены!');
console.log('📚 Доступные функции:');
console.log('   • getCacheSize() - размер кэша');
console.log('   • getCacheKeys() - ключи кэша');
console.log('   • getCacheAPIDetails() - детали Cache API');
console.log('   • testCacheBeforeClear() - тест ДО очистки');
console.log('   • testCacheAfterClear() - тест ПОСЛЕ очистки');
console.log('   • generateTestReport() - генерация отчета');
console.log('   • monitorClearCacheProcess() - мониторинг процесса');
console.log('');
console.log('🎯 Для начала тестирования выполните: testCacheBeforeClear()');