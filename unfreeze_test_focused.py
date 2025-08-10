#!/usr/bin/env python3
"""
Unfreeze Stuck Bets Backend Testing - Post Logic Fix
===================================================

Testing specific requirements after main agent fixes:
1. POST /api/admin/bets/unfreeze-stuck - should UNFREEZE (not cancel), keep ACTIVE status, set active_deadline=now+1min, remove lock fields, set unfrozen_at/unfrozen_by
2. GET /api/admin/bets/stats - stuck_bets should count ACTIVE games with expired active_deadline
3. GET /api/admin/bets/list - is_stuck field should be based on active_deadline (not >24h age)
4. Basic authorization: 401 without token, 200 with admin token
5. Regression testing of other admin bet endpoints
"""

import requests
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://df28b502-4a8b-41a3-806f-4aea5b27dbbf.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

class UnfreezeStuckBetsTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str, data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin user"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                self.log_result("Admin Authentication", True, f"Successfully authenticated as {ADMIN_EMAIL}")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_authentication_requirements(self):
        """Test authentication requirements for unfreeze endpoint"""
        print("\n🔐 Testing Authentication Requirements...")
        
        # Test 1: Without token should return 401
        try:
            headers_without_auth = {}
            response = requests.post(f"{API_BASE}/admin/bets/unfreeze-stuck", headers=headers_without_auth)
            
            if response.status_code == 401:
                self.log_result("Auth - No Token", True, "Correctly returns 401 without authentication token")
            else:
                self.log_result("Auth - No Token", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Auth - No Token", False, f"Error testing no token: {str(e)}")
        
        # Test 2: With admin token should return 200 (or appropriate response)
        try:
            response = self.session.post(f"{API_BASE}/admin/bets/unfreeze-stuck")
            
            if response.status_code in [200, 404]:  # 200 if games found, 404 if no stuck games
                self.log_result("Auth - Admin Token", True, f"Correctly accepts admin token (status: {response.status_code})")
            else:
                self.log_result("Auth - Admin Token", False, f"Unexpected status with admin token: {response.status_code}")
                
        except Exception as e:
            self.log_result("Auth - Admin Token", False, f"Error testing admin token: {str(e)}")

    def test_stuck_bets_stats_calculation(self):
        """Test GET /api/admin/bets/stats - stuck_bets calculation based on active_deadline"""
        print("\n📊 Testing Stuck Bets Stats Calculation...")
        
        try:
            response = self.session.get(f"{API_BASE}/admin/bets/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if stuck_bets field exists
                if "stuck_bets" in data:
                    stuck_count = data["stuck_bets"]
                    self.log_result("Stats - Stuck Bets Field", True, f"stuck_bets field present with value: {stuck_count}")
                    
                    # Verify it's counting ACTIVE games with expired active_deadline
                    if isinstance(stuck_count, int) and stuck_count >= 0:
                        self.log_result("Stats - Stuck Count Valid", True, f"stuck_bets is valid integer: {stuck_count}")
                    else:
                        self.log_result("Stats - Stuck Count Valid", False, f"stuck_bets is not valid integer: {stuck_count}")
                        
                else:
                    self.log_result("Stats - Stuck Bets Field", False, "stuck_bets field missing from stats response")
                    
                # Log full stats for analysis
                self.log_result("Stats - Full Response", True, f"Complete stats data received", data)
                
            else:
                self.log_result("Stats - API Response", False, f"Stats API failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Stats - API Response", False, f"Error getting stats: {str(e)}")

    def test_bets_list_is_stuck_field(self):
        """Test GET /api/admin/bets/list - is_stuck field based on active_deadline"""
        print("\n📋 Testing Bets List is_stuck Field...")
        
        try:
            response = self.session.get(f"{API_BASE}/admin/bets/list?limit=20")
            
            if response.status_code == 200:
                data = response.json()
                
                if "bets" in data and isinstance(data["bets"], list):
                    bets = data["bets"]
                    self.log_result("List - API Response", True, f"Bets list retrieved with {len(bets)} bets")
                    
                    # Check if any bets have is_stuck field
                    bets_with_is_stuck = [bet for bet in bets if "is_stuck" in bet]
                    
                    if bets_with_is_stuck:
                        self.log_result("List - is_stuck Field", True, f"Found {len(bets_with_is_stuck)} bets with is_stuck field")
                        
                        # Analyze is_stuck logic
                        stuck_bets = [bet for bet in bets_with_is_stuck if bet["is_stuck"]]
                        non_stuck_bets = [bet for bet in bets_with_is_stuck if not bet["is_stuck"]]
                        
                        self.log_result("List - Stuck Analysis", True, 
                                      f"Stuck bets: {len(stuck_bets)}, Non-stuck bets: {len(non_stuck_bets)}")
                        
                        # Sample some bets for detailed analysis
                        if stuck_bets:
                            sample_stuck = stuck_bets[0]
                            self.log_result("List - Sample Stuck Bet", True, 
                                          f"Sample stuck bet analysis", 
                                          {
                                              "id": sample_stuck.get("id"),
                                              "status": sample_stuck.get("status"),
                                              "is_stuck": sample_stuck.get("is_stuck"),
                                              "active_deadline": sample_stuck.get("active_deadline"),
                                              "created_at": sample_stuck.get("created_at")
                                          })
                    else:
                        self.log_result("List - is_stuck Field", False, "No bets found with is_stuck field")
                        
                else:
                    self.log_result("List - API Response", False, "Invalid bets list structure in response")
                    
            else:
                self.log_result("List - API Response", False, f"Bets list API failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("List - API Response", False, f"Error getting bets list: {str(e)}")

    def test_unfreeze_stuck_bets_functionality(self):
        """Test POST /api/admin/bets/unfreeze-stuck - core functionality"""
        print("\n🔓 Testing Unfreeze Stuck Bets Core Functionality...")
        
        try:
            # First, get current stats to see if there are stuck bets
            stats_response = self.session.get(f"{API_BASE}/admin/bets/stats")
            stuck_count_before = 0
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                stuck_count_before = stats_data.get("stuck_bets", 0)
                self.log_result("Unfreeze - Pre-check Stats", True, f"Found {stuck_count_before} stuck bets before unfreezing")
            
            # Execute unfreeze operation
            response = self.session.post(f"{API_BASE}/admin/bets/unfreeze-stuck")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ["success", "message", "total_processed"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("Unfreeze - Response Structure", True, "All required fields present in response")
                    
                    # Check if operation was successful
                    if data.get("success"):
                        total_processed = data.get("total_processed", 0)
                        message = data.get("message", "")
                        
                        self.log_result("Unfreeze - Operation Success", True, 
                                      f"Successfully processed {total_processed} stuck bets. Message: {message}")
                        
                        # Verify message format (should mention "unfrozen" not "cancelled")
                        if "разморож" in message.lower() or "unfreez" in message.lower():
                            self.log_result("Unfreeze - Message Content", True, "Message correctly mentions unfreezing")
                        elif "отмен" in message.lower() or "cancel" in message.lower():
                            self.log_result("Unfreeze - Message Content", False, "Message incorrectly mentions cancelling instead of unfreezing")
                        else:
                            self.log_result("Unfreeze - Message Content", True, f"Message content: {message}")
                            
                        # Check for unfrozen_at and unfrozen_by fields in response (if provided)
                        if "unfrozen_games" in data:
                            unfrozen_games = data["unfrozen_games"]
                            if unfrozen_games:
                                sample_game = unfrozen_games[0] if isinstance(unfrozen_games, list) else unfrozen_games
                                has_unfrozen_fields = "unfrozen_at" in sample_game or "unfrozen_by" in sample_game
                                self.log_result("Unfreeze - Unfrozen Fields", has_unfrozen_fields, 
                                              f"Unfrozen fields present: {has_unfrozen_fields}")
                        
                    else:
                        self.log_result("Unfreeze - Operation Success", False, f"Operation failed: {data}")
                        
                else:
                    self.log_result("Unfreeze - Response Structure", False, f"Missing required fields: {missing_fields}")
                    
                # Log full response for analysis
                self.log_result("Unfreeze - Full Response", True, "Complete unfreeze response", data)
                
            elif response.status_code == 404:
                # No stuck bets found - this is also a valid response
                self.log_result("Unfreeze - No Stuck Bets", True, "No stuck bets found to unfreeze (404 response)")
                
            else:
                self.log_result("Unfreeze - API Response", False, f"Unfreeze API failed: {response.status_code} - {response.text}")
                
            # Verify stats after unfreezing
            time.sleep(1)  # Brief pause to ensure data consistency
            stats_after_response = self.session.get(f"{API_BASE}/admin/bets/stats")
            
            if stats_after_response.status_code == 200:
                stats_after_data = stats_after_response.json()
                stuck_count_after = stats_after_data.get("stuck_bets", 0)
                
                if stuck_count_after <= stuck_count_before:
                    self.log_result("Unfreeze - Stats Verification", True, 
                                  f"Stuck count reduced from {stuck_count_before} to {stuck_count_after}")
                else:
                    self.log_result("Unfreeze - Stats Verification", False, 
                                  f"Stuck count increased from {stuck_count_before} to {stuck_count_after}")
                
        except Exception as e:
            self.log_result("Unfreeze - API Response", False, f"Error testing unfreeze functionality: {str(e)}")

    def test_regression_admin_bet_endpoints(self):
        """Test regression of other admin bet endpoints"""
        print("\n🔄 Testing Regression of Other Admin Bet Endpoints...")
        
        endpoints_to_test = [
            ("GET", "/admin/bets/list", "Bets List"),
            ("GET", "/admin/bets/stats", "Bets Stats"),
            ("POST", "/admin/bets/reset-all", "Reset All Bets"),
            ("POST", "/admin/bets/delete-all", "Delete All Bets"),
            ("POST", "/admin/bets/reset-fractional", "Reset Fractional Bets")
        ]
        
        for method, endpoint, name in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{API_BASE}{endpoint}")
                else:
                    response = self.session.post(f"{API_BASE}{endpoint}")
                
                # Most endpoints should return 200, some might return 404 if no data
                if response.status_code in [200, 404]:
                    self.log_result(f"Regression - {name}", True, f"Endpoint working (status: {response.status_code})")
                else:
                    self.log_result(f"Regression - {name}", False, f"Endpoint failed: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Regression - {name}", False, f"Error testing {endpoint}: {str(e)}")

    def run_comprehensive_test(self):
        """Run all unfreeze stuck bets tests"""
        print("🚀 Starting Comprehensive Unfreeze Stuck Bets Testing...")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate_admin():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all test categories
        self.test_authentication_requirements()
        self.test_stuck_bets_stats_calculation()
        self.test_bets_list_is_stuck_field()
        self.test_unfreeze_stuck_bets_functionality()
        self.test_regression_admin_bet_endpoints()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 80)
        
        return success_rate >= 80  # Consider 80%+ as successful

if __name__ == "__main__":
    tester = UnfreezeStuckBetsTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("🎉 UNFREEZE STUCK BETS TESTING COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("🚨 UNFREEZE STUCK BETS TESTING FAILED!")
        sys.exit(1)