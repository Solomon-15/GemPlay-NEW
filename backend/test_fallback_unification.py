#!/usr/bin/env python3
"""
Тест унификации fallback значений с 12 на 16

ЦЕЛЬ: Все bot.get("cycle_games", X) должны использовать X = 16
для соответствия модели Bot где cycle_games: int = 16
"""

import os
import sys
import re

def test_fallback_unification():
    """Проверяет, что все fallback значения изменены с 12 на 16"""
    
    print("🔍 ТЕСТИРОВАНИЕ УНИФИКАЦИИ FALLBACK ЗНАЧЕНИЙ")
    print("=" * 50)
    
    try:
        with open('server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Счётчики
        total_checks = 0
        passed_checks = 0
        
        print("\n1️⃣ ПРОВЕРКА: НЕТ СТАРЫХ ЗНАЧЕНИЙ 12")
        print("-" * 35)
        
        # 1. Проверяем, что нет cycle_games с fallback 12
        old_patterns = [
            r'cycle_games["\'],?\s*12\)',
            r'cycle_games["\'],?\s*12\s*\)',
            r'\.get\(["\']cycle_games["\'],?\s*12\)'
        ]
        
        old_found = 0
        for pattern in old_patterns:
            matches = re.findall(pattern, content)
            old_found += len(matches)
            total_checks += 1
            
        if old_found == 0:
            print("   ✅ Старые fallback значения 12 удалены")
            passed_checks += 1
        else:
            print(f"   ❌ Найдено {old_found} старых fallback значений 12")
        
        print("\n2️⃣ ПРОВЕРКА: НОВЫЕ ЗНАЧЕНИЯ 16")
        print("-" * 30)
        
        # 2. Проверяем новые значения 16
        new_patterns = [
            r'cycle_games["\'],?\s*16\)',
            r'\.get\(["\']cycle_games["\'],?\s*16\)'
        ]
        
        new_found = 0
        for pattern in new_patterns:
            matches = re.findall(pattern, content)
            new_found += len(matches)
        
        expected_count = 20  # Ожидаемое количество замен
        total_checks += 1
        
        if new_found >= expected_count:
            print(f"   ✅ Найдено {new_found} новых fallback значений 16")
            passed_checks += 1
        else:
            print(f"   ❌ Найдено только {new_found} из {expected_count} ожидаемых значений 16")
        
        print("\n3️⃣ ПРОВЕРКА: СПЕЦИАЛЬНЫЕ СЛУЧАИ")
        print("-" * 32)
        
        # 3. Проверяем cycle_limit fallback
        cycle_limit_pattern = r'cycle_limit\s*=\s*16.*fallback'
        cycle_limit_matches = re.findall(cycle_limit_pattern, content)
        total_checks += 1
        
        if len(cycle_limit_matches) > 0:
            print("   ✅ cycle_limit fallback изменён на 16")
            passed_checks += 1
        else:
            print("   ❌ cycle_limit fallback не найден или не изменён")
        
        # 4. Проверяем "or 16" паттерны
        or_pattern = r'or\s+16\)'
        or_matches = re.findall(or_pattern, content)
        total_checks += 1
        
        if len(or_matches) >= 3:
            print(f"   ✅ Найдено {len(or_matches)} паттернов 'or 16'")
            passed_checks += 1
        else:
            print(f"   ❌ Найдено только {len(or_matches)} паттернов 'or 16'")
        
        print("\n4️⃣ ПРОВЕРКА: КОНСИСТЕНТНОСТЬ С МОДЕЛЬЮ")
        print("-" * 38)
        
        # 5. Проверяем, что модель Bot использует 16
        model_pattern = r'cycle_games:\s*int\s*=\s*16'
        model_matches = re.findall(model_pattern, content)
        total_checks += 1
        
        if len(model_matches) > 0:
            print("   ✅ Модель Bot использует cycle_games = 16")
            passed_checks += 1
        else:
            print("   ❌ Модель Bot не найдена или использует другое значение")
        
        return passed_checks, total_checks
        
    except FileNotFoundError:
        print("❌ Файл server.py не найден")
        return 0, 1
    except Exception as e:
        print(f"❌ Ошибка при проверке файла: {e}")
        return 0, 1

def show_examples():
    """Показывает примеры изменений"""
    
    print("\n📋 ПРИМЕРЫ ИЗМЕНЕНИЙ:")
    print("-" * 20)
    
    examples = [
        ("ДО", "bot.get(\"cycle_games\", 12)"),
        ("ПОСЛЕ", "bot.get(\"cycle_games\", 16)"),
        ("", ""),
        ("ДО", "cycle_limit = 12  # fallback"),
        ("ПОСЛЕ", "cycle_limit = 16  # fallback"),
        ("", ""),
        ("ДО", "int(bot.get(\"cycle_games\", 12) or 12)"),
        ("ПОСЛЕ", "int(bot.get(\"cycle_games\", 16) or 16)")
    ]
    
    for label, code in examples:
        if label:
            print(f"   {label}: {code}")
        else:
            print()

def main():
    """Основная функция теста"""
    
    print("🚀 ТЕСТ УНИФИКАЦИИ FALLBACK ЗНАЧЕНИЙ")
    print("=" * 40)
    
    # Тестируем изменения
    passed, total = test_fallback_unification()
    
    # Показываем примеры
    show_examples()
    
    # Итоговый результат
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("-" * 20)
    
    print(f"🔧 Проверок пройдено: {passed}/{total}")
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"📈 Процент успеха: {success_rate:.1f}%")
    
    if passed == total:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Fallback значения унифицированы с 12 на 16")
        print("✅ Система теперь консистентна с моделью Bot")
        
        print("\n🎯 ЧТО ИЗМЕНЕНО:")
        print("   • Все bot.get('cycle_games', X) теперь используют X = 16")
        print("   • cycle_limit fallback изменён на 16")
        print("   • Паттерны 'or 12' заменены на 'or 16'")
        print("   • Полное соответствие модели Bot")
        
        print("\n🚀 СИСТЕМА ГОТОВА К ТЕСТИРОВАНИЮ!")
        return True
    else:
        print("\n❌ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ!")
        print(f"   • Не пройдено: {total - passed} проверок")
        print("   • Требуется дополнительная корректировка")
        return False

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)