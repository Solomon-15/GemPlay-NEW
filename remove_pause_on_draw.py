#!/usr/bin/env python3
"""
Скрипт для удаления логики pause_on_draw из frontend
"""

import re
import os

def remove_pause_on_draw_from_file(file_path):
    """Удаляет pause_on_draw из файла"""
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return False
    
    print(f"🔧 Обрабатываем: {os.path.basename(file_path)}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # 1. Удаляем поля pause_on_draw из объектов
    patterns_to_remove = [
        r'pause_on_draw:\s*\d+,?\s*',
        r'pause_on_draw:\s*botForm\.pause_on_draw,?\s*',
        r'pause_on_draw:\s*parseInt\([^)]+\)\s*\|\|\s*\d+,?\s*',
        r'pause_on_draw:\s*[^,\n}]+,?\s*'
    ]
    
    for pattern in patterns_to_remove:
        matches = re.findall(pattern, content)
        if matches:
            print(f"   Найдено {len(matches)} упоминаний pause_on_draw")
            content = re.sub(pattern, '// УДАЛЕНО: pause_on_draw\n', content)
            changes_made += len(matches)
    
    # 2. Удаляем UI элементы с "Пауза при ничье"
    ui_pattern = r'\{/\*\s*Пауза при ничье\s*\*/\}.*?</div>\s*</div>'
    ui_matches = re.findall(ui_pattern, content, re.DOTALL)
    if ui_matches:
        print(f"   Найдено {len(ui_matches)} UI элементов")
        content = re.sub(ui_pattern, '{/* УДАЛЕНО: Пауза при ничье - логика полностью удалена */}', content, flags=re.DOTALL)
        changes_made += len(ui_matches)
    
    # 3. Удаляем валидацию pause_on_draw
    validation_pattern = r'if\s*\(\s*formData\.pause_on_draw.*?\)\s*\{[^}]*\}'
    validation_matches = re.findall(validation_pattern, content, re.DOTALL)
    if validation_matches:
        print(f"   Найдено {len(validation_matches)} валидаций")
        content = re.sub(validation_pattern, '// УДАЛЕНО: валидация pause_on_draw', content, flags=re.DOTALL)
        changes_made += len(validation_matches)
    
    # 4. Удаляем обработчики onChange для pause_on_draw
    onchange_pattern = r'onChange=\{[^}]*pause_on_draw[^}]*\}'
    onchange_matches = re.findall(onchange_pattern, content)
    if onchange_matches:
        print(f"   Найдено {len(onchange_matches)} обработчиков onChange")
        content = re.sub(onchange_pattern, '// УДАЛЕНО: onChange для pause_on_draw', content)
        changes_made += len(onchange_matches)
    
    if changes_made > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ Сделано {changes_made} изменений")
        return True
    else:
        print(f"   ℹ️  Изменений не требуется")
        return False

def main():
    print("🗑️ УДАЛЕНИЕ ЛОГИКИ PAUSE_ON_DRAW ИЗ FRONTEND")
    print("=" * 50)
    
    files_to_process = [
        "/workspace/frontend/src/components/RegularBotsManagement.js",
        "/workspace/frontend/src/components/RegularBotsManagement.js.bak"
    ]
    
    total_changes = 0
    
    for file_path in files_to_process:
        if remove_pause_on_draw_from_file(file_path):
            total_changes += 1
    
    print(f"\n📊 ИТОГО:")
    print(f"   Обработано файлов: {len(files_to_process)}")
    print(f"   Изменено файлов: {total_changes}")
    
    if total_changes > 0:
        print(f"\n✅ ЛОГИКА PAUSE_ON_DRAW УДАЛЕНА!")
        print("   - Удалены поля из объектов")
        print("   - Удалены UI элементы")
        print("   - Удалена валидация")
        print("   - Удалены обработчики событий")
    else:
        print(f"\nℹ️  Логика уже была удалена или не найдена")

if __name__ == "__main__":
    main()