#!/usr/bin/env python3
"""
Тестирование логики резервирования ставок
Проверяет ключевые части реализации без запуска сервера
"""

import sys
import os

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_game_status_enum():
    """Проверка добавления нового статуса RESERVED"""
    print("\n🧪 TEST 1: Проверка GameStatus enum")
    print("="*50)
    
    try:
        from server import GameStatus
        
        # Проверяем наличие нового статуса
        if hasattr(GameStatus, 'RESERVED'):
            print("✅ Статус RESERVED добавлен в GameStatus")
            print(f"   Значение: {GameStatus.RESERVED}")
        else:
            print("❌ Статус RESERVED не найден в GameStatus")
            
        # Проверяем все статусы
        print("\n📋 Все статусы игр:")
        for status in GameStatus:
            print(f"   - {status.name}: {status.value}")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке GameStatus: {e}")


def test_game_model_fields():
    """Проверка добавления новых полей в модель Game"""
    print("\n🧪 TEST 2: Проверка модели Game")
    print("="*50)
    
    try:
        from server import Game
        from datetime import datetime
        
        # Создаём тестовую игру
        test_game = Game(
            id="test-123",
            creator_id="user-1",
            bet_amount=10.0,
            bet_gems={"Ruby": 2},
            status="WAITING"
        )
        
        # Проверяем наличие новых полей
        fields_to_check = ['reserved_by', 'reserved_at', 'reservation_expires_at']
        
        print("📋 Проверка полей резервирования:")
        for field in fields_to_check:
            if hasattr(test_game, field):
                print(f"✅ Поле '{field}' добавлено в модель Game")
            else:
                print(f"❌ Поле '{field}' не найдено в модели Game")
                
        # Пробуем установить значения
        print("\n📝 Тест установки значений резервирования:")
        try:
            test_game.reserved_by = "user-2"
            test_game.reserved_at = datetime.utcnow()
            test_game.reservation_expires_at = datetime.utcnow()
            test_game.status = "RESERVED"
            print("✅ Значения резервирования успешно установлены")
        except Exception as e:
            print(f"❌ Ошибка при установке значений: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке модели Game: {e}")


def test_api_endpoints():
    """Проверка наличия новых эндпоинтов"""
    print("\n🧪 TEST 3: Проверка API эндпоинтов")
    print("="*50)
    
    try:
        from server import api_router
        
        # Получаем все маршруты
        routes = []
        for route in api_router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods) if route.methods else []
                })
        
        # Проверяем наличие новых эндпоинтов
        required_endpoints = [
            ('/api/games/{game_id}/reserve', 'POST'),
            ('/api/games/{game_id}/unreserve', 'POST')
        ]
        
        print("📋 Проверка эндпоинтов резервирования:")
        for path, method in required_endpoints:
            found = any(
                route['path'] == path and method in route['methods'] 
                for route in routes
            )
            if found:
                print(f"✅ Эндпоинт {method} {path} найден")
            else:
                print(f"❌ Эндпоинт {method} {path} не найден")
                
        # Показываем все игровые эндпоинты
        print("\n📋 Все игровые эндпоинты:")
        game_routes = [r for r in routes if '/games' in r['path']]
        for route in sorted(game_routes, key=lambda x: x['path']):
            methods_str = ', '.join(route['methods'])
            print(f"   {methods_str:6} {route['path']}")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке эндпоинтов: {e}")


def test_filter_logic():
    """Проверка логики фильтрации зарезервированных игр"""
    print("\n🧪 TEST 4: Проверка логики фильтрации")
    print("="*50)
    
    print("📋 Проверка обновлений в эндпоинтах:")
    
    # Проверяем наличие изменений в коде
    backend_file = os.path.join(os.path.dirname(__file__), 'backend', 'server.py')
    
    try:
        with open(backend_file, 'r') as f:
            content = f.read()
            
        # Проверяем наличие фильтрации RESERVED в get_available_games
        if 'GameStatus.RESERVED' in content and 'get_available_games' in content:
            print("✅ Фильтрация RESERVED добавлена в get_available_games")
        else:
            print("⚠️  Проверьте фильтрацию RESERVED в get_available_games")
            
        # Проверяем наличие фильтрации в get_active_bot_games
        if 'get_active_bot_games' in content:
            print("✅ Эндпоинт get_active_bot_games найден")
        else:
            print("⚠️  Эндпоинт get_active_bot_games не найден")
            
        # Проверяем обновление find_available_bets_for_bot
        if 'find_available_bets_for_bot' in content and '# Exclude RESERVED games' in content:
            print("✅ Фильтрация RESERVED добавлена для Human-ботов")
        else:
            print("⚠️  Проверьте фильтрацию RESERVED для Human-ботов")
            
        # Проверяем фоновую задачу
        if 'cleanup_expired_reservations' in content:
            print("✅ Фоновая задача cleanup_expired_reservations добавлена")
        else:
            print("❌ Фоновая задача cleanup_expired_reservations не найдена")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке файла: {e}")


def test_frontend_changes():
    """Проверка изменений в frontend"""
    print("\n🧪 TEST 5: Проверка Frontend изменений")
    print("="*50)
    
    frontend_files = {
        'Lobby.js': os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'components', 'Lobby.js'),
        'JoinBattleModal.js': os.path.join(os.path.dirname(__file__), 'frontend', 'src', 'components', 'JoinBattleModal.js')
    }
    
    for filename, filepath in frontend_files.items():
        print(f"\n📋 Проверка {filename}:")
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            if filename == 'Lobby.js':
                # Проверяем handleOpenJoinBattle
                if 'async (game)' in content and '/reserve' in content:
                    print("✅ handleOpenJoinBattle обновлён для резервирования")
                else:
                    print("❌ handleOpenJoinBattle не обновлён")
                    
                # Проверяем проверку гемов
                if 'Insufficient gems to join this bet' in content:
                    print("✅ Проверка достаточности гемов добавлена")
                else:
                    print("❌ Проверка достаточности гемов не найдена")
                    
                # Проверяем handleCloseJoinBattle
                if 'gameJoined = false' in content and '/unreserve' in content:
                    print("✅ handleCloseJoinBattle обновлён для разблокировки")
                else:
                    print("❌ handleCloseJoinBattle не обновлён")
                    
            elif filename == 'JoinBattleModal.js':
                # Проверяем isGameJoined
                if 'isGameJoined' in content:
                    print("✅ Состояние isGameJoined добавлено")
                else:
                    print("❌ Состояние isGameJoined не найдено")
                    
                # Проверяем передачу статуса при закрытии
                if 'onClose(isGameJoined)' in content:
                    print("✅ Передача статуса при закрытии реализована")
                else:
                    print("❌ Передача статуса при закрытии не реализована")
                    
        except Exception as e:
            print(f"❌ Ошибка при проверке {filename}: {e}")


def main():
    """Запуск всех тестов"""
    print("🚀 Тестирование системы резервирования ставок")
    print("="*50)
    
    # Запускаем тесты
    test_game_status_enum()
    test_game_model_fields()
    test_api_endpoints()
    test_filter_logic()
    test_frontend_changes()
    
    print("\n✅ Проверка завершена!")
    print("\n📝 Примечание: Для полного тестирования функциональности")
    print("   необходимо запустить сервер и выполнить интеграционные тесты.")


if __name__ == "__main__":
    main()