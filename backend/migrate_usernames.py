"""
Скрипт миграции для преобразования существующих имён пользователей в латиницу
"""

import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from username_utils import process_username, get_username_suggestions
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def migrate_usernames():
    """Основная функция миграции пользователей"""
    
    # Подключение к базе данных
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Получаем всех пользователей
        users_cursor = db.users.find({})
        users = await users_cursor.to_list(length=None)
        
        logger.info(f"Найдено пользователей для обработки: {len(users)}")
        
        migration_stats = {
            'total': len(users),
            'changed': 0,
            'duplicates_resolved': 0,
            'errors': 0,
            'unchanged': 0
        }
        
        # Отслеживание существующих имён для предотвращения дубликатов
        existing_usernames = set()
        
        # Сначала собираем все существующие имена пользователей
        async for user in db.users.find({}, {"username": 1}):
            existing_usernames.add(user["username"].lower())
        
        processed_users = []
        
        for user in users:
            try:
                original_username = user.get('username', '')
                user_id = user.get('id') or user.get('_id')
                
                # Обрабатываем имя пользователя
                result = process_username(original_username)
                
                if result['is_valid'] and not result['changed']:
                    # Имя уже корректное
                    migration_stats['unchanged'] += 1
                    logger.debug(f"Пользователь {user_id}: имя '{original_username}' уже корректное")
                    continue
                
                new_username = result['sanitized']
                
                # Проверяем, что новое имя валидно
                if not result['is_valid'] or not new_username:
                    logger.warning(f"Не удалось обработать имя '{original_username}' для пользователя {user_id}")
                    # Генерируем предложения
                    suggestions = get_username_suggestions(original_username)
                    if suggestions:
                        new_username = suggestions[0]
                        logger.info(f"Используем сгенерированное имя '{new_username}' для пользователя {user_id}")
                    else:
                        new_username = f"user_{user_id[:8]}"
                        logger.info(f"Используем fallback имя '{new_username}' для пользователя {user_id}")
                
                # Проверяем на дубликат
                username_lower = new_username.lower()
                if username_lower in existing_usernames:
                    # Генерируем уникальное имя
                    counter = 1
                    while f"{new_username}{counter}".lower() in existing_usernames:
                        counter += 1
                    new_username = f"{new_username}{counter}"
                    migration_stats['duplicates_resolved'] += 1
                    logger.info(f"Разрешён дубликат: '{original_username}' -> '{new_username}'")
                
                # Добавляем в список обработанных
                processed_users.append({
                    'filter': {'id': user_id},
                    'update': {'$set': {'username': new_username}},
                    'original': original_username,
                    'new': new_username
                })
                
                # Добавляем в список существующих имён
                existing_usernames.add(new_username.lower())
                migration_stats['changed'] += 1
                
                logger.info(f"Пользователь {user_id}: '{original_username}' -> '{new_username}'")
                
            except Exception as e:
                migration_stats['errors'] += 1
                logger.error(f"Ошибка обработки пользователя {user_id}: {e}")
        
        # Выполняем массовое обновление
        if processed_users:
            logger.info(f"Обновляем {len(processed_users)} пользователей в базе данных...")
            
            for user_update in processed_users:
                try:
                    result = await db.users.update_one(
                        user_update['filter'],
                        user_update['update']
                    )
                    
                    if result.modified_count == 0:
                        logger.warning(f"Не удалось обновить пользователя с фильтром {user_update['filter']}")
                        
                except Exception as e:
                    logger.error(f"Ошибка обновления пользователя: {e}")
                    migration_stats['errors'] += 1
        
        # Выводим статистику
        logger.info("=== РЕЗУЛЬТАТЫ МИГРАЦИИ ===")
        logger.info(f"Всего пользователей: {migration_stats['total']}")
        logger.info(f"Изменено имён: {migration_stats['changed']}")
        logger.info(f"Без изменений: {migration_stats['unchanged']}")
        logger.info(f"Дубликатов разрешено: {migration_stats['duplicates_resolved']}")
        logger.info(f"Ошибок: {migration_stats['errors']}")
        
        # Проверяем результат
        logger.info("=== ПРОВЕРКА РЕЗУЛЬТАТОВ ===")
        invalid_users = []
        async for user in db.users.find({}, {"id": 1, "username": 1}):
            username = user.get('username', '')
            result = process_username(username)
            if not result['is_valid']:
                invalid_users.append({
                    'id': user.get('id'),
                    'username': username,
                    'errors': result['errors']
                })
        
        if invalid_users:
            logger.warning(f"Остались пользователи с невалидными именами: {len(invalid_users)}")
            for user in invalid_users[:5]:  # Показываем первых 5
                logger.warning(f"ID: {user['id']}, Username: '{user['username']}', Errors: {user['errors']}")
        else:
            logger.info("✅ Все имена пользователей теперь валидны!")
            
    except Exception as e:
        logger.error(f"Критическая ошибка миграции: {e}")
    finally:
        client.close()

async def check_usernames_status():
    """Проверяет статус имён пользователей без изменений"""
    
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        stats = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'cyrillic': 0,
            'empty': 0
        }
        
        invalid_examples = []
        
        async for user in db.users.find({}, {"id": 1, "username": 1}):
            stats['total'] += 1
            username = user.get('username', '')
            
            if not username:
                stats['empty'] += 1
                continue
                
            result = process_username(username)
            
            if result['is_valid'] and not result['changed']:
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
                
                if result['changed']:
                    stats['cyrillic'] += 1
                    
                if len(invalid_examples) < 5:
                    invalid_examples.append({
                        'id': user.get('id'),
                        'original': username,
                        'sanitized': result['sanitized'],
                        'errors': result['errors']
                    })
        
        logger.info("=== СТАТУС ИМЁН ПОЛЬЗОВАТЕЛЕЙ ===")
        logger.info(f"Всего пользователей: {stats['total']}")
        logger.info(f"Валидных имён: {stats['valid']}")
        logger.info(f"Невалидных имён: {stats['invalid']}")
        logger.info(f"Требуют транслитерации: {stats['cyrillic']}")
        logger.info(f"Пустых имён: {stats['empty']}")
        
        if invalid_examples:
            logger.info("=== ПРИМЕРЫ НЕВАЛИДНЫХ ИМЁН ===")
            for example in invalid_examples:
                logger.info(f"ID: {example['id']}")
                logger.info(f"  Оригинал: '{example['original']}'")
                logger.info(f"  После обработки: '{example['sanitized']}'")
                logger.info(f"  Ошибки: {example['errors']}")
                logger.info("---")
                
    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Режим проверки без изменений
        asyncio.run(check_usernames_status())
    else:
        # Режим миграции
        print("ВНИМАНИЕ: Этот скрипт изменит имена пользователей в базе данных!")
        print("Для проверки без изменений используйте: python migrate_usernames.py check")
        
        confirm = input("Продолжить миграцию? (да/нет): ").lower().strip()
        if confirm in ['да', 'yes', 'y', 'д']:
            asyncio.run(migrate_usernames())
        else:
            print("Миграция отменена.")