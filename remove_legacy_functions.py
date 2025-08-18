#!/usr/bin/env python3
"""
Скрипт для удаления deprecated функций из server.py
"""

import re

def remove_legacy_functions():
    # Читаем файл
    with open('/workspace/backend/server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Поиск deprecated функций...")
    
    # 1. Удаляем update_bot_cycle_stats
    pattern1 = r'# DEPRECATED: replaced by bot_profit_accumulators\nasync def update_bot_cycle_stats.*?logger\.error\(f"Error updating bot cycle stats for \{bot_id\}: \{e\}"\)'
    matches1 = re.findall(pattern1, content, re.DOTALL)
    if matches1:
        print(f"✅ Найдена функция update_bot_cycle_stats")
        content = re.sub(pattern1, '# Legacy update_bot_cycle_stats function removed - using bot_profit_accumulators system', content, flags=re.DOTALL)
    
    # 2. Удаляем schedule_draw_replacement_bet
    pattern2 = r'# Removed legacy draw replacement scheduling:.*?\nasync def schedule_draw_replacement_bet.*?return'
    matches2 = re.findall(pattern2, content, re.DOTALL)
    if matches2:
        print(f"✅ Найдена функция schedule_draw_replacement_bet")
        content = re.sub(pattern2, '# Legacy schedule_draw_replacement_bet function removed', content, flags=re.DOTALL)
    
    # 3. Удаляем check_and_complete_bot_cycle
    pattern3 = r'# DEPRECATED: replaced by complete_bot_cycle via accumulators\nasync def check_and_complete_bot_cycle.*?return False'
    matches3 = re.findall(pattern3, content, re.DOTALL)
    if matches3:
        print(f"✅ Найдена функция check_and_complete_bot_cycle")
        content = re.sub(pattern3, '# Legacy check_and_complete_bot_cycle function removed - using complete_bot_cycle via accumulators', content, flags=re.DOTALL)
    
    # Записываем обратно
    with open('/workspace/backend/server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Deprecated функции удалены из server.py")

if __name__ == "__main__":
    remove_legacy_functions()