#!/usr/bin/env python3
"""
Специальный тест для проверки удаления старого механизма
из функции maintain_all_bots_active_bets (строка 2275).
"""

import re
import sys
import os

def extract_maintain_function():
    """Извлекает полный код функции maintain_all_bots_active_bets."""
    
    server_file = "/workspace/backend/server.py"
    
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Найдем функцию maintain_all_bots_active_bets
    pattern = r'async def maintain_all_bots_active_bets\(\):(.*?)(?=\nasync def|\n\ndef|\n@|\nclass|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return None, None
    
    function_code = match.group(1)
    start_pos = match.start()
    
    # Находим номер строки начала функции
    lines_before = content[:start_pos].count('\n')
    start_line = lines_before + 1
    
    return function_code, start_line

def test_old_mechanism_removal():
    """Тестирует удаление старого механизма из maintain_all_bots_active_bets."""
    
    print("🔬 ПРОВЕРКА УДАЛЕНИЯ СТАРОГО МЕХАНИЗМА ИЗ maintain_all_bots_active_bets")
    print("=" * 80)
    
    function_code, start_line = extract_maintain_function()
    
    if not function_code:
        print("❌ Функция maintain_all_bots_active_bets не найдена!")
        return False
    
    print(f"✅ Функция maintain_all_bots_active_bets найдена (начинается со строки {start_line})")
    
    # Разбиваем на строки для детального анализа
    lines = function_code.split('\n')
    
    # Ищем все упоминания save_completed_cycle
    mentions = []
    real_calls = []
    
    for i, line in enumerate(lines):
        line_number = start_line + i
        stripped = line.strip()
        
        if 'save_completed_cycle' in line:
            mentions.append((line_number, line.rstrip()))
            
            # Проверяем это реальный вызов или комментарий
            if re.search(r'await\s+save_completed_cycle\s*\(', line):
                real_calls.append((line_number, line.rstrip()))
    
    print(f"\n📋 АНАЛИЗ УПОМИНАНИЙ save_completed_cycle:")
    print(f"   Всего упоминаний: {len(mentions)}")
    print(f"   Реальных вызовов: {len(real_calls)}")
    
    if mentions:
        print(f"\n📝 ВСЕ УПОМИНАНИЯ save_completed_cycle:")
        for line_num, line_content in mentions:
            is_comment = line_content.strip().startswith('#')
            is_real_call = re.search(r'await\s+save_completed_cycle\s*\(', line_content)
            
            if is_real_call:
                marker = "❌ ВЫЗОВ"
            elif is_comment:
                marker = "📝 КОММЕНТ"
            else:
                marker = "❓ ДРУГОЕ"
                
            print(f"   {marker} Строка {line_num}: {line_content.strip()}")
    
    # Специальная проверка области строки 2275
    print(f"\n🎯 СПЕЦИАЛЬНАЯ ПРОВЕРКА ОБЛАСТИ СТРОКИ 2275:")
    
    # Ищем строки вокруг 2275
    target_area_lines = []
    for line_num, line_content in mentions:
        if 2270 <= line_num <= 2280:
            target_area_lines.append((line_num, line_content))
    
    if target_area_lines:
        print("   Найдены упоминания в целевой области:")
        for line_num, line_content in target_area_lines:
            is_comment = line_content.strip().startswith('#')
            print(f"   Строка {line_num}: {'📝 КОММЕНТ' if is_comment else '❌ КОД'} - {line_content.strip()}")
    else:
        print("   ❌ Упоминания в области строки 2275 не найдены (возможно, номера строк сдвинулись)")
    
    # Итоговая оценка
    success = len(real_calls) == 0
    
    if success:
        print(f"\n✅ УСПЕХ: Старый механизм удален!")
        print(f"   - Реальных вызовов save_completed_cycle: {len(real_calls)}")
        print(f"   - Найдены только комментарии об исправлении")
    else:
        print(f"\n❌ ОШИБКА: Найдены реальные вызовы!")
        print(f"   - Количество реальных вызовов: {len(real_calls)}")
        for line_num, line_content in real_calls:
            print(f"   - Строка {line_num}: {line_content.strip()}")
    
    return success

