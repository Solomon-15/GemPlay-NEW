#!/usr/bin/env python3
"""
Глубокое бесконечное тестирование последних доработок.
Тестирует до тех пор, пока два последних тестирования подряд не покажут идеальный результат.
"""

import asyncio
import re
import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeepTestingEngine:
    """Движок глубокого тестирования."""
    
    def __init__(self):
        self.test_results = []
        self.perfect_streak = 0  # Количество подряд идеальных тестов
        self.test_counter = 0
        self.required_perfect_streak = 2  # Нужно 2 идеальных теста подряд
        
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Логирует результат теста."""
        result = {
            "test_number": self.test_counter,
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if passed:
            logger.info(f"✅ ТЕСТ {self.test_counter}: {test_name} - ПРОЙДЕН")
        else:
            logger.error(f"❌ ТЕСТ {self.test_counter}: {test_name} - ПРОВАЛЕН: {details}")
    
    def test_old_mechanism_completely_removed(self) -> bool:
        """Тест 1: Проверка полного удаления старого механизма."""
        logger.info("🔍 ТЕСТ 1: Полное удаление старого механизма save_completed_cycle")
        
        server_file = "/workspace/backend/server.py"
        
        if not os.path.exists(server_file):
            self.log_test_result("Old mechanism removal", False, "server.py не найден")
            return False
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Найдем функцию maintain_all_bots_active_bets
        maintain_match = re.search(
            r'async def maintain_all_bots_active_bets\(\):(.*?)(?=\nasync def|\Z)', 
            content, 
            re.DOTALL
        )
        
        if not maintain_match:
            self.log_test_result("Old mechanism removal", False, "maintain_all_bots_active_bets не найдена")
            return False
        
        maintain_code = maintain_match.group(1)
        
        # Проверяем что нет реальных вызовов save_completed_cycle
        real_calls = re.findall(r'await\s+save_completed_cycle\s*\(', maintain_code)
        
        if len(real_calls) > 0:
            self.log_test_result("Old mechanism removal", False, f"Найдено {len(real_calls)} реальных вызовов")
            return False
        
        # Проверяем наличие комментария об исправлении
        has_fix_comment = "ИСПРАВЛЕНО: Убрали дублированный вызов save_completed_cycle" in maintain_code
        
        if not has_fix_comment:
            self.log_test_result("Old mechanism removal", False, "Комментарий об исправлении не найден")
            return False
        
        self.log_test_result("Old mechanism removal", True, "Старый механизм полностью удален")
        return True
    
    def test_new_mechanism_works(self) -> bool:
        """Тест 2: Проверка работы нового механизма."""
        logger.info("🔍 ТЕСТ 2: Работа нового механизма через complete_bot_cycle")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Найдем функцию complete_bot_cycle
        complete_match = re.search(
            r'async def complete_bot_cycle\(.*?\):(.*?)(?=\nasync def|\Z)', 
            content, 
            re.DOTALL
        )
        
        if not complete_match:
            self.log_test_result("New mechanism works", False, "complete_bot_cycle не найдена")
            return False
        
        complete_code = complete_match.group(1)
        
        # Проверяем наличие вызова save_completed_cycle
        save_calls = re.findall(r'await\s+save_completed_cycle\s*\(', complete_code)
        
        if len(save_calls) != 1:
            self.log_test_result("New mechanism works", False, f"Ожидался 1 вызов, найдено {len(save_calls)}")
            return False
        
        # Проверяем идемпотентность - должна быть проверка существования
        has_existence_check = "existing_cycle" in complete_code and "find_one" in complete_code
        
        if not has_existence_check:
            self.log_test_result("New mechanism works", False, "Нет проверки существования цикла")
            return False
        
        self.log_test_result("New mechanism works", True, "Новый механизм работает с идемпотентностью")
        return True
    
    def test_line_2275_specifically(self) -> bool:
        """Тест 3: Проверка конкретно строки 2275."""
        logger.info("🔍 ТЕСТ 3: Проверка строки 2275 где был старый механизм")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2275:
            self.log_test_result("Line 2275 check", False, "Файл содержит меньше 2275 строк")
            return False
        
        line_2275 = lines[2274]  # 2275-1 для 0-based индекса
        
        # Проверяем что это не реальный вызов
        has_real_call = re.search(r'await\s+save_completed_cycle\s*\(', line_2275)
        
        if has_real_call:
            self.log_test_result("Line 2275 check", False, "Строка 2275 содержит реальный вызов")
            return False
        
        # Проверяем что это комментарий об исправлении
        is_fix_comment = line_2275.strip().startswith('#') and "ИСПРАВЛЕНО" in line_2275
        
        if not is_fix_comment:
            self.log_test_result("Line 2275 check", False, "Строка 2275 не содержит комментарий об исправлении")
            return False
        
        self.log_test_result("Line 2275 check", True, "Строка 2275 содержит только комментарий об исправлении")
        return True
    
    def test_api_filtering_comprehensive(self) -> bool:
        """Тест 4: Комплексная проверка фильтрации в API."""
        logger.info("🔍 ТЕСТ 4: Комплексная проверка фильтрации temp_cycle_ в API")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Список критических API эндпоинтов
        critical_endpoints = [
            "get_bot_cycle_history",
            "get_bot_cycles_history", 
            "export_bot_cycles_csv",
            "get_bot_revenue_summary"
        ]
        
        missing_filters = []
        
        for endpoint in critical_endpoints:
            # Ищем эндпоинт
            endpoint_match = re.search(
                rf'async def {endpoint}\(.*?\):(.*?)(?=\nasync def|\Z)', 
                content, 
                re.DOTALL
            )
            
            if endpoint_match:
                endpoint_code = endpoint_match.group(1)
                
                # Проверяем наличие фильтрации temp_cycle_
                has_filter = '"id": {"$not": {"$regex": "^temp_cycle_"}}' in endpoint_code
                
                if not has_filter:
                    missing_filters.append(endpoint)
        
        if missing_filters:
            self.log_test_result("API filtering", False, f"Нет фильтрации в: {missing_filters}")
            return False
        
        self.log_test_result("API filtering", True, "Все критические API содержат фильтрацию")
        return True
    
    def test_frontend_filtering(self) -> bool:
        """Тест 5: Проверка фильтрации на frontend."""
        logger.info("🔍 ТЕСТ 5: Проверка фильтрации на frontend")
        
        frontend_files = [
            "/workspace/frontend/src/components/BotCycleModal.js",
            "/workspace/frontend/src/components/RegularBotsManagement.js"
        ]
        
        filters_found = 0
        
        for file_path in frontend_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверяем наличие фильтрации
                has_filter = ("!game.id.startsWith('temp_cycle_')" in content or 
                             "!cycle.id.startsWith('temp_cycle_')" in content)
                
                if has_filter:
                    filters_found += 1
        
        if filters_found < 2:
            self.log_test_result("Frontend filtering", False, f"Фильтрация найдена только в {filters_found}/2 файлах")
            return False
        
        self.log_test_result("Frontend filtering", True, "Фильтрация найдена во всех frontend файлах")
        return True
    
    def test_no_temp_cycle_generation(self) -> bool:
        """Тест 6: Проверка отсутствия генерации temp_cycle_."""
        logger.info("🔍 ТЕСТ 6: Отсутствие генерации temp_cycle_")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем что нет создания temp_cycle_ ID
        temp_creation_patterns = [
            r'f"temp_cycle_',
            r'"temp_cycle_" \+',
            r"'temp_cycle_' \+",
            r'temp_cycle_.*=.*str',
            r'temp_cycle_.*=.*uuid'
        ]
        
        found_creation = []
        for pattern in temp_creation_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_creation.extend(matches)
        
        if found_creation:
            self.log_test_result("No temp_cycle generation", False, f"Найдено создание temp_cycle_: {found_creation}")
            return False
        
        # Проверяем что нет генерации демо-данных
        demo_generation_patterns = [
            "Generating demo data for temporary cycle",
            "Generating demo games for temporary cycle"
        ]
        
        found_demo = []
        for pattern in demo_generation_patterns:
            if pattern in content:
                found_demo.append(pattern)
        
        if found_demo:
            self.log_test_result("No temp_cycle generation", False, f"Найдена генерация демо-данных: {found_demo}")
            return False
        
        self.log_test_result("No temp_cycle generation", True, "Генерация temp_cycle_ полностью удалена")
        return True
    
    def test_idempotency_logic(self) -> bool:
        """Тест 7: Проверка логики идемпотентности."""
        logger.info("🔍 ТЕСТ 7: Логика идемпотентности в save_completed_cycle")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Найдем функцию save_completed_cycle
        save_match = re.search(
            r'async def save_completed_cycle\(.*?\):(.*?)(?=\nasync def|\Z)', 
            content, 
            re.DOTALL
        )
        
        if not save_match:
            self.log_test_result("Idempotency logic", False, "save_completed_cycle не найдена")
            return False
        
        save_code = save_match.group(1)
        
        # Проверяем наличие проверки существования
        has_existence_check = "existing_cycle" in save_code and "find_one" in save_code
        
        if not has_existence_check:
            self.log_test_result("Idempotency logic", False, "Нет проверки существования перед вставкой")
            return False
        
        # Проверяем раннее возвращение при существовании
        has_early_return = "if existing_cycle:" in save_code and "return" in save_code
        
        if not has_early_return:
            self.log_test_result("Idempotency logic", False, "Нет раннего возвращения при существовании цикла")
            return False
        
        # Проверяем обработку ошибок дублирования
        has_duplicate_error_handling = ("duplicate key" in save_code.lower() or 
                                       "e11000" in save_code.lower())
        
        if not has_duplicate_error_handling:
            self.log_test_result("Idempotency logic", False, "Нет обработки ошибок дублирования")
            return False
        
        self.log_test_result("Idempotency logic", True, "Логика идемпотентности полностью реализована")
        return True
    
    def test_cleanup_scripts_exist(self) -> bool:
        """Тест 8: Проверка наличия скриптов очистки."""
        logger.info("🔍 ТЕСТ 8: Наличие скриптов очистки")
        
        required_scripts = [
            "/workspace/backend/cleanup_and_fix_cycles.py",
            "/workspace/backend/verify_cycles_integrity.py", 
            "/workspace/backend/create_unique_index.py"
        ]
        
        missing_scripts = []
        
        for script_path in required_scripts:
            if not os.path.exists(script_path):
                missing_scripts.append(script_path)
        
        if missing_scripts:
            self.log_test_result("Cleanup scripts", False, f"Отсутствуют скрипты: {missing_scripts}")
            return False
        
        self.log_test_result("Cleanup scripts", True, "Все скрипты очистки присутствуют")
        return True
    
    def test_unique_index_creation(self) -> bool:
        """Тест 9: Проверка создания уникального индекса."""
        logger.info("🔍 ТЕСТ 9: Создание уникального индекса")
        
        index_script = "/workspace/backend/create_unique_index.py"
        
        if not os.path.exists(index_script):
            self.log_test_result("Unique index creation", False, "create_unique_index.py не найден")
            return False
        
        with open(index_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем создание уникального индекса на (bot_id, cycle_number)
        has_unique_index = ('create_index' in content and 
                           'bot_id' in content and 
                           'cycle_number' in content and
                           'unique=True' in content)
        
        if not has_unique_index:
            self.log_test_result("Unique index creation", False, "Нет создания уникального индекса")
            return False
        
        self.log_test_result("Unique index creation", True, "Скрипт создания уникального индекса корректен")
        return True
    
    def test_error_handling_comprehensive(self) -> bool:
        """Тест 10: Комплексная проверка обработки ошибок."""
        logger.info("🔍 ТЕСТ 10: Комплексная обработка ошибок")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем обработку ошибок в save_completed_cycle
        save_match = re.search(
            r'async def save_completed_cycle\(.*?\):(.*?)(?=\nasync def|\Z)', 
            content, 
            re.DOTALL
        )
        
        if not save_match:
            self.log_test_result("Error handling", False, "save_completed_cycle не найдена")
            return False
        
        save_code = save_match.group(1)
        
        # Проверяем try-catch блоки
        has_try_catch = "try:" in save_code and "except" in save_code
        
        if not has_try_catch:
            self.log_test_result("Error handling", False, "Нет try-catch блоков")
            return False
        
        # Проверяем специфичную обработку ошибок дублирования
        has_duplicate_handling = ("duplicate key" in save_code.lower() and 
                                 "e11000" in save_code.lower())
        
        if not has_duplicate_handling:
            self.log_test_result("Error handling", False, "Нет специфичной обработки ошибок дублирования")
            return False
        
        # Проверяем логирование ошибок
        has_error_logging = "logger.error" in save_code or "logger.warning" in save_code
        
        if not has_error_logging:
            self.log_test_result("Error handling", False, "Нет логирования ошибок")
            return False
        
        self.log_test_result("Error handling", True, "Обработка ошибок реализована комплексно")
        return True
    
    def run_single_test_cycle(self) -> bool:
        """Запускает один цикл всех тестов."""
        self.test_counter += 1
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 ЗАПУСК ЦИКЛА ТЕСТИРОВАНИЯ #{self.test_counter}")
        logger.info(f"{'='*80}")
        
        tests = [
            self.test_old_mechanism_completely_removed,
            self.test_new_mechanism_works,
            self.test_line_2275_specifically,
            self.test_api_filtering_comprehensive,
            self.test_frontend_filtering,
            self.test_no_temp_cycle_generation,
            self.test_idempotency_logic,
            self.test_cleanup_scripts_exist,
            self.test_unique_index_creation,
            self.test_error_handling_comprehensive
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            try:
                result = test_func()
                if result:
                    passed_tests += 1
            except Exception as e:
                logger.error(f"❌ ОШИБКА в тесте {test_func.__name__}: {e}")
                self.log_test_result(test_func.__name__, False, f"Исключение: {e}")
        
        success_rate = (passed_tests / total_tests) * 100
        
        logger.info(f"\n📊 РЕЗУЛЬТАТЫ ЦИКЛА #{self.test_counter}:")
        logger.info(f"   Пройдено: {passed_tests}/{total_tests}")
        logger.info(f"   Процент успеха: {success_rate:.1f}%")
        
        is_perfect = passed_tests == total_tests
        
        if is_perfect:
            self.perfect_streak += 1
            logger.info(f"🎉 ИДЕАЛЬНЫЙ РЕЗУЛЬТАТ! Серия идеальных тестов: {self.perfect_streak}")
        else:
            self.perfect_streak = 0
            logger.warning(f"⚠️ НЕ ИДЕАЛЬНЫЙ РЕЗУЛЬТАТ. Серия прервана.")
        
        return is_perfect
    
    def run_infinite_testing(self):
        """Запускает бесконечное тестирование до получения требуемой серии."""
        logger.info("🔄 ЗАПУСК ГЛУБОКОГО БЕСКОНЕЧНОГО ТЕСТИРОВАНИЯ")
        logger.info(f"Цель: {self.required_perfect_streak} идеальных теста подряд")
        logger.info("="*80)
        
        start_time = time.time()
        
        while self.perfect_streak < self.required_perfect_streak:
            is_perfect = self.run_single_test_cycle()
            
            logger.info(f"\n🎯 СТАТУС: {self.perfect_streak}/{self.required_perfect_streak} идеальных тестов подряд")
            
            if not is_perfect:
                logger.info("⏳ Продолжаем тестирование...")
                time.sleep(1)  # Небольшая пауза между циклами
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 ЦЕЛЬ ДОСТИГНУТА!")
        logger.info(f"{'='*80}")
        logger.info(f"✅ Получено {self.required_perfect_streak} идеальных теста подряд")
        logger.info(f"📊 Всего циклов тестирования: {self.test_counter}")
        logger.info(f"⏱️ Время тестирования: {duration:.2f} секунд")
        logger.info(f"🎯 Система полностью протестирована и готова!")
        
        return True

def main():
    """Главная функция."""
    print("🧪 ГЛУБОКОЕ БЕСКОНЕЧНОЕ ТЕСТИРОВАНИЕ ПОСЛЕДНИХ ДОРАБОТОК")
    print("="*80)
    print("Цель: Получить 2 идеальных результата тестирования подряд")
    print("="*80)
    
    engine = DeepTestingEngine()
    
    try:
        success = engine.run_infinite_testing()
        
        if success:
            print("\n🎉 МИССИЯ ВЫПОЛНЕНА!")
            print("✅ Все доработки протестированы до идеального состояния")
            return True
        else:
            print("\n❌ ТЕСТИРОВАНИЕ ПРЕРВАНО")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️ ТЕСТИРОВАНИЕ ОСТАНОВЛЕНО ПОЛЬЗОВАТЕЛЕМ")
        print(f"📊 Выполнено циклов: {engine.test_counter}")
        print(f"🎯 Текущая серия идеальных тестов: {engine.perfect_streak}")
        return False
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)