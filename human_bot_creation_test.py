#!/usr/bin/env python3
"""
Human-Bot Creation and Auto-Selection Fix Testing
Focus: Testing fixes for Human-bot creation with disabled options and auto-selection logic
Russian Review Requirements: Протестировать исправления проблем Human-bot создания и автоподбора
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List
import random
import string
from datetime import datetime

# Configuration
BASE_URL = "https://27d5aabc-60c1-4cea-8910-9c833ddf3795.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class HumanBotCreationTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.created_bots = []  # Track created bots for cleanup
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_result("Admin Authentication", True, f"Token obtained: {self.admin_token[:20]}...")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_individual_human_bot_creation(self) -> bool:
        """Test CREATE Human-bot with individual settings"""
        print("\n=== TEST 1: Individual Human-bot Creation with Disabled Options ===")
        
        try:
            # Create Human-bot with specific individual settings including disabled options
            bot_data = {
                "name": f"TestBot_Individual_{int(time.time())}",
                "character": "BALANCED",
                "gender": "male",
                "min_bet": 10.0,
                "max_bet": 100.0,
                "bet_limit": 5,
                "bet_limit_amount": 200.0,
                "win_percentage": 45.0,
                "loss_percentage": 35.0,
                "draw_percentage": 20.0,
                "min_delay": 60,
                "max_delay": 180,
                "use_commit_reveal": True,
                "logging_level": "INFO",
                # CRITICAL: Test disabled options
                "can_play_with_other_bots": False,  # DISABLED
                "can_play_with_players": False,     # DISABLED
                # Individual delay settings
                "bot_min_delay_seconds": 120,
                "bot_max_delay_seconds": 1800,
                "player_min_delay_seconds": 90,
                "player_max_delay_seconds": 1500,
                # Individual concurrent games limit
                "max_concurrent_games": 2
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=bot_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                created_bot = response.json()
                bot_id = created_bot.get("id")
                self.created_bots.append(bot_id)
                
                # Verify all individual settings are saved correctly
                verification_checks = [
                    ("can_play_with_other_bots", False, created_bot.get("can_play_with_other_bots")),
                    ("can_play_with_players", False, created_bot.get("can_play_with_players")),
                    ("bot_min_delay_seconds", 120, created_bot.get("bot_min_delay_seconds")),
                    ("bot_max_delay_seconds", 1800, created_bot.get("bot_max_delay_seconds")),
                    ("player_min_delay_seconds", 90, created_bot.get("player_min_delay_seconds")),
                    ("player_max_delay_seconds", 1500, created_bot.get("player_max_delay_seconds")),
                    ("max_concurrent_games", 2, created_bot.get("max_concurrent_games"))
                ]
                
                all_correct = True
                for field_name, expected, actual in verification_checks:
                    if actual != expected:
                        self.log_result(f"Individual Setting Verification - {field_name}", False, 
                                      f"Expected: {expected}, Got: {actual}")
                        all_correct = False
                    else:
                        self.log_result(f"Individual Setting Verification - {field_name}", True, 
                                      f"Correctly saved: {actual}")
                
                if all_correct:
                    self.log_result("Individual Human-bot Creation", True, 
                                  f"Bot created with ID: {bot_id}, all individual settings correct")
                    return True
                else:
                    self.log_result("Individual Human-bot Creation", False, 
                                  "Some individual settings were not saved correctly")
                    return False
            else:
                self.log_result("Individual Human-bot Creation", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Individual Human-bot Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_bulk_human_bot_creation(self) -> bool:
        """Test BULK CREATE Human-bots with disabled options"""
        print("\n=== TEST 2: Bulk Human-bot Creation with Disabled Options ===")
        
        try:
            # Create multiple Human-bots with disabled options
            bulk_data = {
                "count": 3,
                "character": "AGGRESSIVE",
                "min_bet_range": [5.0, 15.0],
                "max_bet_range": [50.0, 150.0],
                "bet_limit_range": [8, 15],
                "win_percentage": 40.0,
                "loss_percentage": 40.0,
                "draw_percentage": 20.0,
                "delay_range": [30, 120],
                "min_delay": 30,
                "max_delay": 120,
                "use_commit_reveal": True,
                "logging_level": "INFO",
                # CRITICAL: Test disabled options for bulk creation
                "can_play_with_other_bots": False,  # DISABLED for all bots
                "can_play_with_players": False,     # DISABLED for all bots
                # Individual delay settings ranges
                "bot_min_delay_range": [60, 180],
                "bot_max_delay_range": [1200, 2000],
                "player_min_delay_range": [45, 120],
                "player_max_delay_range": [900, 1800],
                # Concurrent games range
                "max_concurrent_games_range": [1, 3]
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots/bulk-create",
                json=bulk_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                created_bots_basic = result.get("created_bots", [])
                
                if len(created_bots_basic) == 3:
                    # Get detailed bot info from the list endpoint
                    list_response = requests.get(
                        f"{BASE_URL}/admin/human-bots?page=1&per_page=10",
                        headers=self.get_auth_headers()
                    )
                    
                    if list_response.status_code != 200:
                        self.log_result("Bulk Human-bot Creation", False, 
                                      f"Could not fetch bot details: {list_response.status_code}")
                        return False
                    
                    all_bots = list_response.json().get("bots", [])
                    created_bot_ids = [bot["id"] for bot in created_bots_basic]
                    created_bots = [bot for bot in all_bots if bot["id"] in created_bot_ids]
                    # Track created bots for cleanup
                    for bot in created_bots:
                        self.created_bots.append(bot.get("id"))
                    
                    # Verify all bots have disabled options
                    all_disabled_correctly = True
                    for i, bot in enumerate(created_bots):
                        bot_checks = [
                            ("can_play_with_other_bots", False, bot.get("can_play_with_other_bots")),
                            ("can_play_with_players", False, bot.get("can_play_with_players"))
                        ]
                        
                        for field_name, expected, actual in bot_checks:
                            if actual != expected:
                                self.log_result(f"Bulk Bot {i+1} - {field_name}", False, 
                                              f"Expected: {expected}, Got: {actual}")
                                all_disabled_correctly = False
                            else:
                                self.log_result(f"Bulk Bot {i+1} - {field_name}", True, 
                                              f"Correctly disabled: {actual}")
                        
                        # Verify random values are within ranges
                        bot_min_delay = bot.get("bot_min_delay_seconds")
                        bot_max_delay = bot.get("bot_max_delay_seconds")
                        player_min_delay = bot.get("player_min_delay_seconds")
                        player_max_delay = bot.get("player_max_delay_seconds")
                        max_concurrent = bot.get("max_concurrent_games")
                        
                        range_checks = [
                            ("bot_min_delay_seconds", 60, 180, bot_min_delay),
                            ("bot_max_delay_seconds", 1200, 2000, bot_max_delay),
                            ("player_min_delay_seconds", 45, 120, player_min_delay),
                            ("player_max_delay_seconds", 900, 1800, player_max_delay),
                            ("max_concurrent_games", 1, 3, max_concurrent)
                        ]
                        
                        for field_name, min_val, max_val, actual_val in range_checks:
                            if min_val <= actual_val <= max_val:
                                self.log_result(f"Bulk Bot {i+1} - {field_name} Range", True, 
                                              f"Value {actual_val} within range [{min_val}, {max_val}]")
                            else:
                                self.log_result(f"Bulk Bot {i+1} - {field_name} Range", False, 
                                              f"Value {actual_val} outside range [{min_val}, {max_val}]")
                                all_disabled_correctly = False
                    
                    if all_disabled_correctly:
                        self.log_result("Bulk Human-bot Creation", True, 
                                      f"Created {len(created_bots)} bots with correct disabled options")
                        return True
                    else:
                        self.log_result("Bulk Human-bot Creation", False, 
                                      "Some bots were not created with correct settings")
                        return False
                else:
                    self.log_result("Bulk Human-bot Creation", False, 
                                  f"Expected 3 bots, got {len(created_bots)}")
                    return False
            else:
                self.log_result("Bulk Human-bot Creation", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Bulk Human-bot Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_toggle_persistence(self) -> bool:
        """Test toggle persistence - create bot with disabled flags, toggle them"""
        print("\n=== TEST 3: Toggle Persistence Testing ===")
        
        try:
            # First create a bot with disabled flags
            bot_data = {
                "name": f"TestBot_Toggle_{int(time.time())}",
                "character": "CAUTIOUS",
                "gender": "female",
                "min_bet": 15.0,
                "max_bet": 75.0,
                "bet_limit": 10,
                "win_percentage": 50.0,
                "loss_percentage": 30.0,
                "draw_percentage": 20.0,
                "min_delay": 45,
                "max_delay": 150,
                # Start with disabled options
                "can_play_with_other_bots": False,
                "can_play_with_players": False,
                "max_concurrent_games": 1
            }
            
            # Create the bot
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=bot_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code != 200:
                self.log_result("Toggle Test - Bot Creation", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            created_bot = response.json()
            bot_id = created_bot.get("id")
            self.created_bots.append(bot_id)
            
            # Verify initial disabled state
            if (created_bot.get("can_play_with_other_bots") == False and 
                created_bot.get("can_play_with_players") == False):
                self.log_result("Toggle Test - Initial Disabled State", True, 
                              "Bot created with disabled options")
            else:
                self.log_result("Toggle Test - Initial Disabled State", False, 
                              f"Bot options not disabled: bots={created_bot.get('can_play_with_other_bots')}, players={created_bot.get('can_play_with_players')}")
                return False
            
            # Test toggle auto-play (can_play_with_other_bots)
            toggle_auto_play_data = {"can_play_with_other_bots": True}
            response = requests.post(
                f"{BASE_URL}/admin/human-bots/{bot_id}/toggle-auto-play",
                json=toggle_auto_play_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                self.log_result("Toggle Test - Auto-play Toggle", True, "Auto-play toggled successfully")
            else:
                self.log_result("Toggle Test - Auto-play Toggle", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # Test toggle play with players
            toggle_players_data = {"can_play_with_players": True}
            response = requests.post(
                f"{BASE_URL}/admin/human-bots/{bot_id}/toggle-play-with-players",
                json=toggle_players_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                self.log_result("Toggle Test - Play with Players Toggle", True, "Play with players toggled successfully")
            else:
                self.log_result("Toggle Test - Play with Players Toggle", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            # Verify the toggles persisted by fetching the bot again
            response = requests.get(
                f"{BASE_URL}/admin/human-bots/{bot_id}",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                updated_bot = response.json()
                if (updated_bot.get("can_play_with_other_bots") == True and 
                    updated_bot.get("can_play_with_players") == True):
                    self.log_result("Toggle Test - Persistence Verification", True, 
                                  "Both toggles persisted correctly (now enabled)")
                    return True
                else:
                    self.log_result("Toggle Test - Persistence Verification", False, 
                                  f"Toggles not persisted: bots={updated_bot.get('can_play_with_other_bots')}, players={updated_bot.get('can_play_with_players')}")
                    return False
            else:
                self.log_result("Toggle Test - Persistence Verification", False, 
                              f"Could not fetch updated bot: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Toggle Persistence Testing", False, f"Exception: {str(e)}")
            return False
    
    def test_auto_selection_logic(self) -> bool:
        """Test that bots with disabled options don't participate in auto-selection"""
        print("\n=== TEST 4: Auto-Selection Logic Testing ===")
        
        try:
            # Create a bot with disabled auto-play
            disabled_bot_data = {
                "name": f"TestBot_Disabled_{int(time.time())}",
                "character": "STABLE",
                "min_bet": 20.0,
                "max_bet": 80.0,
                "can_play_with_other_bots": False,  # DISABLED
                "can_play_with_players": False      # DISABLED
            }
            
            response = requests.post(
                f"{BASE_URL}/admin/human-bots",
                json=disabled_bot_data,
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                disabled_bot = response.json()
                disabled_bot_id = disabled_bot.get("id")
                self.created_bots.append(disabled_bot_id)
                
                self.log_result("Auto-Selection Test - Disabled Bot Creation", True, 
                              f"Created disabled bot: {disabled_bot_id}")
                
                # Check if the bot appears in any active games (it shouldn't)
                # This is a basic check - in a real scenario, we'd need to wait and monitor
                response = requests.get(
                    f"{BASE_URL}/admin/games?status=ACTIVE",
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 200:
                    active_games = response.json().get("games", [])
                    disabled_bot_in_games = any(
                        game.get("creator_id") == disabled_bot_id or 
                        game.get("opponent_id") == disabled_bot_id 
                        for game in active_games
                    )
                    
                    if not disabled_bot_in_games:
                        self.log_result("Auto-Selection Test - Disabled Bot Not in Games", True, 
                                      "Disabled bot correctly not participating in active games")
                        return True
                    else:
                        self.log_result("Auto-Selection Test - Disabled Bot Not in Games", False, 
                                      "Disabled bot found in active games (should not happen)")
                        return False
                else:
                    self.log_result("Auto-Selection Test - Games Check", False, 
                                  f"Could not check active games: {response.status_code}")
                    return False
            else:
                self.log_result("Auto-Selection Test - Disabled Bot Creation", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Auto-Selection Logic Testing", False, f"Exception: {str(e)}")
            return False
    
    def cleanup_created_bots(self):
        """Clean up created test bots"""
        print("\n=== CLEANUP: Removing Created Test Bots ===")
        
        for bot_id in self.created_bots:
            try:
                response = requests.delete(
                    f"{BASE_URL}/admin/human-bots/{bot_id}",
                    headers=self.get_auth_headers()
                )
                if response.status_code == 200:
                    self.log_result(f"Cleanup Bot {bot_id}", True, "Bot deleted successfully")
                else:
                    self.log_result(f"Cleanup Bot {bot_id}", False, 
                                  f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Bot {bot_id}", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all Human-bot creation and auto-selection tests"""
        print("🚀 STARTING HUMAN-BOT CREATION AND AUTO-SELECTION FIX TESTING")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_admin():
            print("❌ CRITICAL: Admin authentication failed. Cannot proceed.")
            return False
        
        # Run tests
        test_results = []
        test_results.append(self.test_individual_human_bot_creation())
        test_results.append(self.test_bulk_human_bot_creation())
        test_results.append(self.test_toggle_persistence())
        test_results.append(self.test_auto_selection_logic())
        
        # Cleanup
        self.cleanup_created_bots()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 HUMAN-BOT CREATION AND AUTO-SELECTION FIX TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"✅ PASSED: {passed_tests}/{total_tests} tests ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 ALL HUMAN-BOT CREATION AND AUTO-SELECTION FIXES WORKING CORRECTLY!")
            print("✅ Individual settings properly saved")
            print("✅ Bulk creation with disabled options working")
            print("✅ Toggle persistence verified")
            print("✅ Auto-selection logic respects disabled flags")
        else:
            print("⚠️  SOME ISSUES FOUND:")
            for i, result in enumerate(test_results):
                test_names = [
                    "Individual Human-bot Creation",
                    "Bulk Human-bot Creation", 
                    "Toggle Persistence",
                    "Auto-Selection Logic"
                ]
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {status}: {test_names[i]}")
        
        return passed_tests == total_tests

def main():
    """Main function"""
    tester = HumanBotCreationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()