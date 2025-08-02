#!/usr/bin/env python3
"""
Human-Bot Toggle Endpoints Testing
Focus: Testing Human-bot "Играть друг с другом" и "Играть с игроками" toggle functionality
Russian Review Requirements: Test toggle endpoints and individual settings persistence
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
from datetime import datetime

# Configuration
BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class HumanBotToggleTestRunner:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.created_bots = []  # Track created bots for cleanup
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def authenticate_admin(self) -> bool:
        """Authenticate as admin user"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_result("Admin Authentication", True, f"Successfully authenticated as {ADMIN_USER['email']}")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}

    def create_test_human_bot(self, name_suffix: str = None, max_concurrent_games: int = 1) -> Optional[str]:
        """Create a test Human-bot for testing"""
        try:
            if not name_suffix:
                name_suffix = str(int(time.time()))
            
            bot_data = {
                "name": f"ToggleTestBot_{name_suffix}",
                "character": "BALANCED",
                "gender": "male",
                "min_bet": 5.0,
                "max_bet": 50.0,
                "bet_limit": 12,
                "bet_limit_amount": 300.0,
                "win_percentage": 40.0,
                "loss_percentage": 40.0,
                "draw_percentage": 20.0,
                "min_delay": 30,
                "max_delay": 120,
                "use_commit_reveal": True,
                "logging_level": "INFO",
                "can_play_with_other_bots": True,
                "can_play_with_players": True,
                "bot_min_delay_seconds": 30,
                "bot_max_delay_seconds": 2000,
                "player_min_delay_seconds": 30,
                "player_max_delay_seconds": 2000,
                "max_concurrent_games": max_concurrent_games
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=bot_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                bot_id = data.get("id")
                if bot_id:
                    self.created_bots.append(bot_id)
                    self.log_result(
                        f"Create Test Human-bot ({name_suffix})", 
                        True, 
                        f"Created bot with ID: {bot_id}, max_concurrent_games: {max_concurrent_games}"
                    )
                    return bot_id
                else:
                    self.log_result(f"Create Test Human-bot ({name_suffix})", False, "No bot ID in response", data)
                    return None
            else:
                self.log_result(f"Create Test Human-bot ({name_suffix})", False, f"Status {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result(f"Create Test Human-bot ({name_suffix})", False, f"Exception: {str(e)}")
            return None

    def test_toggle_auto_play_endpoint(self, bot_id: str) -> bool:
        """Test POST /admin/human-bots/{bot_id}/toggle-auto-play endpoint"""
        try:
            # Test toggling can_play_with_other_bots to False
            toggle_data = {"can_play_with_other_bots": False}
            response = requests.post(
                f"{BASE_URL}/admin/human-bots/{bot_id}/toggle-auto-play",
                json=toggle_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                message = data.get("message", "")
                
                if success:
                    self.log_result(
                        "Toggle Auto-Play Endpoint (False)", 
                        True, 
                        f"Successfully toggled can_play_with_other_bots to False. Message: {message}"
                    )
                    
                    # Test toggling back to True
                    toggle_data = {"can_play_with_other_bots": True}
                    response = requests.post(
                        f"{BASE_URL}/admin/human-bots/{bot_id}/toggle-auto-play",
                        json=toggle_data,
                        headers=self.get_auth_headers()
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        success = data.get("success", False)
                        message = data.get("message", "")
                        
                        if success:
                            self.log_result(
                                "Toggle Auto-Play Endpoint (True)", 
                                True, 
                                f"Successfully toggled can_play_with_other_bots to True. Message: {message}"
                            )
                            return True
                        else:
                            self.log_result("Toggle Auto-Play Endpoint (True)", False, f"Success=False: {message}", data)
                            return False
                    else:
                        self.log_result("Toggle Auto-Play Endpoint (True)", False, f"Status {response.status_code}", response.text)
                        return False
                else:
                    self.log_result("Toggle Auto-Play Endpoint (False)", False, f"Success=False: {message}", data)
                    return False
            else:
                self.log_result("Toggle Auto-Play Endpoint (False)", False, f"Status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Toggle Auto-Play Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_toggle_play_with_players_endpoint(self, bot_id: str) -> bool:
        """Test POST /admin/human-bots/{bot_id}/toggle-play-with-players endpoint"""
        try:
            # Test toggling can_play_with_players to False
            toggle_data = {"can_play_with_players": False}
            response = requests.post(
                f"{BASE_URL}/admin/human-bots/{bot_id}/toggle-play-with-players",
                json=toggle_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                message = data.get("message", "")
                
                if success:
                    self.log_result(
                        "Toggle Play With Players Endpoint (False)", 
                        True, 
                        f"Successfully toggled can_play_with_players to False. Message: {message}"
                    )
                    
                    # Test toggling back to True
                    toggle_data = {"can_play_with_players": True}
                    response = requests.post(
                        f"{BASE_URL}/admin/human-bots/{bot_id}/toggle-play-with-players",
                        json=toggle_data,
                        headers=self.get_auth_headers()
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        success = data.get("success", False)
                        message = data.get("message", "")
                        
                        if success:
                            self.log_result(
                                "Toggle Play With Players Endpoint (True)", 
                                True, 
                                f"Successfully toggled can_play_with_players to True. Message: {message}"
                            )
                            return True
                        else:
                            self.log_result("Toggle Play With Players Endpoint (True)", False, f"Success=False: {message}", data)
                            return False
                    else:
                        self.log_result("Toggle Play With Players Endpoint (True)", False, f"Status {response.status_code}", response.text)
                        return False
                else:
                    self.log_result("Toggle Play With Players Endpoint (False)", False, f"Success=False: {message}", data)
                    return False
            else:
                self.log_result("Toggle Play With Players Endpoint (False)", False, f"Status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Toggle Play With Players Endpoint", False, f"Exception: {str(e)}")
            return False

    def get_human_bot_details(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Get Human-bot details to verify settings persistence"""
        try:
            response = requests.get(
                f"{BASE_URL}/admin/human-bots/{bot_id}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Get Human-bot Details", True, f"Successfully retrieved bot details for {bot_id}")
                return data
            elif response.status_code == 405:
                # Try getting from list endpoint instead
                response = requests.get(
                    f"{BASE_URL}/admin/human-bots?page=1&limit=100",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bots = data.get("bots", [])
                    for bot in bots:
                        if bot.get("id") == bot_id:
                            self.log_result("Get Human-bot Details (via list)", True, f"Found bot in list: {bot_id}")
                            return bot
                    
                    self.log_result("Get Human-bot Details", False, f"Bot {bot_id} not found in list")
                    return None
                else:
                    self.log_result("Get Human-bot Details", False, f"List endpoint status {response.status_code}", response.text)
                    return None
            else:
                self.log_result("Get Human-bot Details", False, f"Status {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("Get Human-bot Details", False, f"Exception: {str(e)}")
            return None

    def test_individual_settings_persistence(self, bot_id: str) -> bool:
        """Test that individual settings are properly saved and retrieved"""
        try:
            # Get initial bot details
            initial_details = self.get_human_bot_details(bot_id)
            if not initial_details:
                return False
            
            initial_can_play_bots = initial_details.get("can_play_with_other_bots")
            initial_can_play_players = initial_details.get("can_play_with_players")
            initial_max_concurrent = initial_details.get("max_concurrent_games")
            
            self.log_result(
                "Initial Settings Check", 
                True, 
                f"can_play_with_other_bots: {initial_can_play_bots}, can_play_with_players: {initial_can_play_players}, max_concurrent_games: {initial_max_concurrent}"
            )
            
            # Toggle settings
            toggle_auto_success = self.test_toggle_auto_play_endpoint(bot_id)
            toggle_players_success = self.test_toggle_play_with_players_endpoint(bot_id)
            
            if not (toggle_auto_success and toggle_players_success):
                return False
            
            # Get updated bot details
            updated_details = self.get_human_bot_details(bot_id)
            if not updated_details:
                return False
            
            updated_can_play_bots = updated_details.get("can_play_with_other_bots")
            updated_can_play_players = updated_details.get("can_play_with_players")
            updated_max_concurrent = updated_details.get("max_concurrent_games")
            
            # Verify settings were persisted (should be True after toggling back)
            settings_correct = (
                updated_can_play_bots == True and
                updated_can_play_players == True and
                updated_max_concurrent == initial_max_concurrent
            )
            
            if settings_correct:
                self.log_result(
                    "Settings Persistence Verification", 
                    True, 
                    f"Settings correctly persisted: can_play_with_other_bots: {updated_can_play_bots}, can_play_with_players: {updated_can_play_players}, max_concurrent_games: {updated_max_concurrent}"
                )
                return True
            else:
                self.log_result(
                    "Settings Persistence Verification", 
                    False, 
                    f"Settings not correctly persisted: can_play_with_other_bots: {updated_can_play_bots}, can_play_with_players: {updated_can_play_players}, max_concurrent_games: {updated_max_concurrent}"
                )
                return False
                
        except Exception as e:
            self.log_result("Individual Settings Persistence", False, f"Exception: {str(e)}")
            return False

    def test_max_concurrent_games_fix(self) -> bool:
        """Test that individual max_concurrent_games setting is used instead of global setting"""
        try:
            # Create bot with max_concurrent_games=1
            bot_id_1 = self.create_test_human_bot("concurrent_1", max_concurrent_games=1)
            if not bot_id_1:
                return False
            
            # Create bot with max_concurrent_games=3
            bot_id_3 = self.create_test_human_bot("concurrent_3", max_concurrent_games=3)
            if not bot_id_3:
                return False
            
            # Verify both bots have their individual settings
            bot_1_details = self.get_human_bot_details(bot_id_1)
            bot_3_details = self.get_human_bot_details(bot_id_3)
            
            if not (bot_1_details and bot_3_details):
                return False
            
            bot_1_max_concurrent = bot_1_details.get("max_concurrent_games")
            bot_3_max_concurrent = bot_3_details.get("max_concurrent_games")
            
            if bot_1_max_concurrent == 1 and bot_3_max_concurrent == 3:
                self.log_result(
                    "Max Concurrent Games Individual Settings", 
                    True, 
                    f"Bot 1 has max_concurrent_games: {bot_1_max_concurrent}, Bot 3 has max_concurrent_games: {bot_3_max_concurrent}"
                )
                return True
            else:
                self.log_result(
                    "Max Concurrent Games Individual Settings", 
                    False, 
                    f"Expected Bot 1: 1, Bot 3: 3. Got Bot 1: {bot_1_max_concurrent}, Bot 3: {bot_3_max_concurrent}"
                )
                return False
                
        except Exception as e:
            self.log_result("Max Concurrent Games Fix", False, f"Exception: {str(e)}")
            return False

    def test_update_individual_settings(self, bot_id: str) -> bool:
        """Test updating individual settings via PUT endpoint"""
        try:
            update_data = {
                "can_play_with_other_bots": False,
                "can_play_with_players": False,
                "max_concurrent_games": 2,
                "bot_min_delay_seconds": 60,
                "bot_max_delay_seconds": 1800,
                "player_min_delay_seconds": 45,
                "player_max_delay_seconds": 1500
            }
            
            response = requests.put(
                f"{BASE_URL}/admin/human-bots/{bot_id}",
                json=update_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify updated values are returned
                updated_can_play_bots = data.get("can_play_with_other_bots")
                updated_can_play_players = data.get("can_play_with_players")
                updated_max_concurrent = data.get("max_concurrent_games")
                updated_bot_min_delay = data.get("bot_min_delay_seconds")
                updated_bot_max_delay = data.get("bot_max_delay_seconds")
                updated_player_min_delay = data.get("player_min_delay_seconds")
                updated_player_max_delay = data.get("player_max_delay_seconds")
                
                all_correct = (
                    updated_can_play_bots == False and
                    updated_can_play_players == False and
                    updated_max_concurrent == 2 and
                    updated_bot_min_delay == 60 and
                    updated_bot_max_delay == 1800 and
                    updated_player_min_delay == 45 and
                    updated_player_max_delay == 1500
                )
                
                if all_correct:
                    self.log_result(
                        "Update Individual Settings", 
                        True, 
                        f"All individual settings updated correctly: can_play_bots={updated_can_play_bots}, can_play_players={updated_can_play_players}, max_concurrent={updated_max_concurrent}, delays=({updated_bot_min_delay}-{updated_bot_max_delay}, {updated_player_min_delay}-{updated_player_max_delay})"
                    )
                    return True
                else:
                    self.log_result(
                        "Update Individual Settings", 
                        False, 
                        f"Some settings not updated correctly: can_play_bots={updated_can_play_bots}, can_play_players={updated_can_play_players}, max_concurrent={updated_max_concurrent}, delays=({updated_bot_min_delay}-{updated_bot_max_delay}, {updated_player_min_delay}-{updated_player_max_delay})"
                    )
                    return False
            else:
                self.log_result("Update Individual Settings", False, f"Status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Update Individual Settings", False, f"Exception: {str(e)}")
            return False

    def cleanup_test_bots(self):
        """Clean up created test bots"""
        for bot_id in self.created_bots:
            try:
                response = requests.delete(
                    f"{BASE_URL}/admin/human-bots/{bot_id}",
                    headers=self.get_auth_headers()
                )
                if response.status_code == 200:
                    self.log_result(f"Cleanup Bot {bot_id}", True, "Successfully deleted test bot")
                else:
                    self.log_result(f"Cleanup Bot {bot_id}", False, f"Status {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Bot {bot_id}", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all Human-bot toggle tests"""
        print("🚀 STARTING HUMAN-BOT TOGGLE ENDPOINTS TESTING")
        print("=" * 80)
        print()
        
        # Authenticate
        if not self.authenticate_admin():
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed with tests.")
            return
        
        # Create test bot for main testing
        main_bot_id = self.create_test_human_bot("main")
        if not main_bot_id:
            print("❌ CRITICAL: Failed to create test bot. Cannot proceed with tests.")
            return
        
        # Test 1: Toggle Auto-Play Endpoint
        print("📋 TEST 1: Toggle Auto-Play Endpoint")
        self.test_toggle_auto_play_endpoint(main_bot_id)
        
        # Test 2: Toggle Play With Players Endpoint
        print("📋 TEST 2: Toggle Play With Players Endpoint")
        self.test_toggle_play_with_players_endpoint(main_bot_id)
        
        # Test 3: Individual Settings Persistence
        print("📋 TEST 3: Individual Settings Persistence")
        self.test_individual_settings_persistence(main_bot_id)
        
        # Test 4: Max Concurrent Games Fix
        print("📋 TEST 4: Max Concurrent Games Individual Settings")
        self.test_max_concurrent_games_fix()
        
        # Test 5: Update Individual Settings
        print("📋 TEST 5: Update Individual Settings via PUT")
        self.test_update_individual_settings(main_bot_id)
        
        # Cleanup
        print("📋 CLEANUP: Removing test bots")
        self.cleanup_test_bots()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 HUMAN-BOT TOGGLE ENDPOINTS TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        # Check if toggle endpoints work
        toggle_auto_working = any(r["success"] and "Toggle Auto-Play Endpoint" in r["test"] for r in self.test_results)
        toggle_players_working = any(r["success"] and "Toggle Play With Players Endpoint" in r["test"] for r in self.test_results)
        
        if toggle_auto_working and toggle_players_working:
            print("   ✅ Toggle endpoints are working correctly")
        else:
            print("   ❌ Toggle endpoints have issues")
        
        # Check if individual settings work
        settings_working = any(r["success"] and "Individual Settings" in r["test"] for r in self.test_results)
        if settings_working:
            print("   ✅ Individual settings persistence is working")
        else:
            print("   ❌ Individual settings persistence has issues")
        
        # Check if max_concurrent_games fix works
        concurrent_fix_working = any(r["success"] and "Max Concurrent Games" in r["test"] for r in self.test_results)
        if concurrent_fix_working:
            print("   ✅ Individual max_concurrent_games setting is working")
        else:
            print("   ❌ Individual max_concurrent_games setting has issues")
        
        print()
        
        if success_rate >= 80:
            print("🎉 OVERALL RESULT: HUMAN-BOT TOGGLE FUNCTIONALITY IS WORKING!")
        elif success_rate >= 60:
            print("⚠️  OVERALL RESULT: HUMAN-BOT TOGGLE FUNCTIONALITY HAS MINOR ISSUES")
        else:
            print("❌ OVERALL RESULT: HUMAN-BOT TOGGLE FUNCTIONALITY HAS MAJOR ISSUES")
        
        print("=" * 80)

def main():
    """Main function to run the tests"""
    runner = HumanBotToggleTestRunner()
    runner.run_all_tests()

if __name__ == "__main__":
    main()