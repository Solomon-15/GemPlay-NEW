#!/usr/bin/env python3
"""
Тест API эндпоинтов для проверки интеграции с фронтендом
"""

import json
import requests
import time

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        
    def test_server_connection(self):
        """Проверяет подключение к серверу"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def authenticate_admin(self):
        """Аутентификация как администратор"""
        # Здесь должна быть логика аутентификации
        # Для тестирования используем mock token
        self.auth_token = "mock_admin_token"
        self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        return True
    
    def test_bot_cycle_endpoints(self):
        """Тестирует эндпоинты связанные с циклами ботов"""
        print("🔌 ТЕСТ API ЭНДПОИНТОВ")
        print("=" * 50)
        
        # Проверяем подключение к серверу
        print("📡 Проверка подключения к серверу...")
        if not self.test_server_connection():
            print("❌ Сервер недоступен. Запустите backend сервер.")
            print("   Команда: cd /workspace/backend && python server.py")
            return False
        
        print("✅ Сервер доступен")
        
        # Аутентификация
        if not self.authenticate_admin():
            print("❌ Ошибка аутентификации")
            return False
        
        print("✅ Аутентификация успешна")
        
        # Тестируем основные эндпоинты
        endpoints_to_test = [
            {
                "name": "Список ботов",
                "url": "/admin/bots/regular/list",
                "method": "GET"
            },
            {
                "name": "История циклов ботов",
                "url": "/admin/profit/bot-cycles-history",
                "method": "GET"
            },
            {
                "name": "Сводка доходов от ботов",
                "url": "/admin/profit/bot-revenue-summary",
                "method": "GET"
            }
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            print(f"\n🔍 Тестируем: {endpoint['name']}")
            try:
                url = f"{self.base_url}{endpoint['url']}"
                response = self.session.get(url, timeout=10)
                
                print(f"   URL: {url}")
                print(f"   Статус: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Успешно получены данные")
                    
                    # Анализируем структуру ответа
                    if endpoint['url'] == '/admin/profit/bot-cycles-history':
                        cycles = data.get('cycles', [])
                        print(f"   📊 Найдено циклов: {len(cycles)}")
                        
                        if cycles:
                            sample_cycle = cycles[0]
                            print(f"   📋 Пример цикла:")
                            print(f"      ID: {sample_cycle.get('id', 'N/A')}")
                            print(f"      Игр: {sample_cycle.get('total_games', 'N/A')}")
                            print(f"      W/L/D: {sample_cycle.get('wins', 'N/A')}/{sample_cycle.get('losses', 'N/A')}/{sample_cycle.get('draws', 'N/A')}")
                            print(f"      Прибыль: {sample_cycle.get('net_profit', 'N/A')}")
                            print(f"      ROI: {sample_cycle.get('roi_percent', 'N/A')}%")
                    
                    elif endpoint['url'] == '/admin/profit/bot-revenue-summary':
                        revenue = data.get('revenue', {})
                        cycles = data.get('cycles', {})
                        print(f"   💰 Общий доход: {revenue.get('total', 'N/A')}")
                        print(f"   🔄 Всего циклов: {cycles.get('total', 'N/A')}")
                        print(f"   📈 Прибыльных: {cycles.get('profitable', 'N/A')}")
                    
                    results[endpoint['name']] = {"status": "SUCCESS", "data": data}
                    
                else:
                    print(f"   ❌ Ошибка: HTTP {response.status_code}")
                    print(f"   Ответ: {response.text[:200]}...")
                    results[endpoint['name']] = {"status": "FAILED", "error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                print(f"   ❌ Исключение: {e}")
                results[endpoint['name']] = {"status": "ERROR", "error": str(e)}
        
        return results

def test_manual_data_verification():
    """Ручная проверка данных без API"""
    print("\n🔍 РУЧНАЯ ПРОВЕРКА ДАННЫХ")
    print("=" * 50)
    
    print("📋 Проверка файлов конфигурации:")
    
    # Проверяем существование файлов
    files_to_check = [
        "/workspace/backend/server.py",
        "/workspace/frontend/src/components/RegularBotsManagement.js",
        "/workspace/frontend/src/components/ProfitAdmin.js"
    ]
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"✅ {file_path.split('/')[-1]}: {len(content)} символов")
            
            # Проверяем ключевые функции/компоненты
            if "server.py" in file_path:
                key_functions = [
                    "complete_bot_cycle",
                    "generate_cycle_bets_natural_distribution",
                    "get_bot_completed_cycles",
                    "get_bot_revenue_summary"
                ]
                
                for func in key_functions:
                    if func in content:
                        print(f"   ✅ Функция {func} найдена")
                    else:
                        print(f"   ❌ Функция {func} НЕ найдена")
            
            elif "RegularBotsManagement.js" in file_path:
                key_elements = [
                    "История циклов",
                    "roi_active",
                    "exact_cycle_total"
                ]
                
                for element in key_elements:
                    if element in content:
                        print(f"   ✅ Элемент '{element}' найден")
                    else:
                        print(f"   ❌ Элемент '{element}' НЕ найден")
            
        except Exception as e:
            print(f"❌ {file_path}: Ошибка чтения - {e}")

def main():
    """Главная функция"""
    print("🧪 ТЕСТИРОВАНИЕ API И ИНТЕГРАЦИИ")
    print("=" * 60)
    
    # API тестирование
    api_tester = APITester()
    api_results = api_tester.test_bot_cycle_endpoints()
    
    # Ручная проверка
    test_manual_data_verification()
    
    # Итоговый отчёт
    print(f"\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЁТ API ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    if api_results:
        total_tests = len(api_results)
        successful = sum(1 for result in api_results.values() if result["status"] == "SUCCESS")
        
        print(f"📈 Статистика API:")
        print(f"   Всего эндпоинтов: {total_tests}")
        print(f"   Успешно: {successful}")
        print(f"   Провалено: {total_tests - successful}")
        
        for name, result in api_results.items():
            status_icon = {"SUCCESS": "✅", "FAILED": "❌", "ERROR": "🔥"}[result["status"]]
            print(f"   {name}: {status_icon}")
    else:
        print("⚠️  API тестирование не выполнено (сервер недоступен)")
    
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    print(f"   1. Запустите backend сервер: cd /workspace/backend && python server.py")
    print(f"   2. Запустите frontend: cd /workspace/frontend && npm start")
    print(f"   3. Создайте тестового бота через интерфейс")
    print(f"   4. Проверьте отображение данных в 'Доход от ботов'")

if __name__ == "__main__":
    main()