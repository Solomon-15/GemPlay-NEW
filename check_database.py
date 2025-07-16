#!/usr/bin/env python3
"""
Скрипт для проверки коллекций в MongoDB
"""

import asyncio
from pymongo import MongoClient
import os

async def check_database_collections():
    """Проверка коллекций в базе данных"""
    
    # Подключение к MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/gemplay')
    client = MongoClient(mongo_url)
    db = client.gemplay
    
    print("=== ПРОВЕРКА КОЛЛЕКЦИЙ В БАЗЕ ДАННЫХ ===")
    
    # Получаем все коллекции
    collections = db.list_collection_names()
    print(f"📊 Найдено коллекций: {len(collections)}")
    
    for collection_name in collections:
        count = db[collection_name].count_documents({})
        print(f"   - {collection_name}: {count} документов")
        
        if collection_name == "bots" or "bot" in collection_name:
            print(f"     👀 Проверяем коллекцию {collection_name}:")
            # Получаем первые 3 документа
            docs = list(db[collection_name].find({}).limit(3))
            for doc in docs:
                print(f"       - {doc.get('name', doc.get('id', 'Unknown'))}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_database_collections())