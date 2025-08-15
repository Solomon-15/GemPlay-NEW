import asyncio
import aiohttp
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000/api"

# Test users credentials
USER1 = {"username": "testuser1@example.com", "password": "testpass123"}
USER2 = {"username": "testuser2@example.com", "password": "testpass123"}

class TestReservationSystem:
    def __init__(self):
        self.session = None
        self.user1_token = None
        self.user2_token = None
        self.user1_id = None
        self.user2_id = None
        
    async def setup(self):
        """Initialize test session and create test users"""
        self.session = aiohttp.ClientSession()
        
        # Register test users
        print("📝 Registering test users...")
        try:
            # Register user 1
            resp = await self.session.post(f"{BASE_URL}/auth/register", json={
                "email": USER1["username"],
                "password": USER1["password"],
                "username": "TestUser1"
            })
            if resp.status == 200:
                data = await resp.json()
                self.user1_token = data["access_token"]
                self.user1_id = data["user"]["id"]
                print(f"✅ User 1 registered: {self.user1_id}")
            else:
                # Try login if already exists
                resp = await self.session.post(f"{BASE_URL}/auth/login", json=USER1)
                data = await resp.json()
                self.user1_token = data["access_token"]
                self.user1_id = data["user"]["id"]
                print(f"✅ User 1 logged in: {self.user1_id}")
                
            # Register user 2
            resp = await self.session.post(f"{BASE_URL}/auth/register", json={
                "email": USER2["username"],
                "password": USER2["password"],
                "username": "TestUser2"
            })
            if resp.status == 200:
                data = await resp.json()
                self.user2_token = data["access_token"]
                self.user2_id = data["user"]["id"]
                print(f"✅ User 2 registered: {self.user2_id}")
            else:
                # Try login if already exists
                resp = await self.session.post(f"{BASE_URL}/auth/login", json=USER2)
                data = await resp.json()
                self.user2_token = data["access_token"]
                self.user2_id = data["user"]["id"]
                print(f"✅ User 2 logged in: {self.user2_id}")
                
        except Exception as e:
            print(f"❌ Error in setup: {e}")
            
    async def cleanup(self):
        """Close session"""
        if self.session:
            await self.session.close()
            
    async def give_user_gems(self, user_token, amount=100):
        """Give test user some gems"""
        try:
            # First get user's gem info
            headers = {"Authorization": f"Bearer {user_token}"}
            
            # Give user virtual balance for testing
            resp = await self.session.post(
                f"{BASE_URL}/admin/users/add-balance",
                headers=headers,
                json={"user_id": self.user1_id, "amount": amount}
            )
            
            # Alternative: directly manipulate test data if admin endpoint not available
            print(f"💎 Attempting to give user ${amount} worth of gems...")
            
        except Exception as e:
            print(f"⚠️  Could not add gems (may need admin access): {e}")
            
    async def test_reservation_flow(self):
        """Test the complete reservation flow"""
        print("\n🧪 TEST 1: Basic Reservation Flow")
        print("="*50)
        
        try:
            # User 1 creates a bet
            print("\n1️⃣ User 1 creating a bet...")
            headers1 = {"Authorization": f"Bearer {self.user1_token}"}
            
            create_resp = await self.session.post(
                f"{BASE_URL}/games/create",
                headers=headers1,
                json={
                    "bet_amount": 10,
                    "gems": {"Ruby": 2}  # Assuming Ruby is worth $5 each
                }
            )
            
            if create_resp.status != 200:
                error_text = await create_resp.text()
                print(f"❌ Failed to create game: {error_text}")
                return
                
            game_data = await create_resp.json()
            game_id = game_data["id"]
            print(f"✅ Game created with ID: {game_id}")
            
            # User 2 tries to reserve the game
            print("\n2️⃣ User 2 attempting to reserve the game...")
            headers2 = {"Authorization": f"Bearer {self.user2_token}"}
            
            reserve_resp = await self.session.post(
                f"{BASE_URL}/games/{game_id}/reserve",
                headers=headers2
            )
            
            if reserve_resp.status == 200:
                reserve_data = await reserve_resp.json()
                print(f"✅ Game reserved successfully!")
                print(f"   Reserved until: {reserve_data.get('reserved_until')}")
            else:
                error_data = await reserve_resp.json()
                print(f"❌ Reservation failed: {error_data.get('detail')}")
                
            # Check if game appears in available games
            print("\n3️⃣ Checking available games lists...")
            
            # Check for User 1 (creator)
            avail_resp1 = await self.session.get(f"{BASE_URL}/games/available", headers=headers1)
            avail_games1 = await avail_resp1.json()
            game_visible_to_user1 = any(g.get("game_id") == game_id for g in avail_games1)
            print(f"   Game visible to User 1 (creator): {game_visible_to_user1} ❌" if game_visible_to_user1 else "   Game hidden from User 1 (creator): ✅")
            
            # Check for User 2 (reserver)
            avail_resp2 = await self.session.get(f"{BASE_URL}/games/available", headers=headers2)
            avail_games2 = await avail_resp2.json()
            game_visible_to_user2 = any(g.get("game_id") == game_id for g in avail_games2)
            print(f"   Game visible to User 2 (reserver): {game_visible_to_user2} ✅" if game_visible_to_user2 else "   Game hidden from User 2 (reserver): ❌")
            
            # Test unreserve
            print("\n4️⃣ User 2 unreserving the game...")
            unreserve_resp = await self.session.post(
                f"{BASE_URL}/games/{game_id}/unreserve",
                headers=headers2
            )
            
            if unreserve_resp.status == 200:
                print("✅ Game unreserved successfully!")
            else:
                print("❌ Failed to unreserve game")
                
            # Check if game is visible again
            print("\n5️⃣ Checking if game is visible after unreserve...")
            avail_resp3 = await self.session.get(f"{BASE_URL}/games/available", headers=headers2)
            avail_games3 = await avail_resp3.json()
            game_visible_after = any(g.get("game_id") == game_id for g in avail_games3)
            print(f"   Game visible after unreserve: {game_visible_after} ✅" if game_visible_after else "   Game still hidden: ❌")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            
    async def test_insufficient_gems(self):
        """Test reservation with insufficient gems"""
        print("\n🧪 TEST 2: Insufficient Gems Check")
        print("="*50)
        
        try:
            # User 1 creates a high-value bet
            print("\n1️⃣ User 1 creating a high-value bet ($1000)...")
            headers1 = {"Authorization": f"Bearer {self.user1_token}"}
            
            create_resp = await self.session.post(
                f"{BASE_URL}/games/create",
                headers=headers1,
                json={
                    "bet_amount": 1000,
                    "gems": {"Ruby": 200}  # Assuming Ruby is worth $5 each
                }
            )
            
            if create_resp.status != 200:
                # User 1 might not have enough gems either
                print("⚠️  User 1 couldn't create high-value bet (expected)")
                return
                
            game_data = await create_resp.json()
            game_id = game_data["id"]
            print(f"✅ High-value game created: {game_id}")
            
            # User 2 tries to reserve without enough gems
            print("\n2️⃣ User 2 trying to reserve without enough gems...")
            headers2 = {"Authorization": f"Bearer {self.user2_token}"}
            
            reserve_resp = await self.session.post(
                f"{BASE_URL}/games/{game_id}/reserve",
                headers=headers2
            )
            
            if reserve_resp.status == 400:
                error_data = await reserve_resp.json()
                print(f"✅ Correctly rejected: {error_data.get('detail')}")
            else:
                print("❌ Reservation should have failed due to insufficient gems!")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            
    async def test_concurrent_reservation(self):
        """Test that only one user can reserve a game"""
        print("\n🧪 TEST 3: Concurrent Reservation Prevention")
        print("="*50)
        
        try:
            # Create a third test user
            print("\n0️⃣ Creating third test user...")
            resp = await self.session.post(f"{BASE_URL}/auth/register", json={
                "email": "testuser3@example.com",
                "password": "testpass123",
                "username": "TestUser3"
            })
            
            if resp.status == 200:
                data = await resp.json()
                user3_token = data["access_token"]
            else:
                # Try login
                resp = await self.session.post(f"{BASE_URL}/auth/login", json={
                    "username": "testuser3@example.com",
                    "password": "testpass123"
                })
                data = await resp.json()
                user3_token = data["access_token"]
            
            # User 1 creates a bet
            print("\n1️⃣ User 1 creating a bet...")
            headers1 = {"Authorization": f"Bearer {self.user1_token}"}
            
            create_resp = await self.session.post(
                f"{BASE_URL}/games/create",
                headers=headers1,
                json={
                    "bet_amount": 10,
                    "gems": {"Ruby": 2}
                }
            )
            
            game_data = await create_resp.json()
            game_id = game_data["id"]
            print(f"✅ Game created: {game_id}")
            
            # User 2 reserves the game
            print("\n2️⃣ User 2 reserving the game...")
            headers2 = {"Authorization": f"Bearer {self.user2_token}"}
            
            reserve_resp = await self.session.post(
                f"{BASE_URL}/games/{game_id}/reserve",
                headers=headers2
            )
            
            if reserve_resp.status == 200:
                print("✅ User 2 reserved the game")
            else:
                print("❌ User 2 failed to reserve")
                return
                
            # User 3 tries to reserve the same game
            print("\n3️⃣ User 3 trying to reserve the already reserved game...")
            headers3 = {"Authorization": f"Bearer {user3_token}"}
            
            reserve_resp3 = await self.session.post(
                f"{BASE_URL}/games/{game_id}/reserve",
                headers=headers3
            )
            
            if reserve_resp3.status == 400:
                error_data = await reserve_resp3.json()
                print(f"✅ Correctly prevented: {error_data.get('detail')}")
            else:
                print("❌ User 3 should not be able to reserve an already reserved game!")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            
    async def test_auto_unreserve(self):
        """Test automatic unreserve after timeout"""
        print("\n🧪 TEST 4: Automatic Unreserve After Timeout")
        print("="*50)
        print("⚠️  This test takes ~70 seconds to complete...")
        
        try:
            # User 1 creates a bet
            print("\n1️⃣ User 1 creating a bet...")
            headers1 = {"Authorization": f"Bearer {self.user1_token}"}
            
            create_resp = await self.session.post(
                f"{BASE_URL}/games/create",
                headers=headers1,
                json={
                    "bet_amount": 10,
                    "gems": {"Ruby": 2}
                }
            )
            
            game_data = await create_resp.json()
            game_id = game_data["id"]
            print(f"✅ Game created: {game_id}")
            
            # User 2 reserves the game
            print("\n2️⃣ User 2 reserving the game...")
            headers2 = {"Authorization": f"Bearer {self.user2_token}"}
            
            reserve_resp = await self.session.post(
                f"{BASE_URL}/games/{game_id}/reserve",
                headers=headers2
            )
            
            if reserve_resp.status == 200:
                reserve_data = await reserve_resp.json()
                print(f"✅ Game reserved until: {reserve_data.get('reserved_until')}")
            else:
                print("❌ Failed to reserve")
                return
                
            # Wait for 65 seconds (reservation expires after 60)
            print("\n⏳ Waiting 65 seconds for reservation to expire...")
            for i in range(13):
                print(f"   {65 - i*5} seconds remaining...", end='\r')
                await asyncio.sleep(5)
            print()
            
            # Check if game is visible to others now
            print("\n3️⃣ Checking if game is visible to User 3 after timeout...")
            
            # Create/login user 3
            resp = await self.session.post(f"{BASE_URL}/auth/login", json={
                "username": "testuser3@example.com",
                "password": "testpass123"
            })
            data = await resp.json()
            user3_token = data["access_token"]
            headers3 = {"Authorization": f"Bearer {user3_token}"}
            
            avail_resp = await self.session.get(f"{BASE_URL}/games/available", headers=headers3)
            avail_games = await avail_resp.json()
            game_visible = any(g.get("game_id") == game_id for g in avail_games)
            
            if game_visible:
                print("✅ Game is now visible after timeout!")
            else:
                print("❌ Game should be visible after reservation timeout")
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting Reservation System Tests")
    print("="*50)
    
    tester = TestReservationSystem()
    
    try:
        await tester.setup()
        
        # Run tests
        await tester.test_reservation_flow()
        await tester.test_insufficient_gems()
        await tester.test_concurrent_reservation()
        
        # Optional: Run timeout test (takes 65+ seconds)
        # await tester.test_auto_unreserve()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())