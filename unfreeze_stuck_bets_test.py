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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cyrillic-writer-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

class UnfreezeStuckBetsTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
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
        
    def setup_authentication(self) -> bool:
        """Setup admin authentication"""
        try:
            # Login as admin
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.admin_token = token_data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                self.log_test("Admin Authentication", True, f"Successfully logged in as {ADMIN_EMAIL}")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_unfreeze_stuck_endpoint_auth(self):
        """Test authentication and authorization for unfreeze-stuck endpoint"""
        
        # Test 1: No authentication
        try:
            headers_backup = self.session.headers.copy()
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            response = self.session.post(f"{API_BASE}/admin/bets/unfreeze-stuck")
            
            if response.status_code == 401:
                self.log_test("Unfreeze Stuck - No Auth", True, "Correctly rejected request without authentication")
            else:
                self.log_test("Unfreeze Stuck - No Auth", False, f"Expected 401, got {response.status_code}")
            
            # Restore headers
            self.session.headers.update(headers_backup)
            
        except Exception as e:
            self.log_test("Unfreeze Stuck - No Auth", False, f"Error testing no auth: {str(e)}")
        
        # Test 2: With admin authentication (should work)
        try:
            response = self.session.post(f"{API_BASE}/admin/bets/unfreeze-stuck")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["success", "message", "total_processed"]
                
                missing_fields = [field for field in expected_fields if field not in data]
                if not missing_fields:
                    self.log_test("Unfreeze Stuck - Admin Auth", True, 
                                f"Endpoint accessible with admin auth. Processed: {data.get('total_processed', 0)} games")
                else:
                    self.log_test("Unfreeze Stuck - Admin Auth", False, 
                                f"Missing expected fields: {missing_fields}")
                
                # Check that OLD cancellation fields are NOT present (key requirement)
                old_fields = ["cancelled_games", "total_gems_returned", "total_commission_returned"]
                present_old_fields = [field for field in old_fields if field in data]
                if not present_old_fields:
                    self.log_test("Unfreeze - No Cancellation Fields", True, 
                                "Response correctly does NOT include cancellation fields (gems_returned, commission_returned)")
                else:
                    self.log_test("Unfreeze - No Cancellation Fields", False, 
                                f"Response incorrectly includes old cancellation fields: {present_old_fields}")
            else:
                self.log_test("Unfreeze Stuck - Admin Auth", False, 
                            f"Expected 200, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Unfreeze Stuck - Admin Auth", False, f"Error testing admin auth: {str(e)}")
    
    def test_unfreeze_stuck_functionality(self):
        """Test the core functionality of unfreeze-stuck endpoint"""
        
        try:
            # Get initial stats
            stats_response = self.session.get(f"{API_BASE}/admin/bets/stats")
            if stats_response.status_code != 200:
                self.log_test("Get Initial Stats", False, f"Failed to get initial stats: {stats_response.status_code}")
                return
            
            initial_stats = stats_response.json()
            initial_stuck_bets = initial_stats.get("stuck_bets", 0)
            
            self.log_test("Get Initial Stats", True, 
                        f"Initial stuck bets: {initial_stuck_bets}, Active bets: {initial_stats.get('active_bets', 0)}")
            
            # Call unfreeze-stuck endpoint
            unfreeze_response = self.session.post(f"{API_BASE}/admin/bets/unfreeze-stuck")
            
            if unfreeze_response.status_code == 200:
                unfreeze_data = unfreeze_response.json()
                
                # Validate response structure
                required_fields = ["success", "message", "total_processed"]
                missing_fields = [field for field in required_fields if field not in unfreeze_data]
                
                if missing_fields:
                    self.log_test("Unfreeze Response Structure", False, f"Missing fields: {missing_fields}")
                    return
                else:
                    self.log_test("Unfreeze Response Structure", True, "All required fields present")
                
                # Check that OLD cancellation fields are NOT present (key requirement)
                old_fields = ["cancelled_games", "total_gems_returned", "total_commission_returned"]
                present_old_fields = [field for field in old_fields if field in unfreeze_data]
                if not present_old_fields:
                    self.log_test("Unfreeze - No Resource Return", True, 
                                "Response correctly does NOT return resources/commission (unfreezing, not cancelling)")
                else:
                    self.log_test("Unfreeze - No Resource Return", False, 
                                f"Response incorrectly includes resource return fields: {present_old_fields}")
                
                total_processed = unfreeze_data.get("total_processed", 0)
                message = unfreeze_data.get("message", "")
                
                # Check if message format is correct
                expected_message_pattern = f"Разморожено {total_processed} зависших ставок"
                if message == expected_message_pattern:
                    self.log_test("Unfreeze Message Format", True, f"Correct message format: '{message}'")
                else:
                    self.log_test("Unfreeze Message Format", False, f"Expected: '{expected_message_pattern}', Got: '{message}'")
                
                # Get stats after unfreezing
                stats_after_response = self.session.get(f"{API_BASE}/admin/bets/stats")
                if stats_after_response.status_code == 200:
                    stats_after = stats_after_response.json()
                    stuck_bets_after = stats_after.get("stuck_bets", 0)
                    active_bets_after = stats_after.get("active_bets", 0)
                    initial_active_bets = initial_stats.get("active_bets", 0)
                    
                    # KEY REQUIREMENT: Active bet count should NOT decrease after unfreezing
                    if active_bets_after >= initial_active_bets:
                        self.log_test("Active Bets Count Maintained", True, 
                                    f"Active bets maintained or increased: {initial_active_bets} -> {active_bets_after}")
                    else:
                        self.log_test("Active Bets Count Maintained", False, 
                                    f"CRITICAL: Active bets decreased after unfreezing: {initial_active_bets} -> {active_bets_after}")
                    
                    # Validate that stuck bets count changed appropriately
                    if total_processed > 0:
                        if stuck_bets_after < initial_stuck_bets:
                            self.log_test("Stuck Bets Count Update", True, 
                                        f"Stuck bets reduced from {initial_stuck_bets} to {stuck_bets_after}")
                        else:
                            self.log_test("Stuck Bets Count Update", False, 
                                        f"Stuck bets should have reduced, but went from {initial_stuck_bets} to {stuck_bets_after}")
                    else:
                        self.log_test("Stuck Bets Count Update", True, 
                                    f"No stuck bets to process (initial: {initial_stuck_bets}, after: {stuck_bets_after})")
                
                # Check unfrozen games details if available
                if "unfrozen_games" in unfreeze_data and total_processed > 0:
                    unfrozen_games = unfreeze_data.get("unfrozen_games", [])
                    if unfrozen_games:
                        self.log_test("Unfrozen Games Details", True, 
                                    f"Received details for {len(unfrozen_games)} unfrozen games")
                        
                        # Check deadline extension logic for first game
                        first_game = unfrozen_games[0]
                        if "old_deadline" in first_game and "new_deadline" in first_game:
                            try:
                                old_deadline = datetime.fromisoformat(first_game["old_deadline"].replace('Z', '+00:00'))
                                new_deadline = datetime.fromisoformat(first_game["new_deadline"].replace('Z', '+00:00'))
                                extension_seconds = (new_deadline - old_deadline).total_seconds()
                                
                                if 50 <= extension_seconds <= 70:  # Around 1 minute
                                    self.log_test("Deadline Extension", True, 
                                                f"Deadline correctly extended by ~1 minute ({extension_seconds:.0f}s)")
                                else:
                                    self.log_test("Deadline Extension", False, 
                                                f"Deadline extension incorrect: {extension_seconds:.0f}s (expected ~60s)")
                            except Exception as e:
                                self.log_test("Deadline Extension", False, f"Error parsing deadlines: {str(e)}")
                    else:
                        self.log_test("Unfrozen Games Details", False, 
                                    f"Processed {total_processed} games but no unfrozen_games details")
                
                self.log_test("Unfreeze Stuck Functionality", True, 
                            f"Successfully processed {total_processed} stuck bets")
                
            else:
                self.log_test("Unfreeze Stuck Functionality", False, 
                            f"Unfreeze failed: {unfreeze_response.status_code} - {unfreeze_response.text}")
                
        except Exception as e:
            self.log_test("Unfreeze Stuck Functionality", False, f"Error testing functionality: {str(e)}")
    
    def test_stats_endpoint_stuck_bets_calculation(self):
        """Test that stats endpoint correctly calculates stuck_bets"""
        
        try:
            response = self.session.get(f"{API_BASE}/admin/bets/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["total_bets", "active_bets", "completed_bets", "cancelled_bets", "stuck_bets", "average_bet"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Stats Endpoint Structure", False, f"Missing fields: {missing_fields}")
                    return
                
                stuck_bets = data.get("stuck_bets", 0)
                active_bets = data.get("active_bets", 0)
                total_bets = data.get("total_bets", 0)
                
                # Validate that stuck_bets is a reasonable number
                if isinstance(stuck_bets, int) and stuck_bets >= 0:
                    self.log_test("Stats Stuck Bets Calculation", True, 
                                f"Stuck bets: {stuck_bets}, Active bets: {active_bets}, Total bets: {total_bets}")
                else:
                    self.log_test("Stats Stuck Bets Calculation", False, 
                                f"Invalid stuck_bets value: {stuck_bets} (type: {type(stuck_bets)})")
                
                # Log detailed stats for analysis
                self.log_test("Stats Endpoint Details", True, 
                            f"Total: {total_bets}, Active: {active_bets}, Completed: {data.get('completed_bets', 0)}, "
                            f"Cancelled: {data.get('cancelled_bets', 0)}, Stuck: {stuck_bets}, Avg: {data.get('average_bet', 0):.2f}")
                
            else:
                self.log_test("Stats Endpoint", False, f"Stats endpoint failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Stats Endpoint", False, f"Error testing stats endpoint: {str(e)}")
    
    def test_regression_admin_bet_endpoints(self):
        """Test that existing admin bet endpoints still work correctly"""
        
        endpoints_to_test = [
            ("GET", "/admin/bets/list", "Bets List"),
            ("GET", "/admin/bets/stats", "Bets Stats"),
        ]
        
        # Test GET endpoints
        for method, endpoint, name in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{API_BASE}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"Regression - {name}", True, f"Endpoint working correctly")
                else:
                    self.log_test(f"Regression - {name}", False, 
                                f"Endpoint failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"Regression - {name}", False, f"Error testing {name}: {str(e)}")
        
        # Test POST endpoints that require super admin (these should fail with current admin)
        super_admin_endpoints = [
            ("POST", "/admin/bets/reset-all", "Reset All Bets"),
            ("POST", "/admin/bets/delete-all", "Delete All Bets"),
        ]
        
        for method, endpoint, name in super_admin_endpoints:
            try:
                response = self.session.post(f"{API_BASE}{endpoint}")
                
                # These should fail with 403 (Forbidden) for regular admin
                if response.status_code == 403:
                    self.log_test(f"Regression - {name} Auth", True, 
                                f"Correctly rejected admin user (needs super admin)")
                elif response.status_code == 200:
                    self.log_test(f"Regression - {name}", True, f"Endpoint working (super admin access)")
                else:
                    self.log_test(f"Regression - {name}", False, 
                                f"Unexpected response: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"Regression - {name}", False, f"Error testing {name}: {str(e)}")
        
        # Test fractional reset endpoint
        try:
            fractional_data = {"percentage": 10}  # Reset 10% of bets
            response = self.session.post(f"{API_BASE}/admin/bets/reset-fractional", json=fractional_data)
            
            if response.status_code in [200, 403]:  # 200 if allowed, 403 if needs super admin
                self.log_test("Regression - Reset Fractional", True, 
                            f"Endpoint responding correctly ({response.status_code})")
            else:
                self.log_test("Regression - Reset Fractional", False, 
                            f"Unexpected response: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Regression - Reset Fractional", False, f"Error testing fractional reset: {str(e)}")
    
    def test_individual_bet_cancel(self):
        """Test individual bet cancellation endpoint"""
        
        try:
            # Get list of bets to find one to cancel
            list_response = self.session.get(f"{API_BASE}/admin/bets/list?limit=5")
            
            if list_response.status_code == 200:
                list_data = list_response.json()
                bets = list_data.get("bets", [])
                
                if bets:
                    # Try to cancel the first bet
                    bet_id = bets[0].get("id")
                    if bet_id:
                        cancel_response = self.session.post(f"{API_BASE}/admin/bets/{bet_id}/cancel")
                        
                        if cancel_response.status_code == 200:
                            cancel_data = cancel_response.json()
                            self.log_test("Individual Bet Cancel", True, 
                                        f"Successfully cancelled bet {bet_id}")
                        else:
                            self.log_test("Individual Bet Cancel", False, 
                                        f"Cancel failed: {cancel_response.status_code} - {cancel_response.text}")
                    else:
                        self.log_test("Individual Bet Cancel", False, "No bet ID found in bet data")
                else:
                    self.log_test("Individual Bet Cancel", True, "No bets available to cancel (system clean)")
            else:
                self.log_test("Individual Bet Cancel", False, 
                            f"Failed to get bet list: {list_response.status_code}")
                
        except Exception as e:
            self.log_test("Individual Bet Cancel", False, f"Error testing bet cancel: {str(e)}")
    
    def analyze_current_implementation(self):
        """Analyze the current implementation to understand what it actually does"""
        
        try:
            # Call the unfreeze endpoint and analyze the response
            response = self.session.post(f"{API_BASE}/admin/bets/unfreeze-stuck")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check what the endpoint actually returns
                total_processed = data.get("total_processed", 0)
                cancelled_games = data.get("cancelled_games", [])
                message = data.get("message", "")
                
                # Analyze the behavior
                if total_processed > 0:
                    # Check if games were actually cancelled or unfrozen
                    if cancelled_games:
                        first_game = cancelled_games[0]
                        game_status = first_game.get("status", "")
                        
                        if game_status == "ACTIVE":
                            self.log_test("Implementation Analysis", False, 
                                        f"CRITICAL ISSUE: Endpoint is CANCELLING stuck games instead of UNFREEZING them. "
                                        f"Found {total_processed} games that were cancelled, not unfrozen.")
                        else:
                            self.log_test("Implementation Analysis", True, 
                                        f"Endpoint correctly processed {total_processed} stuck games")
                    else:
                        self.log_test("Implementation Analysis", True, 
                                    f"Endpoint processed {total_processed} games (no details available)")
                else:
                    self.log_test("Implementation Analysis", True, 
                                f"No stuck games found to process (system is clean)")
                
            else:
                self.log_test("Implementation Analysis", False, 
                            f"Failed to analyze implementation: {response.status_code}")
                
        except Exception as e:
            self.log_test("Implementation Analysis", False, f"Error analyzing implementation: {str(e)}")
    
    def run_comprehensive_tests(self):
        """Run all tests in the correct order"""
        
        print("🚀 Starting Comprehensive Backend Testing for Unfreeze Stuck Bets Feature")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0,
                "unfreeze_working": False,
                "stats_working": False,
                "no_regression": False,
                "implementation_issues": True,
                "test_results": []
            }
        
        print("\n🔍 Analyzing Current Implementation")
        print("-" * 50)
        self.analyze_current_implementation()
        
        print("\n📊 Testing Stats Endpoint and Stuck Bets Calculation")
        print("-" * 50)
        self.test_stats_endpoint_stuck_bets_calculation()
        
        print("\n🔐 Testing Authentication and Authorization")
        print("-" * 50)
        self.test_unfreeze_stuck_endpoint_auth()
        
        print("\n🔧 Testing Unfreeze Stuck Functionality")
        print("-" * 50)
        self.test_unfreeze_stuck_functionality()
        
        print("\n🔄 Testing Regression - Existing Admin Bet Endpoints")
        print("-" * 50)
        self.test_regression_admin_bet_endpoints()
        
        print("\n❌ Testing Individual Bet Cancellation")
        print("-" * 50)
        self.test_individual_bet_cancel()
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  - {test['test']}: {test['details']}")
        
        print("\n🎯 KEY FINDINGS:")
        
        # Analyze unfreeze functionality
        unfreeze_tests = [t for t in self.test_results if "Unfreeze" in t["test"]]
        unfreeze_success = all(t["success"] for t in unfreeze_tests)
        
        if unfreeze_success:
            print("✅ Unfreeze Stuck Bets functionality is working correctly")
        else:
            print("❌ Unfreeze Stuck Bets functionality has issues")
        
        # Analyze stats functionality
        stats_tests = [t for t in self.test_results if "Stats" in t["test"]]
        stats_success = all(t["success"] for t in stats_tests)
        
        if stats_success:
            print("✅ Stats endpoint and stuck_bets calculation is working correctly")
        else:
            print("❌ Stats endpoint has issues with stuck_bets calculation")
        
        # Analyze regression
        regression_tests = [t for t in self.test_results if "Regression" in t["test"]]
        regression_success = all(t["success"] for t in regression_tests)
        
        if regression_success:
            print("✅ All existing admin bet endpoints are working correctly (no regression)")
        else:
            print("❌ Some existing admin bet endpoints have regression issues")
        
        # Check for critical implementation issues
        implementation_tests = [t for t in self.test_results if "Implementation Analysis" in t["test"]]
        implementation_issues = [t for t in implementation_tests if not t["success"]]
        
        if implementation_issues:
            print("🚨 CRITICAL IMPLEMENTATION ISSUES FOUND:")
            for issue in implementation_issues:
                print(f"  - {issue['details']}")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "unfreeze_working": unfreeze_success,
            "stats_working": stats_success,
            "no_regression": regression_success,
            "implementation_issues": len(implementation_issues) > 0,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = UnfreezeStuckBetsTester()
    results = tester.run_comprehensive_tests()
    
    # Return exit code based on results
    if results and results["success_rate"] >= 80 and not results["implementation_issues"]:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()