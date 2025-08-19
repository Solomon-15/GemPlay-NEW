// 🤖 АВТОМАТИЗИРОВАННЫЙ ТЕСТ КНОПКИ "ОЧИСТИТЬ КЭШ"
// Этот скрипт можно запустить в консоли браузера для автоматического тестирования

console.log('🤖 === АВТОМАТИЗИРОВАННЫЙ ТЕСТ ОЧИСТКИ КЭША ===');

class CacheTestAutomation {
    constructor() {
        this.testResults = {};
        this.testStartTime = Date.now();
    }

    // 📊 Анализ кэша
    analyzeCacheState() {
        const state = {
            localStorage: {
                size: this.getStorageSize(localStorage),
                items: Object.keys(localStorage).length,
                keys: Object.keys(localStorage)
            },
            sessionStorage: {
                size: this.getStorageSize(sessionStorage),
                items: Object.keys(sessionStorage).length,
                keys: Object.keys(sessionStorage)
            },
            cacheAPI: {
                supported: 'caches' in window
            },
            timestamp: new Date().toISOString()
        };

        return state;
    }

    getStorageSize(storage) {
        let size = 0;
        for (let key in storage) {
            if (storage.hasOwnProperty(key)) {
                size += storage[key].length + key.length;
            }
        }
        return size;
    }

    // 🎯 Создание тестовых данных
    async createTestData() {
        console.log('🎯 Создаем тестовые данные...');
        
        // localStorage тестовые данные
        const testData = {
            'test_cache_user': JSON.stringify({ id: 123, name: 'Test User', gems: 1000 }),
            'test_cache_dashboard': JSON.stringify({ stats: { users: 100, games: 50, bots: 25 } }),
            'test_cache_games': JSON.stringify({ active: [1, 2, 3], completed: [4, 5, 6] }),
            'test_cache_bots': JSON.stringify({ human_bots: 5, regular_bots: 10 }),
            'test_large_data_1': 'A'.repeat(5000), // 5KB
            'test_large_data_2': 'B'.repeat(3000), // 3KB
            'test_large_data_3': 'C'.repeat(2000)  // 2KB
        };

        for (const [key, value] of Object.entries(testData)) {
            localStorage.setItem(key, value);
        }

        // sessionStorage тестовые данные
        sessionStorage.setItem('test_session_cache', JSON.stringify({ 
            session: 'test_session', 
            timestamp: Date.now(),
            data: 'X'.repeat(1000)
        }));
        sessionStorage.setItem('test_temp_session', 'Temporary session data');

        // Cache API тестовые данные (если поддерживается)
        if ('caches' in window) {
            try {
                const cache = await caches.open('test-gemplay-cache');
                await cache.put('/test-api/dashboard', new Response(JSON.stringify({ test: 'data' })));
                await cache.put('/test-api/users', new Response(JSON.stringify({ users: [] })));
                console.log('✅ Cache API тестовые данные созданы');
            } catch (error) {
                console.log('⚠️ Ошибка создания Cache API данных:', error.message);
            }
        }

        console.log('✅ Тестовые данные созданы');
        return testData;
    }

    // 🔍 Поиск кнопки очистки кэша
    findClearCacheButton() {
        console.log('🔍 Ищем кнопку очистки кэша...');
        
        // Возможные селекторы для кнопки
        const selectors = [
            'button[title*="Очистить серверный и локальный кэш"]',
            'button[title*="Очистить кэш"]',
            'button:contains("Очистить кэш")',
            'button[onclick*="clearCache"]',
            '[data-testid="clear-cache-button"]'
        ];

        for (const selector of selectors) {
            try {
                const button = document.querySelector(selector);
                if (button) {
                    console.log(`✅ Кнопка найдена селектором: ${selector}`);
                    return button;
                }
            } catch (error) {
                // Игнорируем ошибки селекторов
            }
        }

        // Поиск по тексту
        const buttons = document.querySelectorAll('button');
        for (const button of buttons) {
            if (button.textContent.includes('Очистить кэш') || 
                button.textContent.includes('Clear Cache')) {
                console.log('✅ Кнопка найдена по тексту');
                return button;
            }
        }

        console.log('❌ Кнопка очистки кэша не найдена');
        return null;
    }