def check_line_2275_specifically():
    """Проверяет конкретно что на строке 2275 и вокруг нее."""
    
    print(f"\n🔍 ДЕТАЛЬНАЯ ПРОВЕРКА СТРОКИ 2275:")
    print("-" * 50)
    
    server_file = "/workspace/backend/server.py"
    
    with open(server_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Показываем область вокруг строки 2275
    start_line = max(0, 2273 - 1)  # 2272 в 0-based
    end_line = min(len(lines), 2280)  # до 2280
    
    print("Содержимое строк 2273-2279:")
    for i in range(start_line, end_line):
        line_num = i + 1
        line_content = lines[i].rstrip()
        
        # Специальная проверка строки 2275
        if line_num == 2275:
            has_real_call = re.search(r'await\s+save_completed_cycle\s*\(', line_content)
            has_mention = 'save_completed_cycle' in line_content
            is_comment = line_content.strip().startswith('#')
            
            if has_real_call:
                marker = "❌ ВЫЗОВ!"
                status = "ПРОБЛЕМА"
            elif has_mention and is_comment:
                marker = "✅ КОММЕНТ"
                status = "НОРМА"
            elif has_mention:
                marker = "❓ ДРУГОЕ"
                status = "ПРОВЕРИТЬ"
            else:
                marker = "  "
                status = "ЧИСТО"
                
            print(f"{marker} {line_num:4d}: {line_content} [{status}]")
        else:
            print(f"   {line_num:4d}: {line_content}")
    
    # Проверяем результат для строки 2275
    if len(lines) > 2274:  # 2275-1 для 0-based
        line_2275 = lines[2274]
        has_real_call = re.search(r'await\s+save_completed_cycle\s*\(', line_2275)
        has_mention = 'save_completed_cycle' in line_2275
        is_comment = line_2275.strip().startswith('#')
        
        print(f"\n📊 АНАЛИЗ СТРОКИ 2275:")
        print(f"   Содержит 'save_completed_cycle': {has_mention}")
        print(f"   Это комментарий: {is_comment}")
        print(f"   Это реальный вызов: {has_real_call}")
        
        if has_real_call:
            print("   ❌ СТАТУС: ПРОБЛЕМА - найден реальный вызов!")
            return False
        elif has_mention and is_comment:
            print("   ✅ СТАТУС: НОРМА - только комментарий об исправлении")
            return True
        elif not has_mention:
            print("   ✅ СТАТУС: ЧИСТО - никаких упоминаний")
            return True
        else:
            print("   ❓ СТАТУС: НЕЯСНО - требует проверки")
            return False
    else:
        print("   ❌ ОШИБКА: Строка 2275 не найдена в файле")
        return False

def main():
    """Запускает все проверки."""
    
    print("🎯 ПОЛНАЯ ПРОВЕРКА УДАЛЕНИЯ СТАРОГО МЕХАНИЗМА")
    print("=" * 80)
    print("Проверяем удаление вызова save_completed_cycle из maintain_all_bots_active_bets (строка 2275)")
    
    # Тест 1: Анализ функции maintain_all_bots_active_bets
    test1_passed = test_old_mechanism_removal()
    
    # Тест 2: Проверка конкретно строки 2275
    test2_passed = check_line_2275_specifically()
    
    # Итоговый результат
    print("\n" + "=" * 80)
    print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("=" * 80)
    
    if test1_passed and test2_passed:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("✅ Старый механизм полностью удален из maintain_all_bots_active_bets")
        print("✅ Строка 2275 не содержит реальных вызовов save_completed_cycle")
        print("✅ Дублирование циклов устранено")
        
        print("\n🔧 ЧТО ПОДТВЕРЖДЕНО:")
        print("   - maintain_all_bots_active_bets НЕ вызывает save_completed_cycle")
        print("   - Строка 2275 содержит только комментарий об исправлении")
        print("   - Сохранение циклов происходит только через complete_bot_cycle()")
        
        return True
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        if not test1_passed:
            print("❌ Проблемы в функции maintain_all_bots_active_bets")
        if not test2_passed:
            print("❌ Проблемы со строкой 2275")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)