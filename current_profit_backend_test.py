#!/usr/bin/env python3
"""
CURRENT PROFIT FIELD TESTING - Backend API Testing
Testing the new current_profit field and admin profit endpoints as requested in review.

REQUIREMENTS TO TEST:
1. GET /api/admin/bots/regular/list must return current_profit field per bot (number), 
   computed as sum_wins - sum_losses of the current cycle, non-negative or negative as per data; 
   and existing fields unchanged.

2. Verify existing Regular Bots endpoints still pass: 
   - /api/admin/bots/{id}/cycle-bets
   - /api/admin/bots/{id}
   - /api/admin/bots/{id}/recalculate-bets
   - /api/admin/bots/regular/list structure (active_pool, cycle_total_display, current_cycle_wins/losses/draws default 0)
   - lobby endpoints unaffected

3. Admin Profit endpoints: 
   - /api/admin/profit/stats
   - /api/admin/profit/bot-integration
   - /api/admin/profit/bot-revenue-details
   Should respond without reliance on legacy creation_modes/behaviors; 
   ensure /admin/profit/bot-integration returns bot_stats, efficiency, recent_transactions 
   and does not include creation_modes/behaviors to avoid Object.entries null error on frontend.

Using admin@gemplay.com / Admin123! for authorization
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
from datetime import datetime

# Configuration
BASE_URL = "https://49b21745-59e5-4980-8f15-13cafed79fb5.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print test result with colors"""
    status = f"{Colors.GREEN}✅ PASSED{Colors.END}" if success else f"{Colors.RED}❌ FAILED{Colors.END}"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {Colors.YELLOW}Details: {details}{Colors.END}")

def record_test(test_name: str, success: bool, details: str = "", response_data: Any = None):
    """Record test result"""
    test_results["total"] += 1
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    test_results["tests"].append({
        "name": test_name,
        "success": success,
        "details": details,
        "response_data": response_data,
        "timestamp": datetime.now().isoformat()
    })
    
    print_test_result(test_name, success, details)

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None, params: Dict = None) -> Tuple[bool, Any, str]:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return False, None, f"Unsupported method: {method}"
        
        response_time = time.time() - start_time
        
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        success = response.status_code in [200, 201]
        details = f"Status: {response.status_code}, Time: {response_time:.3f}s"
        
        if not success:
            details += f", Error: {response_data}"
        
        return success, response_data, details
        
    except requests.exceptions.Timeout:
        return False, None, "Request timeout (30s)"
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error"
    except Exception as e:
        return False, None, f"Request error: {str(e)}"

def authenticate_admin() -> Optional[str]:
    """Authenticate as admin and return access token"""
    print(f"{Colors.BLUE}🔐 Authenticating as admin user...{Colors.END}")
    
    success, response_data, details = make_request(
        "POST", 
        "/auth/login",
        data=ADMIN_USER
    )
    
    if success and response_data and "access_token" in response_data:
        token = response_data["access_token"]
        print(f"{Colors.GREEN}✅ Admin authentication successful{Colors.END}")
        return token
    else:
        print(f"{Colors.RED}❌ Admin authentication failed: {details}{Colors.END}")
        return None

