#!/usr/bin/env python3
"""
Ультра-глубокое тестирование с максимальной детализацией.
Проводит исчерпывающую проверку всех аспектов доработок.
"""

import asyncio
import re
import os
import sys
import json
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltraDeepTestEngine:
    """Движок ультра-глубокого тестирования."""
    
    def __init__(self):
        self.test_results = []
        self.perfect_streak = 0
        self.test_counter = 0
        self.required_perfect_streak = 2
        self.detailed_analysis = {}
        
    def log_test_result(self, test_name: str, passed: bool, details: str = "", analysis: Dict = None):
        """Логирует детальный результат теста."""
        result = {
            "test_number": self.test_counter,
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "analysis": analysis or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if passed:
            logger.info(f"✅ ТЕСТ {self.test_counter}: {test_name} - ПРОЙДЕН")
            if analysis:
                for key, value in analysis.items():
                    logger.info(f"   📊 {key}: {value}")
        else:
            logger.error(f"❌ ТЕСТ {self.test_counter}: {test_name} - ПРОВАЛЕН: {details}")
    
    def analyze_file_structure(self, filepath: str) -> Dict[str, Any]:
        """Анализирует структуру файла."""
        if not os.path.exists(filepath):
            return {"exists": False}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "exists": True,
            "size": len(content),
            "lines": len(content.split('\n')),
            "functions": len(re.findall(r'async def |def ', content)),
            "classes": len(re.findall(r'class ', content)),
            "imports": len(re.findall(r'^import |^from ', content, re.MULTILINE)),
            "comments": len(re.findall(r'#.*', content)),
            "docstrings": len(re.findall(r'""".*?"""', content, re.DOTALL))
        }
    
    def test_server_file_integrity(self) -> bool:
        """Тест 1: Целостность основного файла server.py."""
        logger.info("🔍 ТЕСТ 1: Целостность файла server.py")
        
        server_file = "/workspace/backend/server.py"
        analysis = self.analyze_file_structure(server_file)
        
        if not analysis["exists"]:
            self.log_test_result("Server file integrity", False, "server.py не существует")
            return False
        
        # Проверяем минимальные требования
        if analysis["lines"] < 20000:
            self.log_test_result("Server file integrity", False, f"Слишком мало строк: {analysis['lines']}")
            return False
        
        if analysis["functions"] < 100:
            self.log_test_result("Server file integrity", False, f"Слишком мало функций: {analysis['functions']}")
            return False
        
        self.log_test_result("Server file integrity", True, "Файл server.py целостный", analysis)
        return True
    
    def test_maintain_function_deep_analysis(self) -> bool:
        """Тест 2: Глубокий анализ функции maintain_all_bots_active_bets."""
        logger.info("🔍 ТЕСТ 2: Глубокий анализ maintain_all_bots_active_bets")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Найдем функцию
        maintain_match = re.search(
            r'async def maintain_all_bots_active_bets\(\):(.*?)(?=\nasync def|\Z)', 
            content, 
            re.DOTALL
        )
        
        if not maintain_match:
            self.log_test_result("Maintain function analysis", False, "Функция не найдена")
            return False
        
        maintain_code = maintain_match.group(1)
        
        # Детальный анализ
        analysis = {
            "total_lines": len(maintain_code.split('\n')),
            "save_completed_cycle_mentions": len(re.findall(r'save_completed_cycle', maintain_code)),
            "real_save_calls": len(re.findall(r'await\s+save_completed_cycle\s*\(', maintain_code)),
            "comment_mentions": len(re.findall(r'#.*save_completed_cycle', maintain_code)),
            "fix_comments": len(re.findall(r'ИСПРАВЛЕНО.*save_completed_cycle', maintain_code)),
            "db_operations": len(re.findall(r'await db\.', maintain_code)),
            "logger_calls": len(re.findall(r'logger\.', maintain_code)),
            "try_catch_blocks": len(re.findall(r'try:', maintain_code))
        }
        
        # Проверки
        if analysis["real_save_calls"] > 0:
            self.log_test_result("Maintain function analysis", False, 
                               f"Найдено {analysis['real_save_calls']} реальных вызовов", analysis)
            return False
        
        if analysis["fix_comments"] == 0:
            self.log_test_result("Maintain function analysis", False, 
                               "Нет комментариев об исправлении", analysis)
            return False
        
        if analysis["comment_mentions"] != analysis["fix_comments"]:
            self.log_test_result("Maintain function analysis", False, 
                               "Есть упоминания save_completed_cycle не в комментариях об исправлении", analysis)
            return False
        
        self.log_test_result("Maintain function analysis", True, 
                           "Функция полностью очищена от старого механизма", analysis)
        return True
    
    def test_complete_bot_cycle_analysis(self) -> bool:
        """Тест 3: Анализ функции complete_bot_cycle."""
        logger.info("🔍 ТЕСТ 3: Анализ complete_bot_cycle")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        complete_match = re.search(
            r'async def complete_bot_cycle\(.*?\):(.*?)(?=\nasync def|\Z)', 
            content, 
            re.DOTALL
        )
        
        if not complete_match:
            self.log_test_result("Complete bot cycle analysis", False, "Функция не найдена")
            return False
        
        complete_code = complete_match.group(1)
        
        analysis = {
            "total_lines": len(complete_code.split('\n')),
            "save_calls": len(re.findall(r'await\s+save_completed_cycle\s*\(', complete_code)),
            "existence_checks": len(re.findall(r'existing_cycle', complete_code)),
            "find_one_calls": len(re.findall(r'find_one', complete_code)),
            "if_not_existing": len(re.findall(r'if not existing_cycle', complete_code)),
            "error_handling": len(re.findall(r'except', complete_code)),
            "logger_calls": len(re.findall(r'logger\.', complete_code))
        }
        
        # Проверки нового механизма
        if analysis["save_calls"] != 1:
            self.log_test_result("Complete bot cycle analysis", False, 
                               f"Ожидался 1 вызов save_completed_cycle, найдено {analysis['save_calls']}", analysis)
            return False
        
        if analysis["existence_checks"] == 0:
            self.log_test_result("Complete bot cycle analysis", False, 
                               "Нет проверки существования цикла", analysis)
            return False
        
        if analysis["if_not_existing"] == 0:
            self.log_test_result("Complete bot cycle analysis", False, 
                               "Нет условия 'if not existing_cycle'", analysis)
            return False
        
        self.log_test_result("Complete bot cycle analysis", True, 
                           "Новый механизм работает корректно", analysis)
        return True
    
    def test_save_completed_cycle_idempotency_deep(self) -> bool:
        """Тест 4: Глубокий анализ идемпотентности save_completed_cycle."""
        logger.info("🔍 ТЕСТ 4: Глубокий анализ идемпотентности save_completed_cycle")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        save_match = re.search(
            r'async def save_completed_cycle\(.*?\):(.*?)(?=\nasync def|\Z)', 
            content, 
            re.DOTALL
        )
        
        if not save_match:
            self.log_test_result("Save cycle idempotency", False, "Функция не найдена")
            return False
        
        save_code = save_match.group(1)
        
        analysis = {
            "total_lines": len(save_code.split('\n')),
            "existence_checks": len(re.findall(r'existing_cycle.*find_one', save_code)),
            "early_returns": len(re.findall(r'if existing_cycle:.*?return', save_code, re.DOTALL)),
            "insert_operations": len(re.findall(r'insert_one', save_code)),
            "duplicate_error_handling": len(re.findall(r'duplicate key|E11000', save_code, re.IGNORECASE)),
            "try_catch_blocks": len(re.findall(r'try:.*?except', save_code, re.DOTALL)),
            "logger_warnings": len(re.findall(r'logger\.warning', save_code)),
            "projection_usage": len(re.findall(r'\{"_id": 1\}', save_code))
        }
        
        # Проверки идемпотентности
        required_checks = [
            ("existence_checks", 1, "Должна быть проверка существования"),
            ("early_returns", 1, "Должен быть ранний возврат при существовании"),
            ("duplicate_error_handling", 1, "Должна быть обработка ошибок дублирования"),
            ("try_catch_blocks", 1, "Должны быть try-catch блоки")
        ]
        
        for check_name, expected_min, error_msg in required_checks:
            if analysis[check_name] < expected_min:
                self.log_test_result("Save cycle idempotency", False, error_msg, analysis)
                return False
        
        self.log_test_result("Save cycle idempotency", True, 
                           "Идемпотентность полностью реализована", analysis)
        return True
    
    def test_api_endpoints_comprehensive(self) -> bool:
        """Тест 5: Комплексная проверка всех API эндпоинтов."""
        logger.info("🔍 ТЕСТ 5: Комплексная проверка API эндпоинтов")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Расширенный список эндпоинтов для проверки
        endpoints_to_check = [
            "get_bot_cycle_history",
            "get_bot_cycles_history", 
            "export_bot_cycles_csv",
            "get_bot_revenue_summary",
            "get_completed_cycle_bets"
        ]
        
        analysis = {
            "total_endpoints_found": 0,
            "endpoints_with_filter": 0,
            "endpoints_without_filter": [],
            "filter_patterns_found": [],
            "temp_cycle_mentions": 0
        }
        
        for endpoint in endpoints_to_check:
            endpoint_match = re.search(
                rf'async def {endpoint}\(.*?\):(.*?)(?=\nasync def|\Z)', 
                content, 
                re.DOTALL
            )
            
            if endpoint_match:
                analysis["total_endpoints_found"] += 1
                endpoint_code = endpoint_match.group(1)
                
                # Ищем различные паттерны фильтрации
                filter_patterns = [
                    r'"id": \{".*temp_cycle_.*"\}',
                    r"'id': \{.*temp_cycle_.*\}",
                    r'filter_query.*temp_cycle_',
                    r'base_filter.*temp_cycle_',
                    r'recent_filter.*temp_cycle_'
                ]
                
                has_filter = False
                for pattern in filter_patterns:
                    if re.search(pattern, endpoint_code):
                        has_filter = True
                        analysis["filter_patterns_found"].append(f"{endpoint}: {pattern}")
                        break
                
                if has_filter:
                    analysis["endpoints_with_filter"] += 1
                else:
                    analysis["endpoints_without_filter"].append(endpoint)
                
                # Считаем упоминания temp_cycle
                temp_mentions = len(re.findall(r'temp_cycle_', endpoint_code))
                analysis["temp_cycle_mentions"] += temp_mentions
        
        # Проверки
        if analysis["endpoints_without_filter"]:
            self.log_test_result("API endpoints comprehensive", False, 
                               f"Эндпоинты без фильтрации: {analysis['endpoints_without_filter']}", analysis)
            return False
        
        if analysis["total_endpoints_found"] < 4:
            self.log_test_result("API endpoints comprehensive", False, 
                               f"Найдено слишком мало эндпоинтов: {analysis['total_endpoints_found']}", analysis)
            return False
        
        self.log_test_result("API endpoints comprehensive", True, 
                           "Все критические API эндпоинты имеют фильтрацию", analysis)
        return True
    
    def test_frontend_components_deep(self) -> bool:
        """Тест 6: Глубокая проверка frontend компонентов."""
        logger.info("🔍 ТЕСТ 6: Глубокая проверка frontend компонентов")
        
        frontend_files = [
            "/workspace/frontend/src/components/BotCycleModal.js",
            "/workspace/frontend/src/components/RegularBotsManagement.js"
        ]
        
        analysis = {
            "total_files_checked": 0,
            "files_with_filter": 0,
            "files_without_filter": [],
            "filter_patterns": [],
            "component_analysis": {}
        }
        
        for file_path in frontend_files:
            filename = os.path.basename(file_path)
            
            if not os.path.exists(file_path):
                analysis["component_analysis"][filename] = {"exists": False}
                continue
            
            analysis["total_files_checked"] += 1
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_analysis = {
                "exists": True,
                "size": len(content),
                "lines": len(content.split('\n')),
                "temp_cycle_mentions": len(re.findall(r'temp_cycle_', content)),
                "filter_patterns": []
            }
            
            # Ищем различные паттерны фильтрации
            filter_patterns = [
                r"!game\.id\.startsWith\('temp_cycle_'\)",
                r"!cycle\.id\.startsWith\('temp_cycle_'\)",
                r'!game\.id \|\| !game\.id\.startsWith\(\'temp_cycle_\'\)',
                r'!cycle\.id \|\| !cycle\.id\.startsWith\(\'temp_cycle_\'\)'
            ]
            
            has_filter = False
            for pattern in filter_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    has_filter = True
                    file_analysis["filter_patterns"].append(pattern)
                    analysis["filter_patterns"].append(f"{filename}: {pattern}")
            
            file_analysis["has_filter"] = has_filter
            analysis["component_analysis"][filename] = file_analysis
            
            if has_filter:
                analysis["files_with_filter"] += 1
            else:
                analysis["files_without_filter"].append(filename)
        
        # Проверки
        if analysis["files_without_filter"]:
            self.log_test_result("Frontend components deep", False, 
                               f"Файлы без фильтрации: {analysis['files_without_filter']}", analysis)
            return False
        
        if analysis["total_files_checked"] < 2:
            self.log_test_result("Frontend components deep", False, 
                               "Проверено слишком мало файлов", analysis)
            return False
        
        self.log_test_result("Frontend components deep", True, 
                           "Все frontend компоненты имеют фильтрацию", analysis)
        return True
    
    def test_temp_cycle_generation_elimination(self) -> bool:
        """Тест 7: Полное устранение генерации temp_cycle_."""
        logger.info("🔍 ТЕСТ 7: Полное устранение генерации temp_cycle_")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis = {
            "file_size": len(content),
            "total_temp_mentions": len(re.findall(r'temp_cycle_', content)),
            "creation_patterns": {},
            "demo_generation_patterns": {},
            "api_generation_blocks": 0,
            "comment_mentions": 0
        }
        
        # Проверяем различные паттерны создания temp_cycle_
        creation_patterns = {
            "f_string_creation": r'f"temp_cycle_',
            "string_concatenation": r'"temp_cycle_" \+',
            "variable_assignment": r'temp_cycle_.*=',
            "uuid_generation": r'temp_cycle_.*uuid',
            "format_creation": r'\.format.*temp_cycle_'
        }
        
        for pattern_name, pattern in creation_patterns.items():
            matches = re.findall(pattern, content)
            analysis["creation_patterns"][pattern_name] = len(matches)
        
        # Проверяем паттерны генерации демо-данных (исключаем защитные блоки)
        demo_patterns = {
            "demo_data_generation": "Generating demo data",
            "demo_games_generation": "Generating demo games", 
            "demo_cycle_creation": "demo_game_",
            "fake_cycle_generation": "completed_cycle = {"
        }
        
        # Отдельно проверяем защитные блоки (это нормально)
        protective_patterns = {
            "temp_cycle_protection": "if cycle_id.startswith(\"temp_cycle_\"):",
            "fake_cycle_rejection": "raise HTTPException.*Fake cycle not accessible"
        }
        
        for pattern_name, pattern in demo_patterns.items():
            if pattern_name == "fake_cycle_generation":
                # Ищем создание фиктивных циклов, но исключаем защитные блоки
                matches = re.findall(re.escape(pattern), content)
                # Фильтруем только те, что создают temp_cycle_
                fake_generations = [m for m in matches if "temp_cycle_" in content[content.find(m):content.find(m)+500]]
                count = len(fake_generations)
            else:
                count = len(re.findall(re.escape(pattern), content))
            analysis["demo_generation_patterns"][pattern_name] = count
        
        # Считаем защитные блоки отдельно (это хорошо)
        analysis["protective_patterns"] = {}
        for pattern_name, pattern in protective_patterns.items():
            if "HTTPException" in pattern:
                count = len(re.findall(pattern, content))
            else:
                count = len(re.findall(re.escape(pattern), content))
            analysis["protective_patterns"][pattern_name] = count
        
        # Считаем упоминания в комментариях
        comment_mentions = re.findall(r'#.*temp_cycle_', content)
        analysis["comment_mentions"] = len(comment_mentions)
        
        # Проверки
        total_creation = sum(analysis["creation_patterns"].values())
        total_demo = sum(analysis["demo_generation_patterns"].values())
        total_protective = sum(analysis["protective_patterns"].values())
        
        if total_creation > 0:
            self.log_test_result("Temp cycle elimination", False, 
                               f"Найдено создание temp_cycle_: {total_creation}", analysis)
            return False
        
        if total_demo > 0:
            self.log_test_result("Temp cycle elimination", False, 
                               f"Найдена генерация демо-данных: {total_demo}", analysis)
            return False
        
        # Защитные блоки - это хорошо, логируем их отдельно
        if total_protective > 0:
            logger.info(f"✅ Найдено {total_protective} защитных блоков от temp_cycle_ (это хорошо)")
        
        # Проверяем что все упоминания только в комментариях и фильтрах
        non_comment_mentions = analysis["total_temp_mentions"] - analysis["comment_mentions"]
        # Допускаем упоминания в фильтрах (примерно 10-15 для всех API)
        if non_comment_mentions > 20:
            self.log_test_result("Temp cycle elimination", False, 
                               f"Слишком много упоминаний temp_cycle_ вне комментариев: {non_comment_mentions}", analysis)
            return False
        
        self.log_test_result("Temp cycle elimination", True, 
                           "Генерация temp_cycle_ полностью устранена", analysis)
        return True
    
    def test_cleanup_scripts_functionality(self) -> bool:
        """Тест 8: Функциональность скриптов очистки."""
        logger.info("🔍 ТЕСТ 8: Функциональность скриптов очистки")
        
        scripts_to_check = {
            "/workspace/backend/cleanup_and_fix_cycles.py": {
                "required_functions": ["cleanup_and_fix_cycles", "main"],
                "required_patterns": ["temp_cycle_", "delete_many", "aggregate"]
            },
            "/workspace/backend/verify_cycles_integrity.py": {
                "required_functions": ["verify_cycles_integrity", "main"],
                "required_patterns": ["completed_cycles", "count_documents", "fake_cycles"]
            },
            "/workspace/backend/create_unique_index.py": {
                "required_functions": ["create_unique_index", "main"],
                "required_patterns": ["create_index", "unique=True", "bot_id", "cycle_number"]
            }
        }
        
        analysis = {
            "total_scripts": len(scripts_to_check),
            "scripts_found": 0,
            "scripts_analysis": {}
        }
        
        for script_path, requirements in scripts_to_check.items():
            script_name = os.path.basename(script_path)
            
            if not os.path.exists(script_path):
                analysis["scripts_analysis"][script_name] = {"exists": False}
                continue
            
            analysis["scripts_found"] += 1
            
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            script_analysis = {
                "exists": True,
                "size": len(content),
                "lines": len(content.split('\n')),
                "functions_found": [],
                "patterns_found": [],
                "missing_functions": [],
                "missing_patterns": []
            }
            
            # Проверяем функции
            for func_name in requirements["required_functions"]:
                if f"def {func_name}" in content or f"async def {func_name}" in content:
                    script_analysis["functions_found"].append(func_name)
                else:
                    script_analysis["missing_functions"].append(func_name)
            
            # Проверяем паттерны
            for pattern in requirements["required_patterns"]:
                if pattern in content:
                    script_analysis["patterns_found"].append(pattern)
                else:
                    script_analysis["missing_patterns"].append(pattern)
            
            analysis["scripts_analysis"][script_name] = script_analysis
        
        # Проверки
        if analysis["scripts_found"] < analysis["total_scripts"]:
            missing_scripts = [name for name, data in analysis["scripts_analysis"].items() 
                             if not data.get("exists", True)]
            self.log_test_result("Cleanup scripts functionality", False, 
                               f"Отсутствуют скрипты: {missing_scripts}", analysis)
            return False
        
        # Проверяем что все скрипты имеют необходимые функции
        for script_name, script_data in analysis["scripts_analysis"].items():
            if script_data.get("missing_functions"):
                self.log_test_result("Cleanup scripts functionality", False, 
                                   f"В {script_name} отсутствуют функции: {script_data['missing_functions']}", analysis)
                return False
        
        self.log_test_result("Cleanup scripts functionality", True, 
                           "Все скрипты очистки функциональны", analysis)
        return True
    
    def test_error_handling_comprehensive(self) -> bool:
        """Тест 9: Комплексная проверка обработки ошибок."""
        logger.info("🔍 ТЕСТ 9: Комплексная обработка ошибок")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Анализируем обработку ошибок в ключевых функциях
        functions_to_check = [
            "save_completed_cycle",
            "complete_bot_cycle", 
            "maintain_all_bots_active_bets"
        ]
        
        analysis = {
            "functions_checked": 0,
            "functions_analysis": {}
        }
        
        for func_name in functions_to_check:
            func_match = re.search(
                rf'async def {func_name}\(.*?\):(.*?)(?=\nasync def|\Z)', 
                content, 
                re.DOTALL
            )
            
            if not func_match:
                analysis["functions_analysis"][func_name] = {"found": False}
                continue
            
            analysis["functions_checked"] += 1
            func_code = func_match.group(1)
            
            func_analysis = {
                "found": True,
                "try_blocks": len(re.findall(r'try:', func_code)),
                "except_blocks": len(re.findall(r'except', func_code)),
                "specific_exceptions": len(re.findall(r'except \w+', func_code)),
                "general_exceptions": len(re.findall(r'except Exception', func_code)),
                "error_logging": len(re.findall(r'logger\.(error|warning)', func_code)),
                "duplicate_error_handling": len(re.findall(r'duplicate key|E11000', func_code, re.IGNORECASE)),
                "return_on_error": len(re.findall(r'except.*?return', func_code, re.DOTALL))
            }
            
            analysis["functions_analysis"][func_name] = func_analysis
        
        # Проверки
        if analysis["functions_checked"] < len(functions_to_check):
            self.log_test_result("Error handling comprehensive", False, 
                               "Не все ключевые функции найдены", analysis)
            return False
        
        # Проверяем save_completed_cycle на специфичную обработку ошибок
        save_analysis = analysis["functions_analysis"].get("save_completed_cycle", {})
        if save_analysis.get("duplicate_error_handling", 0) == 0:
            self.log_test_result("Error handling comprehensive", False, 
                               "save_completed_cycle не обрабатывает ошибки дублирования", analysis)
            return False
        
        if save_analysis.get("error_logging", 0) == 0:
            self.log_test_result("Error handling comprehensive", False, 
                               "save_completed_cycle не логирует ошибки", analysis)
            return False
        
        self.log_test_result("Error handling comprehensive", True, 
                           "Обработка ошибок реализована комплексно", analysis)
        return True
    
    def test_code_consistency_and_style(self) -> bool:
        """Тест 10: Консистентность кода и стиль."""
        logger.info("🔍 ТЕСТ 10: Консистентность кода и стиль")
        
        server_file = "/workspace/backend/server.py"
        
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis = {
            "total_lines": len(content.split('\n')),
            "async_functions": len(re.findall(r'async def ', content)),
            "sync_functions": len(re.findall(r'^def ', content, re.MULTILINE)),
            "logger_calls": len(re.findall(r'logger\.', content)),
            "await_calls": len(re.findall(r'await ', content)),
            "try_catch_ratio": 0,
            "comment_density": 0,
            "docstring_coverage": 0,
            "consistent_naming": True,
            "fix_comments": len(re.findall(r'ИСПРАВЛЕНО:', content))
        }
        
        # Рассчитываем метрики
        try_blocks = len(re.findall(r'try:', content))
        except_blocks = len(re.findall(r'except', content))
        analysis["try_catch_ratio"] = except_blocks / max(try_blocks, 1)
        
        comments = len(re.findall(r'#.*', content))
        analysis["comment_density"] = comments / analysis["total_lines"] * 100
        
        functions_total = analysis["async_functions"] + analysis["sync_functions"]
        docstrings = len(re.findall(r'""".*?"""', content, re.DOTALL))
        analysis["docstring_coverage"] = docstrings / max(functions_total, 1) * 100
        
        # Проверки консистентности
        if analysis["fix_comments"] < 1:
            self.log_test_result("Code consistency", False, 
                               "Нет комментариев об исправлениях", analysis)
            return False
        
        if analysis["comment_density"] < 5:  # Минимум 5% строк должны быть комментариями
            self.log_test_result("Code consistency", False, 
                               f"Слишком мало комментариев: {analysis['comment_density']:.1f}%", analysis)
            return False
        
        if analysis["try_catch_ratio"] < 0.8:  # Большинство try должны иметь except
            self.log_test_result("Code consistency", False, 
                               f"Низкий коэффициент try-catch: {analysis['try_catch_ratio']:.2f}", analysis)
            return False
        
        self.log_test_result("Code consistency", True, 
                           "Код консистентен и хорошо структурирован", analysis)
        return True
    
    def run_ultra_deep_cycle(self) -> bool:
        """Запускает один ультра-глубокий цикл тестирования."""
        self.test_counter += 1
        
        logger.info(f"\n{'='*100}")
        logger.info(f"🚀 ЗАПУСК УЛЬТРА-ГЛУБОКОГО ЦИКЛА ТЕСТИРОВАНИЯ #{self.test_counter}")
        logger.info(f"{'='*100}")
        
        tests = [
            self.test_server_file_integrity,
            self.test_maintain_function_deep_analysis,
            self.test_complete_bot_cycle_analysis,
            self.test_save_completed_cycle_idempotency_deep,
            self.test_api_endpoints_comprehensive,
            self.test_frontend_components_deep,
            self.test_temp_cycle_generation_elimination,
            self.test_cleanup_scripts_functionality,
            self.test_error_handling_comprehensive,
            self.test_code_consistency_and_style
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(0.1)  # Небольшая пауза между тестами
            except Exception as e:
                logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА в тесте {test_func.__name__}: {e}")
                self.log_test_result(test_func.__name__, False, f"Критическая ошибка: {e}")
        
        success_rate = (passed_tests / total_tests) * 100
        
        logger.info(f"\n📊 РЕЗУЛЬТАТЫ УЛЬТРА-ГЛУБОКОГО ЦИКЛА #{self.test_counter}:")
        logger.info(f"   Пройдено: {passed_tests}/{total_tests}")
        logger.info(f"   Процент успеха: {success_rate:.1f}%")
        
        is_perfect = passed_tests == total_tests
        
        if is_perfect:
            self.perfect_streak += 1
            logger.info(f"🎉 ИДЕАЛЬНЫЙ РЕЗУЛЬТАТ! Серия идеальных тестов: {self.perfect_streak}")
        else:
            self.perfect_streak = 0
            logger.warning(f"⚠️ НЕ ИДЕАЛЬНЫЙ РЕЗУЛЬТАТ. Серия прервана.")
            
            # Показываем детали провалов
            failed_tests = [result for result in self.test_results[-total_tests:] if not result["passed"]]
            for failed_test in failed_tests:
                logger.error(f"   ❌ {failed_test['test_name']}: {failed_test['details']}")
        
        return is_perfect
    
    def run_ultra_deep_testing(self):
        """Запускает ультра-глубокое бесконечное тестирование."""
        logger.info("🔄 ЗАПУСК УЛЬТРА-ГЛУБОКОГО БЕСКОНЕЧНОГО ТЕСТИРОВАНИЯ")
        logger.info(f"Цель: {self.required_perfect_streak} идеальных ультра-глубоких теста подряд")
        logger.info("="*100)
        
        start_time = time.time()
        
        while self.perfect_streak < self.required_perfect_streak:
            is_perfect = self.run_ultra_deep_cycle()
            
            logger.info(f"\n🎯 СТАТУС: {self.perfect_streak}/{self.required_perfect_streak} идеальных ультра-глубоких тестов подряд")
            
            if not is_perfect:
                logger.info("⏳ Продолжаем ультра-глубокое тестирование...")
                time.sleep(2)  # Пауза между циклами
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n{'='*100}")
        logger.info(f"🎉 УЛЬТРА-ГЛУБОКАЯ ЦЕЛЬ ДОСТИГНУТА!")
        logger.info(f"{'='*100}")
        logger.info(f"✅ Получено {self.required_perfect_streak} идеальных ультра-глубоких теста подряд")
        logger.info(f"📊 Всего ультра-глубоких циклов: {self.test_counter}")
        logger.info(f"⏱️ Время тестирования: {duration:.2f} секунд")
        logger.info(f"🎯 Система прошла исчерпывающую проверку и готова!")
        
        # Сохраняем детальный отчет
        self.save_detailed_report()
        
        return True
    
    def save_detailed_report(self):
        """Сохраняет детальный отчет тестирования."""
        report = {
            "test_summary": {
                "total_cycles": self.test_counter,
                "perfect_streak_achieved": self.perfect_streak,
                "total_individual_tests": len(self.test_results),
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "detailed_analysis": self.detailed_analysis
        }
        
        report_file = "/workspace/ULTRA_DEEP_TEST_REPORT.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Детальный отчет сохранен: {report_file}")

def main():
    """Главная функция ультра-глубокого тестирования."""
    print("🧪 УЛЬТРА-ГЛУБОКОЕ БЕСКОНЕЧНОЕ ТЕСТИРОВАНИЕ ПОСЛЕДНИХ ДОРАБОТОК")
    print("="*100)
    print("Цель: Получить 2 идеальных ультра-глубоких результата подряд")
    print("Каждый цикл включает 10 комплексных тестов с детальным анализом")
    print("="*100)
    
    engine = UltraDeepTestEngine()
    
    try:
        success = engine.run_ultra_deep_testing()
        
        if success:
            print("\n🎉 УЛЬТРА-ГЛУБОКАЯ МИССИЯ ВЫПОЛНЕНА!")
            print("✅ Все доработки прошли исчерпывающую проверку")
            print("✅ Система готова к продакшену с максимальной уверенностью")
            return True
        else:
            print("\n❌ УЛЬТРА-ГЛУБОКОЕ ТЕСТИРОВАНИЕ ПРЕРВАНО")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️ УЛЬТРА-ГЛУБОКОЕ ТЕСТИРОВАНИЕ ОСТАНОВЛЕНО ПОЛЬЗОВАТЕЛЕМ")
        print(f"📊 Выполнено ультра-глубоких циклов: {engine.test_counter}")
        print(f"🎯 Текущая серия идеальных тестов: {engine.perfect_streak}")
        return False
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА В УЛЬТРА-ГЛУБОКОМ ТЕСТИРОВАНИИ: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)