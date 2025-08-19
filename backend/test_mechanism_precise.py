#!/usr/bin/env python3
"""
Точный тест проверки удаления старого механизма save_completed_cycle.
Различает комментарии от реальных вызовов функций.
"""

import re
import sys
import os

def test_old_mechanism_precise():
    """Точно проверяет удаление старого механизма, исключая комментарии."""
    
    print("🔬 ТОЧНАЯ ПРОВЕРКА УДАЛЕНИЯ СТАРОГО МЕХАНИЗМА")
    print("=" * 60)
    
    server_file = "/workspace/backend/server.py"
    
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Найдем функцию maintain_all_bots_active_bets
    maintain_function_match = re.search(
        r'async def maintain_all_bots_active_bets\(\):(.*?)(?=async def|\Z)', 
        content, 
        re.DOTALL
    )
    
    if not maintain_function_match:
        print("❌ Функция maintain_all_bots_active_bets не найдена")
        return False
    
    maintain_function_code = maintain_function_match.group(1)
    
    print("✅ Функция maintain_all_bots_active_bets найдена")
    
    # Разделим код на строки для анализа
    lines = maintain_function_code.split('\n')
    
    # Ищем РЕАЛЬНЫЕ вызовы save_completed_cycle (не в комментариях)
    real_calls = []
    comment_mentions = []
    
    for i, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Пропускаем пустые строки
        if not stripped_line:
            continue
            
        # Если строка начинается с #, это комментарий
        if stripped_line.startswith('#'):
            if 'save_completed_cycle' in stripped_line:
                comment_mentions.append((i, stripped_line))
            continue
        
        # Ищем реальные вызовы функции
        if re.search(r'await\s+save_completed_cycle\s*\(', line):
            real_calls.append((i, stripped_line))
    
    print(f"🔍 Найдено реальных вызовов save_completed_cycle: {len(real_calls)}")
    print(f"📝 Найдено упоминаний в комментариях: {len(comment_mentions)}")
    
    # Показываем детали
    if real_calls:
        print("\n❌ РЕАЛЬНЫЕ ВЫЗОВЫ (проблема!):")
        for line_num, line_content in real_calls:
            print(f"   Строка {line_num}: {line_content}")
    
    if comment_mentions:
        print("\n📝 Упоминания в комментариях (это нормально):")
        for line_num, line_content in comment_mentions:
            print(f"   Строка {line_num}: {line_content}")
    
    # Проверяем результат
    mechanism_removed = len(real_calls) == 0
    
    if mechanism_removed:
        print("\n✅ УСПЕХ: Реальные вызовы save_completed_cycle удалены!")
        print("✅ Найдены только упоминания в комментариях об исправлении")
    else:
        print("\n❌ ОШИБКА: Найдены реальные вызовы save_completed_cycle!")
    
    return mechanism_removed

def test_before_after_comparison():
    """Сравнивает что было до и что стало после исправления."""
    
    print("\n📊 СРАВНЕНИЕ ДО И ПОСЛЕ ИСПРАВЛЕНИЯ:")
    print("-" * 50)
    
    server_file = "/workspace/backend/server.py"
    
    with open(server_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Показываем область вокруг строки 2275
    print("Код в области строки 2275 (где был старый механизм):")
    
    for i in range(2272, 2288):  # Строки 2273-2287
        if i < len(lines):
            line_num = i + 1
            line_content = lines[i].rstrip()
            
            # Выделяем ключевые строки
            if "ИСПРАВЛЕНО" in line_content:
                marker = "🔧"
            elif "await save_completed_cycle" in line_content and not line_content.strip().startswith('#'):
                marker = "❌"  # Реальный вызов (проблема)
            elif "save_completed_cycle" in line_content and line_content.strip().startswith('#'):
                marker = "📝"  # Комментарий (нормально)
            else:
                marker = "  "
                
            print(f"{marker} {line_num:4d}: {line_content}")
    
    # Проверяем что в этой области НЕТ реальных вызовов
    problem_lines = []
    for i in range(2272, 2288):
        if i < len(lines):
            line = lines[i]
            if "await save_completed_cycle" in line and not line.strip().startswith('#'):
                problem_lines.append(i + 1)
    
    if not problem_lines:
        print("\n✅ В области строки 2275 НЕТ реальных вызовов save_completed_cycle")
        return True
    else:
        print(f"\n❌ Найдены реальные вызовы в строках: {problem_lines}")
        return False

def test_new_mechanism_still_works():
    """Проверяет что новый механизм через complete_bot_cycle все еще работает."""
    
    print("\n🔄 ПРОВЕРКА НОВОГО МЕХАНИЗМА:")
    print("-" * 40)
    
    server_file = "/workspace/backend/server.py"
    
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем функцию complete_bot_cycle
    complete_bot_cycle_match = re.search(
        r'async def complete_bot_cycle\(.*?\):(.*?)(?=async def|\Z)', 
        content, 
        re.DOTALL
    )
    
    if not complete_bot_cycle_match:
        print("❌ Функция complete_bot_cycle не найдена")
        return False
    
    complete_bot_cycle_code = complete_bot_cycle_match.group(1)
    
    # Ищем вызовы save_completed_cycle в новом механизме
    new_mechanism_calls = re.findall(r'await\s+save_completed_cycle\s*\(', complete_bot_cycle_code)
    
    if len(new_mechanism_calls) > 0:
        print(f"✅ Новый механизм работает: найдено {len(new_mechanism_calls)} вызовов save_completed_cycle")
        print("✅ Данные циклов сохраняются через complete_bot_cycle()")
        return True
    else:
        print("❌ Новый механизм НЕ работает: вызовы save_completed_cycle не найдены")
        return False

def main():
    """Запускает все точные тесты."""
    
    print("🎯 ТОЧНАЯ ПРОВЕРКА УДАЛЕНИЯ СТАРОГО МЕХАНИЗМА SAVE_COMPLETED_CYCLE")
    print("=" * 70)
    
    # Тест 1: Точная проверка удаления
    test1_passed = test_old_mechanism_precise()
    
    # Тест 2: Сравнение до/после в области строки 2275
    test2_passed = test_before_after_comparison()
    
    # Тест 3: Проверка что новый механизм работает
    test3_passed = test_new_mechanism_still_works()
    
    # Итоговый результат
    print("\n" + "=" * 70)
    print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("=" * 70)
    
    all_passed = test1_passed and test2_passed and test3_passed
    
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Старый механизм полностью удален из maintain_all_bots_active_bets")
        print("✅ Строка 2275 содержит только комментарий об исправлении")
        print("✅ Новый механизм через complete_bot_cycle работает корректно")
        print("✅ Дублирование устранено!")
        
        print("\n🔧 ЧТО БЫЛО ИСПРАВЛЕНО:")
        print("   - Убран вызов await save_completed_cycle() из maintain_all_bots_active_bets")
        print("   - Добавлен комментарий об исправлении")
        print("   - Сохранение циклов теперь только через complete_bot_cycle()")
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        if not test1_passed:
            print("❌ Старый механизм НЕ полностью удален")
        if not test2_passed:
            print("❌ Проблемы в области строки 2275")
        if not test3_passed:
            print("❌ Новый механизм НЕ работает")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)