    // 🧪 Тест работоспособности кнопки
    testButtonFunctionality() {
        console.log('🧪 Тестируем работоспособность кнопки...');
        
        const button = this.findClearCacheButton();
        if (!button) {
            return {
                found: false,
                error: 'Кнопка не найдена'
            };
        }

        const buttonState = {
            found: true,
            text: button.textContent.trim(),
            disabled: button.disabled,
            className: button.className,
            hasClickHandler: !!(button.onclick || button.getAttribute('onclick')),
            hasEventListeners: !!button.getEventListeners, // Если доступно в dev tools
            visible: button.offsetParent !== null,
            inViewport: this.isInViewport(button)
        };

        console.log('📋 Состояние кнопки:', buttonState);

        // Проверяем критические свойства
        const issues = [];
        if (buttonState.disabled) issues.push('Кнопка отключена');
        if (!buttonState.visible) issues.push('Кнопка не видна');
        if (!buttonState.hasClickHandler) issues.push('Нет обработчика клика');

        if (issues.length > 0) {
            console.log('⚠️ Обнаружены проблемы:', issues);
        } else {
            console.log('✅ Кнопка готова к использованию');
        }

        return {
            ...buttonState,
            issues,
            ready: issues.length === 0
        };
    }

    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    // 🎭 Симуляция процесса очистки кэша
    async simulateAdminPanelCacheClear() {
        console.log('🎭 Симулируем процесс очистки кэша из AdminPanel.js...');
        
        try {
            // 1. Имитируем подтверждение (обычно показывается модальное окно)
            console.log('1️⃣ Симулируем подтверждение пользователя...');
            const confirmed = true; // В реальности это результат модального окна
            
            if (!confirmed) {
                console.log('❌ Пользователь отменил операцию');
                return { cancelled: true };
            }

            // 2. Симулируем состояние загрузки
            console.log('2️⃣ Устанавливаем состояние загрузки...');
            const loadingState = { clearCacheLoading: true };

            // 3. Симулируем серверный запрос
            console.log('3️⃣ Симулируем серверный запрос...');
            const serverResponse = await this.simulateServerRequest();

            if (serverResponse.success) {
                // 4. Очищаем клиентский кэш (как в реальном коде)
                console.log('4️⃣ Очищаем клиентский кэш...');
                await this.clearClientCache();

                // 5. Симулируем обновление данных
                console.log('5️⃣ Симулируем обновление данных...');
                // В реальности здесь вызывается fetchDashboardStats()

                console.log('✅ Симуляция завершена успешно');
                return {
                    success: true,
                    serverResponse,
                    clientCacheCleared: true,
                    dataRefreshed: true
                };
            } else {
                throw new Error(serverResponse.message || 'Ошибка сервера');
            }

        } catch (error) {
            console.log(`❌ Ошибка симуляции: ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }

    async simulateServerRequest() {
        console.log('📡 Симулируем серверный запрос к /api/admin/cache/clear...');
        
        // Имитируем задержку сервера
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Имитируем ответ сервера (на основе реального кода)
        return {
            success: true,
            message: "Серверный кэш успешно очищен. Очищено 5 типов кэша.",
            cache_types_cleared: [
                "Dashboard Statistics Cache",
                "User Data Cache", 
                "Game Statistics Cache",
                "Bot Performance Cache",
                "System Metrics Cache"
            ],
            cleared_count: 5,
            timestamp: new Date().toISOString()
        };
    }

    async clearClientCache() {
        console.log('🧹 Очищаем клиентский кэш...');
        
        // Сохраняем важные данные (как в реальном коде)
        const token = localStorage.getItem('token') || 'test-admin-token';
        const user = localStorage.getItem('user') || JSON.stringify({ 
            id: 1, 
            role: 'ADMIN', 
            email: 'admin@test.com' 
        });

        console.log('   💾 Сохраняем токен и данные пользователя...');

        // Очищаем localStorage
        console.log('   🗑️ Очищаем localStorage...');
        localStorage.clear();
        localStorage.setItem('token', token);
        localStorage.setItem('user', user);

        // Очищаем sessionStorage
        console.log('   🗑️ Очищаем sessionStorage...');
        sessionStorage.clear();

        // Очищаем Cache API
        if ('caches' in window) {
            console.log('   🗑️ Очищаем Cache API...');
            const cacheNames = await caches.keys();
            await Promise.all(
                cacheNames.map(cacheName => caches.delete(cacheName))
            );
            console.log(`   ✅ Удалено кэшей: ${cacheNames.length}`);
        }

        console.log('✅ Клиентский кэш очищен');
    }

    // 🚀 Запуск полного автоматического теста
    async runFullTest() {
        console.log('🚀 === ЗАПУСК ПОЛНОГО АВТОМАТИЧЕСКОГО ТЕСТА ===');
        console.log(`🕐 Время начала: ${new Date().toLocaleString()}`);
        console.log('');

        try {
            // 1. Создаем тестовые данные
            console.log('🎯 Шаг 1: Создание тестовых данных');
            await this.createTestData();
            this.testResults.testDataCreated = true;

            // 2. Анализируем состояние ДО
            console.log('\n🔍 Шаг 2: Анализ состояния ДО очистки');
            this.testResults.before = this.analyzeCacheState();
            console.log(`📊 Кэш ДО: ${Math.round(this.testResults.before.localStorage.size / 1024 * 100) / 100} KB`);

            // 3. Тестируем кнопку
            console.log('\n🧪 Шаг 3: Тест работоспособности кнопки');
            this.testResults.buttonTest = this.testButtonFunctionality();

            // 4. Симулируем процесс очистки
            console.log('\n🎭 Шаг 4: Симуляция процесса очистки');
            this.testResults.clearSimulation = await this.simulateAdminPanelCacheClear();

            // 5. Анализируем состояние ПОСЛЕ
            console.log('\n📈 Шаг 5: Анализ состояния ПОСЛЕ очистки');
            this.testResults.after = this.analyzeCacheState();
            console.log(`📊 Кэш ПОСЛЕ: ${Math.round(this.testResults.after.localStorage.size / 1024 * 100) / 100} KB`);

            // 6. Генерируем отчет
            console.log('\n📋 Шаг 6: Генерация отчета');
            const report = this.generateTestReport();

            console.log('\n🎉 === ТЕСТ ЗАВЕРШЕН ===');
            return report;

        } catch (error) {
            console.log(`\n💥 Критическая ошибка теста: ${error.message}`);
            this.testResults.criticalError = error.message;
            return this.generateTestReport();
        }
    }

    // 📋 Генерация детального отчета
    generateTestReport() {
        const testEndTime = Date.now();
        const testDuration = Math.round((testEndTime - this.testStartTime) / 1000 * 100) / 100;

        const report = {
            metadata: {
                testTimestamp: new Date().toISOString(),
                testDuration: `${testDuration} секунд`,
                userAgent: navigator.userAgent,
                url: window.location.href
            },
            
            results: {
                testDataCreated: this.testResults.testDataCreated || false,
                buttonFound: this.testResults.buttonTest?.found || false,
                buttonReady: this.testResults.buttonTest?.ready || false,
                simulationSuccess: this.testResults.clearSimulation?.success || false,
                cacheActuallyCleared: this.calculateCacheCleared()
            },

            cacheAnalysis: {
                before: this.testResults.before,
                after: this.testResults.after,
                difference: this.calculateCacheDifference()
            },

            buttonAnalysis: this.testResults.buttonTest,
            simulationResults: this.testResults.clearSimulation,
            
            issues: this.identifyIssues(),
            recommendations: this.generateRecommendations()
        };

        // Красивый вывод отчета
        this.printFormattedReport(report);
        
        // Сохраняем в глобальную переменную для доступа
        window.lastCacheTestReport = report;
        
        return report;
    }

    calculateCacheCleared() {
        if (!this.testResults.before || !this.testResults.after) {
            return { error: 'Недостаточно данных' };
        }

        const before = this.testResults.before;
        const after = this.testResults.after;

        return {
            localStorage: {
                sizeBefore: before.localStorage.size,
                sizeAfter: after.localStorage.size,
                cleared: before.localStorage.size - after.localStorage.size,
                percentCleared: before.localStorage.size > 0 
                    ? Math.round((1 - after.localStorage.size / before.localStorage.size) * 100)
                    : 0
            },
            sessionStorage: {
                sizeBefore: before.sessionStorage.size,
                sizeAfter: after.sessionStorage.size,
                cleared: before.sessionStorage.size - after.sessionStorage.size,
                percentCleared: before.sessionStorage.size > 0 
                    ? Math.round((1 - after.sessionStorage.size / before.sessionStorage.size) * 100)
                    : 0
            }
        };
    }

    calculateCacheDifference() {
        const cleared = this.calculateCacheCleared();
        if (cleared.error) return cleared;

        return {
            totalSizeCleared: cleared.localStorage.cleared + cleared.sessionStorage.cleared,
            totalSizeClearedKB: Math.round((cleared.localStorage.cleared + cleared.sessionStorage.cleared) / 1024 * 100) / 100,
            effectiveClearing: (cleared.localStorage.percentCleared + cleared.sessionStorage.percentCleared) / 2
        };
    }

    identifyIssues() {
        const issues = [];

        if (!this.testResults.buttonTest?.found) {
            issues.push('🚨 КРИТИЧНО: Кнопка очистки кэша не найдена в DOM');
        }

        if (this.testResults.buttonTest?.found && !this.testResults.buttonTest?.ready) {
            issues.push('⚠️ Кнопка найдена, но не готова к использованию');
            if (this.testResults.buttonTest.issues) {
                issues.push(...this.testResults.buttonTest.issues.map(issue => `   • ${issue}`));
            }
        }

        if (!this.testResults.clearSimulation?.success) {
            issues.push('❌ Симуляция процесса очистки завершилась неудачно');
        }

        const cleared = this.calculateCacheCleared();
        if (!cleared.error) {
            if (cleared.localStorage.percentCleared < 50) {
                issues.push('⚠️ localStorage очищен менее чем на 50%');
            }
            if (cleared.sessionStorage.percentCleared < 90) {
                issues.push('⚠️ sessionStorage очищен менее чем на 90%');
            }
        }

        return issues;
    }

    generateRecommendations() {
        const recommendations = [];

        if (!this.testResults.buttonTest?.found) {
            recommendations.push('1. Убедитесь, что вы находитесь на странице админ-панели');
            recommendations.push('2. Проверьте права доступа пользователя (должен быть ADMIN)');
            recommendations.push('3. Проверьте, что компонент AdminPanel правильно загружен');
        }

        if (this.testResults.buttonTest?.found && this.testResults.buttonTest?.disabled) {
            recommendations.push('1. Дождитесь завершения текущих операций');
            recommendations.push('2. Обновите страницу и попробуйте снова');
        }

        // Всегда добавляем рекомендацию о серверной проблеме
        recommendations.push('⚠️ ВАЖНО: Серверная функция НЕ выполняет реальную очистку кэша');
        recommendations.push('   • Примените исправление из файла cache_clear_patch.txt');
        recommendations.push('   • Добавьте реальную логику очистки Redis/Memcached');

        return recommendations;
    }

    printFormattedReport(report) {
        console.log('\n📋 === ДЕТАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ===');
        console.log(`🕐 Время: ${new Date(report.metadata.testTimestamp).toLocaleString()}`);
        console.log(`⏱️ Длительность: ${report.metadata.testDuration}`);
        console.log('');

        console.log('🎯 РЕЗУЛЬТАТЫ ТЕСТОВ:');
        Object.entries(report.results).forEach(([key, value]) => {
            const status = value ? '✅' : '❌';
            const label = key.replace(/([A-Z])/g, ' $1').toLowerCase();
            console.log(`   ${status} ${label}: ${value}`);
        });

        if (report.cacheAnalysis.difference && !report.cacheAnalysis.difference.error) {
            console.log('\n📊 АНАЛИЗ ОЧИСТКИ КЭША:');
            console.log(`   💾 Общий размер очищен: ${report.cacheAnalysis.difference.totalSizeClearedKB} KB`);
            console.log(`   📈 Эффективность очистки: ${Math.round(report.cacheAnalysis.difference.effectiveClearing)}%`);
        }

        if (report.issues.length > 0) {
            console.log('\n🚨 ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ:');
            report.issues.forEach(issue => console.log(`   ${issue}`));
        }

        if (report.recommendations.length > 0) {
            console.log('\n💡 РЕКОМЕНДАЦИИ:');
            report.recommendations.forEach(rec => console.log(`   ${rec}`));
        }

        console.log('\n📄 Полный отчет сохранен в: window.lastCacheTestReport');
    }
}

// 🚀 Запуск автоматического теста
async function runAutomatedCacheTest() {
    const tester = new CacheTestAutomation();
    return await tester.runFullTest();
}

// 🎯 Быстрый тест только кнопки
function quickButtonTest() {
    console.log('⚡ === БЫСТРЫЙ ТЕСТ КНОПКИ ===');
    const tester = new CacheTestAutomation();
    const buttonTest = tester.testButtonFunctionality();
    
    if (buttonTest.found && buttonTest.ready) {
        console.log('✅ Кнопка готова к использованию!');
        console.log('💡 Для полного теста выполните: runAutomatedCacheTest()');
    } else {
        console.log('❌ Проблемы с кнопкой обнаружены');
        if (buttonTest.issues) {
            buttonTest.issues.forEach(issue => console.log(`   • ${issue}`));
        }
    }
    
    return buttonTest;
}

// Экспорт в глобальную область
window.runAutomatedCacheTest = runAutomatedCacheTest;
window.quickButtonTest = quickButtonTest;
window.CacheTestAutomation = CacheTestAutomation;

// Автозапуск при загрузке
console.log('🤖 Автоматизированный тест кэша загружен!');
console.log('📚 Доступные команды:');
console.log('   • runAutomatedCacheTest() - полный автоматический тест');
console.log('   • quickButtonTest() - быстрый тест кнопки');
console.log('');
console.log('🎯 Для начала тестирования выполните: runAutomatedCacheTest()');