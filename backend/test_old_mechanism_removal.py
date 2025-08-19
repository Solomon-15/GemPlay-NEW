#!/usr/bin/env python3
"""
Тест для проверки удаления старого механизма save_completed_cycle
из функции maintain_all_bots_active_bets.
"""

import re
import sys
import os

def test_old_mechanism_removal():
    """Проверяет что старый механизм save_completed_cycle удален из maintain_all_bots_active_bets."""
    
    print("🧪 Тестирование удаления старого механизма save_completed_cycle")
    print("=" * 70)
    
    server_file = "/workspace/backend/server.py"
    
    if not os.path.exists(server_file):
        print("❌ Файл server.py не найден")
        return False
    
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
    
    # Проверяем что в функции НЕТ прямых вызовов save_completed_cycle
    save_cycle_calls = re.findall(r'await save_completed_cycle\(', maintain_function_code)
    
    print(f"🔍 Найдено прямых вызовов save_completed_cycle: {len(save_cycle_calls)}")
    
    if len(save_cycle_calls) == 0:
        print("✅ УСПЕХ: Прямые вызовы save_completed_cycle удалены из maintain_all_bots_active_bets")
        mechanism_removed = True
    else:
        print("❌ ОШИБКА: Найдены прямые вызовы save_completed_cycle в maintain_all_bots_active_bets:")
        for i, call in enumerate(save_cycle_calls, 1):
            print(f"   {i}. {call}")
        mechanism_removed = False
    
    # Проверяем наличие комментария об исправлении
    has_fix_comment = "ИСПРАВЛЕНО: Убрали дублированный вызов save_completed_cycle" in maintain_function_code
    
    if has_fix_comment:
        print("✅ Найден комментарий об исправлении дублирования")
    else:
        print("⚠️ Комментарий об исправлении не найден")
    
    # Проверяем что механизм аккумуляторов все еще работает
    # Ищем где вызывается save_completed_cycle в complete_bot_cycle
    complete_bot_cycle_match = re.search(
        r'async def complete_bot_cycle\(.*?\):(.*?)(?=async def|\Z)', 
        content, 
        re.DOTALL
    )
    
    if complete_bot_cycle_match:
        complete_bot_cycle_code = complete_bot_cycle_match.group(1)
        new_mechanism_calls = re.findall(r'await save_completed_cycle\(', complete_bot_cycle_code)
        
        if len(new_mechanism_calls) > 0:
            print(f"✅ Новый механизм через complete_bot_cycle работает ({len(new_mechanism_calls)} вызовов)")
            new_mechanism_active = True
        else:
            print("⚠️ Новый механизм через complete_bot_cycle не найден")
            new_mechanism_active = False
    else:
        print("❌ Функция complete_bot_cycle не найдена")
        new_mechanism_active = False
    
    # Итоговая проверка
    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print("=" * 70)
    
    if mechanism_removed and new_mechanism_active:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ:")
        print("   ✅ Старый механизм удален из maintain_all_bots_active_bets")
        print("   ✅ Новый механизм работает через complete_bot_cycle")
        print("   ✅ Дублирование устранено")
        return True
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
        if not mechanism_removed:
            print("   ❌ Старый механизм НЕ удален")
        if not new_mechanism_active:
            print("   ❌ Новый механизм НЕ работает")
        return False

def test_specific_line_2275():
    """Проверяет конкретно строку 2275 где был старый вызов."""
    
    print("\n🔍 ДЕТАЛЬНАЯ ПРОВЕРКА СТРОКИ 2275:")
    print("-" * 50)
    
    server_file = "/workspace/backend/server.py"
    
    with open(server_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Проверяем строки вокруг 2275
    start_line = max(0, 2273 - 1)  # -1 для 0-based индекса
    end_line = min(len(lines), 2285)
    
    print("Содержимое строк 2274-2284:")
    for i in range(start_line, end_line):
        line_num = i + 1
        line_content = lines[i].rstrip()
        marker = "👉" if line_num == 2275 else "  "
        print(f"{marker} {line_num:4d}: {line_content}")
    
    # Проверяем что в строке 2275 НЕТ вызова save_completed_cycle
    line_2275 = lines[2274] if len(lines) > 2274 else ""  # 2275-1 для 0-based
    
    if "save_completed_cycle" in line_2275:
        print("\n❌ ОШИБКА: В строке 2275 все еще есть вызов save_completed_cycle!")
        return False
    else:
        print(f"\n✅ УСПЕХ: Строка 2275 НЕ содержит вызов save_completed_cycle")
        if "ИСПРАВЛЕНО" in line_2275:
            print("✅ Найден комментарий об исправлении")
        return True

def main():
    """Запускает все тесты проверки удаления старого механизма."""
    
    print("🔬 ПРОВЕРКА УДАЛЕНИЯ СТАРОГО МЕХАНИЗМА SAVE_COMPLETED_CYCLE")
    print("=" * 70)
    
    # Тест 1: Общая проверка функции
    test1_passed = test_old_mechanism_removal()
    
    # Тест 2: Проверка конкретной строки 2275
    test2_passed = test_specific_line_2275()
    
    # Итоговый результат
    print("\n" + "=" * 70)
    print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("=" * 70)
    
    if test1_passed and test2_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Старый механизм успешно удален")
        print("✅ Строка 2275 исправлена")
        print("✅ Дублирование устранено")
        return True
    else:
        print("❌ ТЕСТЫ ПРОВАЛЕНЫ!")
        if not test1_passed:
            print("❌ Проблемы с удалением механизма")
        if not test2_passed:
            print("❌ Проблемы со строкой 2275")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)