def test_regular_bots_list_current_profit():
    """Test 1: GET /api/admin/bots/regular/list must return current_profit field per bot"""
    print(f"\n{Colors.MAGENTA}🧪 Test 1: Testing current_profit field in Regular Bots List{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Regular Bots List - current_profit field", False, "Failed to authenticate as admin")
        return None
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/admin/bots/regular/list endpoint...")
    
    # Get regular bots list
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular/list",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Regular Bots List - current_profit field",
            False,
            f"Failed to get regular bots list: {details}"
        )
        return None
    
    # Check if response has bots
    bots = response_data.get("bots", []) if isinstance(response_data, dict) else response_data
    if not bots:
        record_test(
            "Regular Bots List - current_profit field",
            False,
            "No bots found in response"
        )
        return None
    
    print(f"   📊 Found {len(bots)} regular bots to analyze")
    
    # Check each bot for current_profit field
    bots_with_current_profit = 0
    bots_with_valid_current_profit = 0
    current_profit_values = []
    missing_fields = []
    
    for i, bot in enumerate(bots):
        bot_id = bot.get("id", f"bot_{i}")
        bot_name = bot.get("name", f"Unknown_{i}")
        
        # Check for current_profit field
        if "current_profit" in bot:
            bots_with_current_profit += 1
            current_profit = bot["current_profit"]
            current_profit_values.append(current_profit)
            
            # Validate that current_profit is a number
            if isinstance(current_profit, (int, float)):
                bots_with_valid_current_profit += 1
                print(f"      ✅ Bot '{bot_name}' has current_profit: {current_profit}")
            else:
                print(f"      ❌ Bot '{bot_name}' has invalid current_profit type: {type(current_profit)} = {current_profit}")
        else:
            missing_fields.append(bot_name)
            print(f"      ❌ Bot '{bot_name}' missing current_profit field")
        
        # Check for existing required fields
        required_fields = ["active_pool", "cycle_total_display", "current_cycle_wins", "current_cycle_losses", "current_cycle_draws"]
        for field in required_fields:
            if field not in bot:
                print(f"      ⚠️ Bot '{bot_name}' missing required field: {field}")
    
    # Evaluate results
    all_bots_have_current_profit = bots_with_current_profit == len(bots)
    all_current_profit_valid = bots_with_valid_current_profit == len(bots)
    
    if all_bots_have_current_profit and all_current_profit_valid:
        record_test(
            "Regular Bots List - current_profit field",
            True,
            f"All {len(bots)} bots have valid current_profit field. Values: {current_profit_values}"
        )
    elif all_bots_have_current_profit:
        record_test(
            "Regular Bots List - current_profit field",
            False,
            f"All bots have current_profit field but {len(bots) - bots_with_valid_current_profit} have invalid types"
        )
    else:
        record_test(
            "Regular Bots List - current_profit field",
            False,
            f"Only {bots_with_current_profit}/{len(bots)} bots have current_profit field. Missing: {missing_fields}"
        )
    
    return bots

def test_regular_bot_individual_endpoints(bots):
    """Test 2: Verify existing Regular Bots endpoints still pass"""
    print(f"\n{Colors.MAGENTA}🧪 Test 2: Testing Individual Regular Bot Endpoints{Colors.END}")
    
    if not bots:
        record_test("Regular Bot Individual Endpoints", False, "No bots available from previous test")
        return
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Regular Bot Individual Endpoints", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test with first available bot
    test_bot = bots[0]
    bot_id = test_bot.get("id")
    bot_name = test_bot.get("name", "Unknown")
    
    if not bot_id:
        record_test("Regular Bot Individual Endpoints", False, "No bot ID available for testing")
        return
    
    print(f"   📝 Testing endpoints for bot '{bot_name}' (ID: {bot_id})")
    
    endpoints_to_test = [
        ("/admin/bots/{id}", "GET", "Bot Details"),
        ("/admin/bots/{id}/cycle-bets", "GET", "Cycle Bets"),
        ("/admin/bots/{id}/recalculate-bets", "POST", "Recalculate Bets")
    ]
    
    endpoint_results = []
    
    for endpoint_template, method, name in endpoints_to_test:
        endpoint = endpoint_template.replace("{id}", bot_id)
        print(f"      Testing {method} {endpoint}...")
        
        success, response_data, details = make_request(
            method,
            endpoint,
            headers=headers
        )
        
        endpoint_results.append({
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "success": success,
            "details": details,
            "response_data": response_data
        })
        
        if success:
            print(f"         ✅ {name} endpoint working")
        else:
            print(f"         ❌ {name} endpoint failed: {details}")
    
    # Evaluate overall results
    successful_endpoints = sum(1 for result in endpoint_results if result["success"])
    total_endpoints = len(endpoint_results)
    
    if successful_endpoints == total_endpoints:
        record_test(
            "Regular Bot Individual Endpoints",
            True,
            f"All {total_endpoints} individual bot endpoints working correctly"
        )
    else:
        failed_endpoints = [result["name"] for result in endpoint_results if not result["success"]]
        record_test(
            "Regular Bot Individual Endpoints",
            False,
            f"Only {successful_endpoints}/{total_endpoints} endpoints working. Failed: {failed_endpoints}"
        )
    
    return endpoint_results

