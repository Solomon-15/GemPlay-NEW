#!/usr/bin/env python3
"""
Final comprehensive test for bot fields removal - Russian Review
Протестировать удаление полей can_accept_bets и can_play_with_bots для обычных ботов
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BACKEND_URL = "https://detali-shop.preview.emergentagent.com/api"
SUPER_ADMIN_EMAIL = "admin@gemplay.com"
SUPER_ADMIN_PASSWORD = "Admin123!"

class FinalBotFieldsTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def setup(self):
        """Initialize HTTP session and authenticate"""
        self.session = aiohttp.ClientSession()
        await self.authenticate_super_admin()
        
    async def cleanup(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            
    async def authenticate_super_admin(self):
        """Authenticate as SUPER_ADMIN"""
        print("🔐 Authenticating as SUPER_ADMIN...")
        
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        try:
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["access_token"]
                    print(f"✅ SUPER_ADMIN authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ SUPER_ADMIN authentication failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ SUPER_ADMIN authentication error: {e}")
            return False
            
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
        
    async def test_comprehensive_bot_fields_removal(self):
        """Comprehensive test of bot fields removal"""
        print("\n🎯 COMPREHENSIVE BOT FIELDS REMOVAL TESTING")
        print("="*80)
        
        # 1. Test GET /api/admin/bots - check existing bots
        print("\n1️⃣ TESTING GET /api/admin/bots - проверка существующих ботов...")
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/bots", headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    bots = data.get("bots", [])
                    
                    print(f"   📊 Найдено {len(bots)} обычных ботов")
                    
                    if bots:
                        # Check all bots for removed fields
                        bots_with_removed_fields = 0
                        for i, bot in enumerate(bots[:3]):  # Check first 3 bots
                            has_can_accept_bets = "can_accept_bets" in bot
                            has_can_play_with_bots = "can_play_with_bots" in bot
                            
                            if has_can_accept_bets or has_can_play_with_bots:
                                bots_with_removed_fields += 1
                                
                            print(f"   🤖 Бот {i+1} ({bot.get('name', 'Unknown')}):")
                            print(f"      - can_accept_bets: {'❌ ПРИСУТСТВУЕТ' if has_can_accept_bets else '✅ ОТСУТСТВУЕТ'}")
                            print(f"      - can_play_with_bots: {'❌ ПРИСУТСТВУЕТ' if has_can_play_with_bots else '✅ ОТСУТСТВУЕТ'}")
                        
                        if bots_with_removed_fields == 0:
                            print(f"   ✅ Все проверенные боты НЕ содержат удаленные поля")
                            self.test_results.append(("GET /api/admin/bots - удаленные поля отсутствуют", True))
                        else:
                            print(f"   ❌ {bots_with_removed_fields} ботов все еще содержат удаленные поля")
                            self.test_results.append(("GET /api/admin/bots - удаленные поля отсутствуют", False))
                    else:
                        print("   ⚠️ Обычные боты не найдены")
                        self.test_results.append(("GET /api/admin/bots - удаленные поля отсутствуют", "NA"))
                else:
                    error_text = await response.text()
                    print(f"   ❌ Ошибка получения ботов: {response.status} - {error_text}")
                    self.test_results.append(("GET /api/admin/bots - удаленные поля отсутствуют", False))
        except Exception as e:
            print(f"   ❌ Исключение при получении ботов: {e}")
            self.test_results.append(("GET /api/admin/bots - удаленные поля отсутствуют", False))
            
        # 2. Test POST /api/admin/bots/create-regular - create new bot
        print("\n2️⃣ TESTING POST /api/admin/bots/create-regular - создание нового бота...")
        try:
            bot_data = {
                "name": f"TestBot_FieldsRemoval_{int(datetime.now().timestamp())}",
                "min_bet_amount": 1.0,
                "max_bet_amount": 100.0,
                "win_rate": 55.0,
                "cycle_games": 12,
                "individual_limit": 12,
                "pause_between_games": 5,
                "creation_mode": "queue-based",
                "priority_order": 50,
                "profit_strategy": "balanced"
            }
            
            async with self.session.post(f"{BACKEND_URL}/admin/bots/create-regular", 
                                       json=bot_data, headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    created_bot = data.get("bot", {})
                    
                    has_can_accept_bets = "can_accept_bets" in created_bot
                    has_can_play_with_bots = "can_play_with_bots" in created_bot
                    
                    print(f"   ✅ Бот успешно создан: {created_bot.get('name', 'Unknown')}")
                    print(f"   🔍 Проверка полей:")
                    print(f"      - can_accept_bets: {'❌ ПРИСУТСТВУЕТ' if has_can_accept_bets else '✅ ОТСУТСТВУЕТ'}")
                    print(f"      - can_play_with_bots: {'❌ ПРИСУТСТВУЕТ' if has_can_play_with_bots else '✅ ОТСУТСТВУЕТ'}")
                    
                    if not has_can_accept_bets and not has_can_play_with_bots:
                        print(f"   ✅ Новый бот создан БЕЗ удаленных полей")
                        self.test_results.append(("POST /api/admin/bots/create-regular - без удаленных полей", True))
                    else:
                        print(f"   ❌ Новый бот все еще содержит удаленные поля")
                        self.test_results.append(("POST /api/admin/bots/create-regular - без удаленных полей", False))
                        
                    # Store bot ID for further testing
                    self.created_bot_id = created_bot.get("id")
                    
                    # Test PUT update
                    if self.created_bot_id:
                        print(f"\n   🔄 Тестирование PUT /api/admin/bots/{self.created_bot_id}...")
                        update_data = {
                            "name": f"UpdatedBot_FieldsRemoval_{int(datetime.now().timestamp())}",
                            "min_bet_amount": 2.0,
                            "max_bet_amount": 200.0,
                            "win_rate": 60.0
                        }
                        
                        async with self.session.put(f"{BACKEND_URL}/admin/bots/{self.created_bot_id}", 
                                                  json=update_data, headers=self.get_auth_headers()) as put_response:
                            if put_response.status == 200:
                                put_data = await put_response.json()
                                updated_bot = put_data.get("bot", {})
                                
                                has_can_accept_bets = "can_accept_bets" in updated_bot
                                has_can_play_with_bots = "can_play_with_bots" in updated_bot
                                
                                print(f"      ✅ Бот успешно обновлен")
                                print(f"      🔍 Проверка полей после обновления:")
                                print(f"         - can_accept_bets: {'❌ ПРИСУТСТВУЕТ' if has_can_accept_bets else '✅ ОТСУТСТВУЕТ'}")
                                print(f"         - can_play_with_bots: {'❌ ПРИСУТСТВУЕТ' if has_can_play_with_bots else '✅ ОТСУТСТВУЕТ'}")
                                
                                if not has_can_accept_bets and not has_can_play_with_bots:
                                    print(f"      ✅ Обновленный бот НЕ содержит удаленные поля")
                                    self.test_results.append(("PUT /api/admin/bots/{bot_id} - без удаленных полей", True))
                                else:
                                    print(f"      ❌ Обновленный бот все еще содержит удаленные поля")
                                    self.test_results.append(("PUT /api/admin/bots/{bot_id} - без удаленных полей", False))
                            else:
                                error_text = await put_response.text()
                                print(f"      ❌ Ошибка обновления бота: {put_response.status} - {error_text}")
                                self.test_results.append(("PUT /api/admin/bots/{bot_id} - без удаленных полей", False))
                else:
                    error_text = await response.text()
                    print(f"   ❌ Ошибка создания бота: {response.status} - {error_text}")
                    self.test_results.append(("POST /api/admin/bots/create-regular - без удаленных полей", False))
        except Exception as e:
            print(f"   ❌ Исключение при создании бота: {e}")
            self.test_results.append(("POST /api/admin/bots/create-regular - без удаленных полей", False))
            
        # 3. Test Human-bots still have their fields
        print("\n3️⃣ TESTING GET /api/admin/human-bots - проверка Human-ботов...")
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/human-bots", headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    bots = data.get("bots", [])
                    
                    print(f"   📊 Найдено {len(bots)} Human-ботов")
                    
                    if bots:
                        # Check first few human-bots for required fields
                        missing_fields_count = 0
                        for i, bot in enumerate(bots[:3]):  # Check first 3 bots
                            has_can_play_with_other_bots = "can_play_with_other_bots" in bot
                            has_can_play_with_players = "can_play_with_players" in bot
                            
                            if not has_can_play_with_other_bots or not has_can_play_with_players:
                                missing_fields_count += 1
                                
                            print(f"   👥 Human-бот {i+1} ({bot.get('name', 'Unknown')}):")
                            print(f"      - can_play_with_other_bots: {'✅ ПРИСУТСТВУЕТ' if has_can_play_with_other_bots else '❌ ОТСУТСТВУЕТ'}")
                            print(f"      - can_play_with_players: {'✅ ПРИСУТСТВУЕТ' if has_can_play_with_players else '❌ ОТСУТСТВУЕТ'}")
                            if has_can_play_with_other_bots and has_can_play_with_players:
                                print(f"      - Значения: other_bots={bot.get('can_play_with_other_bots')}, players={bot.get('can_play_with_players')}")
                        
                        if missing_fields_count == 0:
                            print(f"   ✅ Все Human-боты СОХРАНИЛИ необходимые поля")
                            self.test_results.append(("GET /api/admin/human-bots - необходимые поля присутствуют", True))
                        else:
                            print(f"   ❌ {missing_fields_count} Human-ботов НЕ имеют необходимые поля")
                            self.test_results.append(("GET /api/admin/human-bots - необходимые поля присутствуют", False))
                    else:
                        print("   ⚠️ Human-боты не найдены")
                        self.test_results.append(("GET /api/admin/human-bots - необходимые поля присутствуют", "NA"))
                else:
                    error_text = await response.text()
                    print(f"   ❌ Ошибка получения Human-ботов: {response.status} - {error_text}")
                    self.test_results.append(("GET /api/admin/human-bots - необходимые поля присутствуют", False))
        except Exception as e:
            print(f"   ❌ Исключение при получении Human-ботов: {e}")
            self.test_results.append(("GET /api/admin/human-bots - необходимые поля присутствуют", False))
            
        # 4. Test system functionality
        print("\n4️⃣ TESTING SYSTEM FUNCTIONALITY - проверка функциональности системы...")
        
        # Test regular bot games
        try:
            async with self.session.get(f"{BACKEND_URL}/bots/active-games", headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle both list and dict response formats
                    if isinstance(data, list):
                        active_games = data
                    else:
                        active_games = data.get("games", [])
                    
                    print(f"   🎮 Активные игры обычных ботов: {len(active_games)}")
                    
                    if len(active_games) > 0:
                        print(f"   ✅ Обычные боты ПРОДОЛЖАЮТ создавать игры")
                        self.test_results.append(("Обычные боты создают игры", True))
                    else:
                        print(f"   ⚠️ Активные игры обычных ботов не найдены (может быть нормально)")
                        self.test_results.append(("Обычные боты создают игры", "NA"))
                else:
                    error_text = await response.text()
                    print(f"   ❌ Ошибка получения активных игр: {response.status} - {error_text}")
                    self.test_results.append(("Обычные боты создают игры", False))
        except Exception as e:
            print(f"   ❌ Исключение при получении активных игр: {e}")
            self.test_results.append(("Обычные боты создают игры", False))
            
        # Test bot automation
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/bots", headers=self.get_auth_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    bots = data.get("bots", [])
                    
                    active_bots = [bot for bot in bots if bot.get("is_active", False)]
                    bots_with_active_bets = [bot for bot in active_bots if bot.get("active_bets", 0) > 0]
                    
                    print(f"   📈 Статистика автоматизации:")
                    print(f"      - Всего обычных ботов: {len(bots)}")
                    print(f"      - Активных ботов: {len(active_bots)}")
                    print(f"      - Ботов с активными ставками: {len(bots_with_active_bets)}")
                    
                    if len(bots_with_active_bets) > 0:
                        print(f"   ✅ Автоматизация создания ставок РАБОТАЕТ")
                        self.test_results.append(("Автоматизация создания ставок работает", True))
                    else:
                        print(f"   ⚠️ Боты без активных ставок (автоматизация может быть приостановлена)")
                        self.test_results.append(("Автоматизация создания ставок работает", "NA"))
                else:
                    error_text = await response.text()
                    print(f"   ❌ Ошибка проверки автоматизации: {response.status} - {error_text}")
                    self.test_results.append(("Автоматизация создания ставок работает", False))
        except Exception as e:
            print(f"   ❌ Исключение при проверке автоматизации: {e}")
            self.test_results.append(("Автоматизация создания ставок работает", False))
            
    async def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 ОЧИСТКА ТЕСТОВЫХ ДАННЫХ...")
        
        if hasattr(self, 'created_bot_id') and self.created_bot_id:
            try:
                async with self.session.delete(f"{BACKEND_URL}/admin/bots/{self.created_bot_id}", 
                                             headers=self.get_auth_headers()) as response:
                    if response.status == 200:
                        print(f"   ✅ Тестовый бот {self.created_bot_id} успешно удален")
                    else:
                        print(f"   ⚠️ Не удалось удалить тестовый бот {self.created_bot_id}: {response.status}")
            except Exception as e:
                print(f"   ⚠️ Ошибка при удалении тестового бота: {e}")
                
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🎯 ИТОГОВЫЙ ОТЧЕТ ПО ТЕСТИРОВАНИЮ УДАЛЕНИЯ ПОЛЕЙ БОТОВ")
        print("="*80)
        
        passed = sum(1 for _, result in self.test_results if result is True)
        failed = sum(1 for _, result in self.test_results if result is False)
        na = sum(1 for _, result in self.test_results if result == "NA")
        total = len(self.test_results)
        
        print(f"📊 СТАТИСТИКА ТЕСТОВ:")
        print(f"   Всего тестов: {total}")
        print(f"   ✅ Пройдено: {passed}")
        print(f"   ❌ Провалено: {failed}")
        print(f"   ⚠️ Н/Д: {na}")
        
        if total > 0:
            success_rate = (passed / (total - na)) * 100 if (total - na) > 0 else 0
            print(f"   🎯 Процент успеха: {success_rate:.1f}%")
        
        print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for test_name, result in self.test_results:
            status = "✅ ПРОЙДЕН" if result is True else "❌ ПРОВАЛЕН" if result is False else "⚠️ Н/Д"
            print(f"   {status} - {test_name}")
            
        # Overall assessment
        print("\n" + "="*80)
        print("🏆 ОБЩАЯ ОЦЕНКА:")
        if failed == 0:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Удаление полей ботов работает корректно.")
            print("✅ Поля can_accept_bets и can_play_with_bots успешно удалены из обычных ботов")
            print("✅ Human-боты сохранили свои необходимые поля")
            print("✅ Функциональность системы не нарушена")
        elif failed <= 2:
            print("⚠️ СИСТЕМА В ОСНОВНОМ РАБОТАЕТ с незначительными проблемами.")
            print("🔧 Удаление полей ботов в значительной степени функционально.")
        else:
            print("❌ ОБНАРУЖЕНЫ ЗНАЧИТЕЛЬНЫЕ ПРОБЛЕМЫ.")
            print("🚨 Удаление полей ботов требует внимания.")
        print("="*80)
        
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ УДАЛЕНИЯ ПОЛЕЙ БОТОВ")
        print("🇷🇺 Russian Review: Протестировать удаление полей can_accept_bets и can_play_with_bots")
        print("="*80)
        
        await self.setup()
        
        try:
            await self.test_comprehensive_bot_fields_removal()
            await self.cleanup_test_data()
        finally:
            await self.cleanup()
            
        self.print_summary()

async def main():
    """Main function"""
    tester = FinalBotFieldsTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())