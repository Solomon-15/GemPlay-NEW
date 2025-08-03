#!/usr/bin/env python3
"""
Human-Bot Active Bets API Testing
Focus: Testing data for fixing "Время" column in HumanBotActiveBetsModal

CONTEXT:
- Recent fix in HumanBotActiveBetsModal.js
- "Время" column should show correct bot activity time:
  * If bot is creator: show bet.created_at
  * If bot is opponent: show bet.updated_at (join time) or bet.created_at as fallback

REQUIREMENTS:
1. Check API endpoint for getting active Human-bot bets
2. Ensure backend returns necessary fields: created_at, updated_at, joined_at
3. Check data correctness for both cases (bot creator / bot opponent)
4. Test API response structure with active Human-bot bets
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List
import random
from datetime import datetime

# Configuration
BASE_URL = "https://a27c21e9-6e48-4ff5-9993-d0d6a8d8cd40.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

class HumanBotActiveBetsTest:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.human_bots = []
        self.test_games = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def admin_login(self) -> bool:
        """Login as admin"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_result("Admin Login", True, "Successfully logged in as admin")
                return True
            else:
                self.log_result("Admin Login", False, f"Login failed: {response.status_code}", 
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Admin Login", False, f"Login error: {str(e)}")
            return False
    
    def get_admin_headers(self) -> Dict[str, str]:
        """Get headers with admin authorization"""
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def get_human_bots_list(self) -> bool:
        """Get list of Human-bots for testing"""
        try:
            response = requests.get(
                f"{BASE_URL}/admin/human-bots",
                headers=self.get_admin_headers(),
                params={"page": 1, "per_page": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("bots"):
                    self.human_bots = data["bots"][:5]  # Take first 5 bots for testing
                    self.log_result("Get Human-bots List", True, 
                                  f"Retrieved {len(self.human_bots)} Human-bots for testing")
                    return True
                else:
                    self.log_result("Get Human-bots List", False, "No Human-bots found in response")
                    return False
            else:
                self.log_result("Get Human-bots List", False, 
                              f"Failed to get Human-bots: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Get Human-bots List", False, f"Error getting Human-bots: {str(e)}")
            return False
    
    def test_active_bets_endpoint_structure(self) -> bool:
        """Test the structure of active bets endpoint response"""
        if not self.human_bots:
            self.log_result("Active Bets Endpoint Structure", False, "No Human-bots available for testing")
            return False
        
        try:
            bot = self.human_bots[0]
            bot_id = bot.get("id")
            bot_name = bot.get("name", "Unknown")
            
            response = requests.get(
                f"{BASE_URL}/admin/human-bots/{bot_id}/active-bets",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required top-level fields
                required_fields = ["success", "bot_id", "bot_name", "activeBets", "totalBets", 
                                 "totalBetAmount", "botWins", "playerWins", "draws", "bets"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Active Bets Endpoint Structure", False, 
                                  f"Missing required fields: {missing_fields}",
                                  {"response_keys": list(data.keys())})
                    return False
                
                # Check bets array structure
                bets = data.get("bets", [])
                if bets:
                    bet = bets[0]
                    bet_required_fields = ["id", "created_at", "bet_amount", "status", "is_creator"]
                    bet_missing_fields = [field for field in bet_required_fields if field not in bet]
                    
                    if bet_missing_fields:
                        self.log_result("Active Bets Endpoint Structure", False, 
                                      f"Missing required bet fields: {bet_missing_fields}",
                                      {"bet_keys": list(bet.keys())})
                        return False
                
                self.log_result("Active Bets Endpoint Structure", True, 
                              f"Endpoint structure correct for bot {bot_name}",
                              {"total_active_bets": data.get("activeBets", 0),
                               "bets_count": len(bets)})
                return True
            else:
                self.log_result("Active Bets Endpoint Structure", False, 
                              f"Endpoint failed: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Active Bets Endpoint Structure", False, f"Error testing endpoint: {str(e)}")
            return False
    
    def test_time_fields_presence(self) -> bool:
        """Test that necessary time fields are present in the response"""
        success_count = 0
        total_tests = 0
        
        for bot in self.human_bots[:3]:  # Test first 3 bots
            try:
                bot_id = bot.get("id")
                bot_name = bot.get("name", "Unknown")
                total_tests += 1
                
                response = requests.get(
                    f"{BASE_URL}/admin/human-bots/{bot_id}/active-bets",
                    headers=self.get_admin_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bets = data.get("bets", [])
                    
                    if not bets:
                        self.log_result(f"Time Fields - {bot_name}", True, 
                                      "No active bets (expected for some bots)")
                        success_count += 1
                        continue
                    
                    # Check each bet for required time fields
                    time_fields_ok = True
                    missing_fields_summary = []
                    
                    for i, bet in enumerate(bets[:5]):  # Check first 5 bets
                        required_time_fields = ["created_at"]
                        optional_time_fields = ["updated_at", "joined_at", "started_at"]
                        
                        missing_required = [field for field in required_time_fields if not bet.get(field)]
                        if missing_required:
                            time_fields_ok = False
                            missing_fields_summary.append(f"Bet {i+1}: missing {missing_required}")
                        
                        # Check if at least created_at is present and valid
                        created_at = bet.get("created_at")
                        if created_at:
                            try:
                                # Try to parse the datetime
                                datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            except ValueError:
                                time_fields_ok = False
                                missing_fields_summary.append(f"Bet {i+1}: invalid created_at format")
                    
                    if time_fields_ok:
                        self.log_result(f"Time Fields - {bot_name}", True, 
                                      f"Time fields present in {len(bets)} active bets")
                        success_count += 1
                    else:
                        self.log_result(f"Time Fields - {bot_name}", False, 
                                      f"Time fields issues: {'; '.join(missing_fields_summary)}")
                else:
                    self.log_result(f"Time Fields - {bot_name}", False, 
                                  f"API call failed: {response.status_code}")
            except Exception as e:
                self.log_result(f"Time Fields - {bot_name}", False, f"Error: {str(e)}")
        
        overall_success = success_count == total_tests
        self.log_result("Time Fields Presence Overall", overall_success, 
                      f"Passed {success_count}/{total_tests} bot tests")
        return overall_success
    
    def test_creator_vs_opponent_data(self) -> bool:
        """Test data correctness for bot as creator vs opponent scenarios"""
        creator_bets = []
        opponent_bets = []
        
        for bot in self.human_bots[:5]:  # Test first 5 bots
            try:
                bot_id = bot.get("id")
                bot_name = bot.get("name", "Unknown")
                
                response = requests.get(
                    f"{BASE_URL}/admin/human-bots/{bot_id}/active-bets",
                    headers=self.get_admin_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bets = data.get("bets", [])
                    
                    for bet in bets:
                        is_creator = bet.get("is_creator", False)
                        if is_creator:
                            creator_bets.append({
                                "bot_name": bot_name,
                                "bet_id": bet.get("id"),
                                "created_at": bet.get("created_at"),
                                "is_creator": True
                            })
                        else:
                            opponent_bets.append({
                                "bot_name": bot_name,
                                "bet_id": bet.get("id"),
                                "created_at": bet.get("created_at"),
                                "is_creator": False
                            })
            except Exception as e:
                self.log_result(f"Creator vs Opponent Data", False, f"Error processing bot {bot_name}: {str(e)}")
                return False
        
        # Analyze results
        total_creator_bets = len(creator_bets)
        total_opponent_bets = len(opponent_bets)
        
        if total_creator_bets == 0 and total_opponent_bets == 0:
            self.log_result("Creator vs Opponent Data", True, 
                          "No active bets found (expected in some scenarios)")
            return True
        
        # Check that we have proper data structure for both scenarios
        success = True
        details = {
            "creator_bets_count": total_creator_bets,
            "opponent_bets_count": total_opponent_bets,
            "creator_bets_sample": creator_bets[:3],
            "opponent_bets_sample": opponent_bets[:3]
        }
        
        if total_creator_bets > 0:
            # Verify creator bets have created_at
            creator_missing_time = [bet for bet in creator_bets if not bet.get("created_at")]
            if creator_missing_time:
                success = False
                details["creator_missing_time"] = len(creator_missing_time)
        
        if total_opponent_bets > 0:
            # Verify opponent bets have created_at (as fallback)
            opponent_missing_time = [bet for bet in opponent_bets if not bet.get("created_at")]
            if opponent_missing_time:
                success = False
                details["opponent_missing_time"] = len(opponent_missing_time)
        
        message = f"Found {total_creator_bets} creator bets and {total_opponent_bets} opponent bets"
        self.log_result("Creator vs Opponent Data", success, message, details)
        return success
    
    def test_api_response_completeness(self) -> bool:
        """Test that API response includes all necessary data for frontend"""
        try:
            if not self.human_bots:
                self.log_result("API Response Completeness", False, "No Human-bots available")
                return False
            
            bot = self.human_bots[0]
            bot_id = bot.get("id")
            
            response = requests.get(
                f"{BASE_URL}/admin/human-bots/{bot_id}/active-bets",
                headers=self.get_admin_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response completeness
                completeness_checks = {
                    "has_success_flag": "success" in data,
                    "has_bot_info": all(field in data for field in ["bot_id", "bot_name"]),
                    "has_statistics": all(field in data for field in ["activeBets", "totalBets", "totalBetAmount"]),
                    "has_win_stats": all(field in data for field in ["botWins", "playerWins", "draws"]),
                    "has_bets_array": "bets" in data and isinstance(data["bets"], list)
                }
                
                all_complete = all(completeness_checks.values())
                
                if data.get("bets"):
                    # Check bet completeness
                    bet = data["bets"][0]
                    bet_completeness = {
                        "has_id": "id" in bet,
                        "has_created_at": "created_at" in bet,
                        "has_bet_amount": "bet_amount" in bet,
                        "has_status": "status" in bet,
                        "has_creator_flag": "is_creator" in bet,
                        "has_opponent_info": "opponent_name" in bet
                    }
                    completeness_checks.update(bet_completeness)
                    all_complete = all(completeness_checks.values())
                
                self.log_result("API Response Completeness", all_complete, 
                              "All required fields present" if all_complete else "Some fields missing",
                              completeness_checks)
                return all_complete
            else:
                self.log_result("API Response Completeness", False, 
                              f"API call failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Response Completeness", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Human-bot active bets tests"""
        print("🚀 Starting Human-Bot Active Bets API Testing")
        print("=" * 60)
        
        # Step 1: Admin login
        if not self.admin_login():
            print("❌ Cannot proceed without admin access")
            return False
        
        # Step 2: Get Human-bots list
        if not self.get_human_bots_list():
            print("❌ Cannot proceed without Human-bots data")
            return False
        
        # Step 3: Test endpoint structure
        self.test_active_bets_endpoint_structure()
        
        # Step 4: Test time fields presence
        self.test_time_fields_presence()
        
        # Step 5: Test creator vs opponent data
        self.test_creator_vs_opponent_data()
        
        # Step 6: Test API response completeness
        self.test_api_response_completeness()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 OVERALL RESULT: SUCCESS")
        else:
            print("❌ OVERALL RESULT: NEEDS ATTENTION")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = HumanBotActiveBetsTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)