def test_admin_profit_endpoints():
    """Test 3: Admin Profit endpoints without legacy creation_modes/behaviors"""
    print(f"\n{Colors.MAGENTA}🧪 Test 3: Testing Admin Profit Endpoints{Colors.END}")
    
    # First authenticate as admin
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Admin Profit Endpoints", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    profit_endpoints = [
        ("/admin/profit/stats", "Profit Stats"),
        ("/admin/profit/bot-integration", "Bot Integration"),
        ("/admin/profit/bot-revenue-details", "Bot Revenue Details")
    ]
    
    endpoint_results = []
    
    for endpoint, name in profit_endpoints:
        print(f"   📝 Testing GET {endpoint}...")
        
        success, response_data, details = make_request(
            "GET",
            endpoint,
            headers=headers
        )
        
        endpoint_results.append({
            "name": name,
            "endpoint": endpoint,
            "success": success,
            "details": details,
            "response_data": response_data
        })
        
        if success and response_data:
            print(f"      ✅ {name} endpoint responding")
            
            # Special check for bot-integration endpoint
            if endpoint == "/admin/profit/bot-integration":
                print(f"         🔍 Checking bot-integration response structure...")
                
                # Check for required fields
                required_fields = ["bot_stats", "efficiency", "recent_transactions"]
                legacy_fields = ["creation_modes", "behaviors"]
                
                has_required = all(field in response_data for field in required_fields)
                has_legacy = any(field in response_data for field in legacy_fields)
                
                if has_required and not has_legacy:
                    print(f"         ✅ Perfect structure: has {required_fields}, no legacy fields")
                elif has_required and has_legacy:
                    print(f"         ⚠️ Has required fields but also legacy fields: {[f for f in legacy_fields if f in response_data]}")
                elif not has_required and not has_legacy:
                    print(f"         ❌ Missing required fields: {[f for f in required_fields if f not in response_data]}")
                else:
                    print(f"         ❌ Missing required fields and has legacy fields")
                
                # Store additional info for this endpoint
                endpoint_results[-1]["has_required_fields"] = has_required
                endpoint_results[-1]["has_legacy_fields"] = has_legacy
                endpoint_results[-1]["required_fields"] = required_fields
                endpoint_results[-1]["legacy_fields"] = legacy_fields
        else:
            print(f"      ❌ {name} endpoint failed: {details}")
    
    # Evaluate overall results
    successful_endpoints = sum(1 for result in endpoint_results if result["success"])
    total_endpoints = len(endpoint_results)
    
    # Special evaluation for bot-integration
    bot_integration_result = next((r for r in endpoint_results if r["endpoint"] == "/admin/profit/bot-integration"), None)
    bot_integration_perfect = False
    
    if bot_integration_result and bot_integration_result["success"]:
        bot_integration_perfect = (
            bot_integration_result.get("has_required_fields", False) and 
            not bot_integration_result.get("has_legacy_fields", True)
        )
    
    if successful_endpoints == total_endpoints and bot_integration_perfect:
        record_test(
            "Admin Profit Endpoints",
            True,
            f"All {total_endpoints} profit endpoints working with correct structure (no legacy fields)"
        )
    elif successful_endpoints == total_endpoints:
        record_test(
            "Admin Profit Endpoints",
            False,
            f"All endpoints responding but bot-integration has structural issues (legacy fields present)"
        )
    else:
        failed_endpoints = [result["name"] for result in endpoint_results if not result["success"]]
        record_test(
            "Admin Profit Endpoints",
            False,
            f"Only {successful_endpoints}/{total_endpoints} endpoints working. Failed: {failed_endpoints}"
        )
    
    return endpoint_results

def test_lobby_endpoints_unaffected():
    """Test 4: Verify lobby endpoints are unaffected"""
    print(f"\n{Colors.MAGENTA}🧪 Test 4: Testing Lobby Endpoints (Unaffected Check){Colors.END}")
    
    # First authenticate as admin for protected endpoints
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("Lobby Endpoints Unaffected", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    lobby_endpoints = [
        ("/games/available", "Available Games"),
        ("/games/active-human-bots", "Active Human-Bot Games"),
        ("/bots/active-games", "Active Bot Games"),
        ("/bots/ongoing-games", "Ongoing Bot Games")
    ]
    
    endpoint_results = []
    
    for endpoint, name in lobby_endpoints:
        print(f"   📝 Testing GET {endpoint}...")
        
        success, response_data, details = make_request(
            "GET",
            endpoint,
            headers=headers
        )
        
        endpoint_results.append({
            "name": name,
            "endpoint": endpoint,
            "success": success,
            "details": details,
            "response_data": response_data
        })
        
        if success:
            # Count games/bots returned
            games_count = 0
            if isinstance(response_data, list):
                games_count = len(response_data)
            elif isinstance(response_data, dict) and "games" in response_data:
                games_count = len(response_data["games"])
            elif isinstance(response_data, dict) and "bots" in response_data:
                games_count = len(response_data["bots"])
            
            print(f"      ✅ {name} endpoint working ({games_count} items returned)")
        else:
            print(f"      ❌ {name} endpoint failed: {details}")
    
    # Evaluate results
    successful_endpoints = sum(1 for result in endpoint_results if result["success"])
    total_endpoints = len(endpoint_results)
    
    if successful_endpoints == total_endpoints:
        record_test(
            "Lobby Endpoints Unaffected",
            True,
            f"All {total_endpoints} lobby endpoints working correctly (unaffected by changes)"
        )
    else:
        failed_endpoints = [result["name"] for result in endpoint_results if not result["success"]]
        record_test(
            "Lobby Endpoints Unaffected",
            False,
            f"Only {successful_endpoints}/{total_endpoints} lobby endpoints working. Failed: {failed_endpoints}"
        )
    
    return endpoint_results

def print_current_profit_summary():
    """Print current_profit testing specific summary"""
    print_header("CURRENT PROFIT FIELD TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 CURRENT PROFIT REQUIREMENTS STATUS:{Colors.END}")
    
    # Check each requirement
    current_profit_test = next((test for test in test_results["tests"] if "current_profit field" in test["name"]), None)
    individual_endpoints_test = next((test for test in test_results["tests"] if "Individual Endpoints" in test["name"]), None)
    profit_endpoints_test = next((test for test in test_results["tests"] if "Profit Endpoints" in test["name"]), None)
    lobby_endpoints_test = next((test for test in test_results["tests"] if "Lobby Endpoints" in test["name"]), None)
    
    requirements = [
        ("1. current_profit field in Regular Bots List", current_profit_test),
        ("2. Individual Regular Bot Endpoints", individual_endpoints_test),
        ("3. Admin Profit Endpoints (no legacy fields)", profit_endpoints_test),
        ("4. Lobby Endpoints Unaffected", lobby_endpoints_test)
    ]
    
    for req_name, test in requirements:
        if test:
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
            print(f"   {req_name}: {status}")
            if test["details"]:
                print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
        else:
            print(f"   {req_name}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    print(f"\n{Colors.BOLD}🔍 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅{Colors.END}" if test["success"] else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Overall conclusion
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: ALL CURRENT PROFIT REQUIREMENTS WORKING!{Colors.END}")
        print(f"{Colors.GREEN}✅ current_profit field present and valid in all bots{Colors.END}")
        print(f"{Colors.GREEN}✅ All individual Regular Bot endpoints working{Colors.END}")
        print(f"{Colors.GREEN}✅ Admin Profit endpoints working without legacy fields{Colors.END}")
        print(f"{Colors.GREEN}✅ Lobby endpoints unaffected by changes{Colors.END}")
    elif success_rate >= 75:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: MOST REQUIREMENTS MET ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Most current_profit requirements working, minor issues remain.{Colors.END}")
    elif success_rate >= 50:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL SUCCESS ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.YELLOW}Some current_profit requirements working, additional work needed.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: CRITICAL ISSUES REMAIN ({success_rate:.1f}% functional){Colors.END}")
        print(f"{Colors.RED}Most current_profit requirements NOT working. Urgent fixes needed.{Colors.END}")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    if current_profit_test and not current_profit_test["success"]:
        print(f"   🔴 Add current_profit field to Regular Bots List API response")
    if individual_endpoints_test and not individual_endpoints_test["success"]:
        print(f"   🔴 Fix individual Regular Bot endpoints")
    if profit_endpoints_test and not profit_endpoints_test["success"]:
        print(f"   🔴 Remove legacy creation_modes/behaviors from Admin Profit endpoints")
    if lobby_endpoints_test and not lobby_endpoints_test["success"]:
        print(f"   🔴 Fix lobby endpoints that were affected by changes")
    
    if success_rate == 100:
        print(f"   🟢 All current_profit requirements met - system ready")
        print(f"   ✅ Main agent can summarize and finish")
    else:
        print(f"   🔧 Fix remaining current_profit issues before completion")

def main():
    """Main test execution for current_profit field testing"""
    print_header("CURRENT PROFIT FIELD TESTING")
    print(f"{Colors.BLUE}🎯 Testing current_profit field and related endpoints{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test 1: current_profit field in Regular Bots List
        bots = test_regular_bots_list_current_profit()
        
        # Test 2: Individual Regular Bot endpoints
        test_regular_bot_individual_endpoints(bots)
        
        # Test 3: Admin Profit endpoints
        test_admin_profit_endpoints()
        
        # Test 4: Lobby endpoints unaffected
        test_lobby_endpoints_unaffected()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_current_profit_summary()

if __name__ == "__main__":
    main()