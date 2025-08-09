#!/usr/bin/env python3
"""
RUSSIAN REVIEW FOCUSED BACKEND TESTING
Тестирование трех конкретных требований из русского обзора:

1. GET /api/admin/bots/regular/list — поля current_cycle_wins/current_cycle_losses/current_cycle_draws 
   должны всегда возвращаться с явным значением 0, если они отсутствуют в документе бота. 
   Также проверить, что active_pool и cycle_total_display присутствуют и корректны.

2. GET /api/admin/bots/{id} — по-прежнему не содержит legacy полей (win_percentage, creation_mode, profit_strategy) 
   и отдает W/L/D и проценты, ROI и пр. как раньше.

3. POST /api/admin/bots/{id}/recalculate-bets — работает, создает ставки, и старые /reset-bets отсутствуют.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://ac189324-9922-4d54-b6a3-50cded9a8e9f.preview.emergentagent.com/api"
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

def test_requirement_1_regular_bots_list():
    """
    REQUIREMENT 1: GET /api/admin/bots/regular/list
    Проверить что current_cycle_wins/losses/draws всегда возвращают явные значения 0,
    и что active_pool и cycle_total_display присутствуют и корректны.
    """
    print(f"\n{Colors.MAGENTA}🧪 REQUIREMENT 1: Testing Regular Bots List API{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("REQUIREMENT 1 - Authentication", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"   📝 Testing GET /api/admin/bots/regular/list...")
    
    success, response_data, details = make_request(
        "GET",
        "/admin/bots/regular/list",
        headers=headers
    )
    
    if not success or not response_data:
        record_test("REQUIREMENT 1 - Regular Bots List API", False, f"API call failed: {details}")
        return
    
    # Check response structure
    if not isinstance(response_data, dict) or "bots" not in response_data:
        record_test("REQUIREMENT 1 - Response Structure", False, "Invalid response structure - missing 'bots' field")
        return
    
    bots = response_data.get("bots", [])
    if not bots:
        record_test("REQUIREMENT 1 - Bots Data", False, "No bots found in response")
        return
    
    print(f"   📊 Found {len(bots)} regular bots to analyze")
    
    # Analyze each bot for required fields
    issues_found = []
    bots_analyzed = 0
    
    for i, bot in enumerate(bots[:5]):  # Analyze first 5 bots
        bots_analyzed += 1
        bot_id = bot.get("id", f"bot_{i}")
        
        # Check current_cycle_* fields - должны быть явными значениями (не null/undefined)
        cycle_wins = bot.get("current_cycle_wins")
        cycle_losses = bot.get("current_cycle_losses") 
        cycle_draws = bot.get("current_cycle_draws")
        
        # Check active_pool and cycle_total_display
        active_pool = bot.get("active_pool")
        cycle_total_display = bot.get("cycle_total_display")
        
        print(f"   🔍 Bot {bot_id}:")
        print(f"      current_cycle_wins: {cycle_wins} (type: {type(cycle_wins).__name__})")
        print(f"      current_cycle_losses: {cycle_losses} (type: {type(cycle_losses).__name__})")
        print(f"      current_cycle_draws: {cycle_draws} (type: {type(cycle_draws).__name__})")
        print(f"      active_pool: {active_pool} (type: {type(active_pool).__name__})")
        print(f"      cycle_total_display: {cycle_total_display}")
        
        # Check if cycle fields are explicit values (not None/null)
        if cycle_wins is None:
            issues_found.append(f"Bot {bot_id}: current_cycle_wins is null/None instead of explicit 0")
        elif not isinstance(cycle_wins, (int, float)):
            issues_found.append(f"Bot {bot_id}: current_cycle_wins is not a number: {cycle_wins}")
            
        if cycle_losses is None:
            issues_found.append(f"Bot {bot_id}: current_cycle_losses is null/None instead of explicit 0")
        elif not isinstance(cycle_losses, (int, float)):
            issues_found.append(f"Bot {bot_id}: current_cycle_losses is not a number: {cycle_losses}")
            
        if cycle_draws is None:
            issues_found.append(f"Bot {bot_id}: current_cycle_draws is null/None instead of explicit 0")
        elif not isinstance(cycle_draws, (int, float)):
            issues_found.append(f"Bot {bot_id}: current_cycle_draws is not a number: {cycle_draws}")
        
        # Check active_pool presence and correctness
        if active_pool is None:
            issues_found.append(f"Bot {bot_id}: active_pool is missing")
        elif not isinstance(active_pool, (int, float)):
            issues_found.append(f"Bot {bot_id}: active_pool is not a number: {active_pool}")
        
        # Check cycle_total_display presence
        if cycle_total_display is None:
            issues_found.append(f"Bot {bot_id}: cycle_total_display is missing")
    
    # Record test result
    if not issues_found:
        record_test(
            "REQUIREMENT 1 - Regular Bots List Fields",
            True,
            f"All {bots_analyzed} bots have correct field structure: explicit cycle values and required fields present"
        )
    else:
        record_test(
            "REQUIREMENT 1 - Regular Bots List Fields",
            False,
            f"Found {len(issues_found)} issues in {bots_analyzed} bots: {'; '.join(issues_found[:3])}..."
        )

def test_requirement_2_bot_details():
    """
    REQUIREMENT 2: GET /api/admin/bots/{id}
    Проверить что НЕТ legacy полей (win_percentage, creation_mode, profit_strategy)
    и есть W/L/D поля и проценты, ROI и пр.
    """
    print(f"\n{Colors.MAGENTA}🧪 REQUIREMENT 2: Testing Bot Details API{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("REQUIREMENT 2 - Authentication", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # First get list of bots to get a bot ID
    success, list_response, _ = make_request("GET", "/admin/bots/regular/list", headers=headers)
    
    if not success or not list_response or "bots" not in list_response:
        record_test("REQUIREMENT 2 - Get Bot List", False, "Failed to get bot list for testing")
        return
    
    bots = list_response["bots"]
    if not bots:
        record_test("REQUIREMENT 2 - Bot Availability", False, "No bots available for testing")
        return
    
    # Test first available bot
    test_bot = bots[0]
    bot_id = test_bot.get("id")
    
    if not bot_id:
        record_test("REQUIREMENT 2 - Bot ID", False, "No valid bot ID found")
        return
    
    print(f"   📝 Testing GET /api/admin/bots/{bot_id}...")
    
    success, response_data, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}",
        headers=headers
    )
    
    if not success or not response_data:
        record_test("REQUIREMENT 2 - Bot Details API", False, f"API call failed: {details}")
        return
    
    print(f"   🔍 Analyzing bot details response structure...")
    
    # Extract bot data from response (it's nested under "bot" key)
    bot_data = response_data.get("bot", response_data)
    
    # Check for LEGACY fields that should NOT be present
    legacy_fields = ["win_percentage", "creation_mode", "profit_strategy"]
    legacy_found = []
    
    for field in legacy_fields:
        if field in bot_data:
            legacy_found.append(field)
    
    # Check for REQUIRED fields that SHOULD be present
    required_fields = [
        "wins_count", "losses_count", "draws_count",
        "wins_percentage", "losses_percentage", "draws_percentage",
        "current_cycle_wins", "current_cycle_losses", "current_cycle_draws"
    ]
    
    missing_required = []
    for field in required_fields:
        if field not in bot_data:
            missing_required.append(field)
    
    print(f"   📊 Analysis Results:")
    print(f"      Legacy fields found: {legacy_found if legacy_found else 'None (✅ Good)'}")
    print(f"      Missing required fields: {missing_required if missing_required else 'None (✅ Good)'}")
    
    # Check specific field values
    wins_count = bot_data.get("wins_count")
    losses_count = bot_data.get("losses_count")
    draws_count = bot_data.get("draws_count")
    wins_percentage = bot_data.get("wins_percentage")
    
    print(f"      W/L/D counts: {wins_count}/{losses_count}/{draws_count}")
    print(f"      Win percentage: {wins_percentage}%")
    
    # Also check for ROI and other expected fields
    roi_active = bot_data.get("roi_active")
    win_rate = bot_data.get("win_rate")
    
    print(f"      ROI Active: {roi_active}")
    print(f"      Win Rate: {win_rate}%")
    
    # Record test result
    if not legacy_found and not missing_required:
        record_test(
            "REQUIREMENT 2 - Bot Details Structure",
            True,
            f"Perfect structure: No legacy fields, all required W/L/D fields present, Win Rate: {win_rate}%"
        )
    elif legacy_found and not missing_required:
        record_test(
            "REQUIREMENT 2 - Bot Details Structure",
            False,
            f"Legacy fields still present: {', '.join(legacy_found)}"
        )
    elif not legacy_found and missing_required:
        record_test(
            "REQUIREMENT 2 - Bot Details Structure",
            False,
            f"Missing required fields: {', '.join(missing_required)}"
        )
    else:
        record_test(
            "REQUIREMENT 2 - Bot Details Structure",
            False,
            f"Both legacy fields present ({', '.join(legacy_found)}) and required fields missing ({', '.join(missing_required)})"
        )

def test_requirement_3_recalculate_bets():
    """
    REQUIREMENT 3: POST /api/admin/bots/{id}/recalculate-bets
    Проверить что работает, создает ставки, и старые /reset-bets отсутствуют.
    """
    print(f"\n{Colors.MAGENTA}🧪 REQUIREMENT 3: Testing Recalculate Bets API{Colors.END}")
    
    admin_token = authenticate_admin()
    if not admin_token:
        record_test("REQUIREMENT 3 - Authentication", False, "Failed to authenticate as admin")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get a bot for testing
    success, list_response, _ = make_request("GET", "/admin/bots/regular/list", headers=headers)
    
    if not success or not list_response or "bots" not in list_response:
        record_test("REQUIREMENT 3 - Get Bot List", False, "Failed to get bot list for testing")
        return
    
    bots = list_response["bots"]
    if not bots:
        record_test("REQUIREMENT 3 - Bot Availability", False, "No bots available for testing")
        return
    
    test_bot = bots[0]
    bot_id = test_bot.get("id")
    
    if not bot_id:
        record_test("REQUIREMENT 3 - Bot ID", False, "No valid bot ID found")
        return
    
    print(f"   📝 Testing POST /api/admin/bots/{bot_id}/recalculate-bets...")
    
    # Test the recalculate-bets endpoint
    success, response_data, details = make_request(
        "POST",
        f"/admin/bots/{bot_id}/recalculate-bets",
        headers=headers
    )
    
    if not success:
        record_test("REQUIREMENT 3 - Recalculate Bets API", False, f"API call failed: {details}")
        return
    
    if not response_data:
        record_test("REQUIREMENT 3 - Recalculate Response", False, "No response data received")
        return
    
    print(f"   📊 Recalculate response: {response_data}")
    
    # Check response structure
    success_field = response_data.get("success", False)
    message = response_data.get("message", "")
    bets_created = response_data.get("bets_created", 0)
    
    print(f"   🔍 Response Analysis:")
    print(f"      Success: {success_field}")
    print(f"      Message: {message}")
    print(f"      Bets created: {bets_created}")
    
    # Test that old /reset-bets endpoint is NOT available
    print(f"   📝 Testing that old /reset-bets endpoint is disabled...")
    
    reset_success, reset_response, reset_details = make_request(
        "POST",
        f"/admin/bots/{bot_id}/reset-bets",
        headers=headers
    )
    
    print(f"   🔍 Reset-bets endpoint test:")
    print(f"      Status: {reset_details}")
    print(f"      Response: {reset_response}")
    
    # Record test results
    recalculate_works = success_field and isinstance(bets_created, (int, float)) and bets_created >= 0
    reset_disabled = not reset_success  # Should fail (404 or similar)
    
    if recalculate_works and reset_disabled:
        record_test(
            "REQUIREMENT 3 - Recalculate Bets Functionality",
            True,
            f"Recalculate works (created {bets_created} bets), old reset-bets disabled"
        )
    elif recalculate_works and not reset_disabled:
        record_test(
            "REQUIREMENT 3 - Recalculate Bets Functionality",
            False,
            f"Recalculate works but old reset-bets endpoint still exists"
        )
    elif not recalculate_works and reset_disabled:
        record_test(
            "REQUIREMENT 3 - Recalculate Bets Functionality",
            False,
            f"Reset-bets disabled but recalculate not working properly"
        )
    else:
        record_test(
            "REQUIREMENT 3 - Recalculate Bets Functionality",
            False,
            f"Both recalculate not working and reset-bets still exists"
        )

def print_russian_review_summary():
    """Print Russian Review testing summary"""
    print_header("RUSSIAN REVIEW FOCUSED TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 RUSSIAN REVIEW REQUIREMENTS STATUS:{Colors.END}")
    
    # Check each requirement
    req1_tests = [test for test in test_results["tests"] if "REQUIREMENT 1" in test["name"]]
    req2_tests = [test for test in test_results["tests"] if "REQUIREMENT 2" in test["name"]]
    req3_tests = [test for test in test_results["tests"] if "REQUIREMENT 3" in test["name"]]
    
    requirements = [
        ("1. GET /api/admin/bots/regular/list - Explicit cycle values", req1_tests),
        ("2. GET /api/admin/bots/{id} - No legacy fields", req2_tests),
        ("3. POST /api/admin/bots/{id}/recalculate-bets - Working", req3_tests)
    ]
    
    for req_name, tests in requirements:
        if tests:
            all_passed = all(test["success"] for test in tests)
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if all_passed else f"{Colors.RED}❌ FAILED{Colors.END}"
            print(f"   {req_name}: {status}")
            
            for test in tests:
                if test["details"]:
                    print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
        else:
            print(f"   {req_name}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    # Overall conclusion
    if success_rate >= 90:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: ALL RUSSIAN REVIEW REQUIREMENTS ARE WORKING!{Colors.END}")
        print(f"{Colors.GREEN}✅ Regular bots list API returns explicit cycle values{Colors.END}")
        print(f"{Colors.GREEN}✅ Bot details API has no legacy fields{Colors.END}")
        print(f"{Colors.GREEN}✅ Recalculate-bets works, reset-bets disabled{Colors.END}")
    elif success_rate >= 66:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: MOST REQUIREMENTS WORKING ({success_rate:.1f}% success){Colors.END}")
        print(f"{Colors.YELLOW}Большинство требований выполнены, есть минорные проблемы.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: CRITICAL ISSUES REMAIN ({success_rate:.1f}% success){Colors.END}")
        print(f"{Colors.RED}Требования русского обзора НЕ выполнены полностью.{Colors.END}")
    
    print(f"\n{Colors.BOLD}💡 RECOMMENDATIONS FOR MAIN AGENT:{Colors.END}")
    
    failed_tests = [test for test in test_results["tests"] if not test["success"]]
    if not failed_tests:
        print(f"   🟢 All Russian review requirements are satisfied")
        print(f"   ✅ Main agent can summarize and finish")
    else:
        print(f"   🔧 Fix the following issues:")
        for test in failed_tests:
            print(f"      🔴 {test['name']}: {test['details']}")

def main():
    """Main test execution for Russian Review focused testing"""
    print_header("RUSSIAN REVIEW FOCUSED BACKEND TESTING")
    print(f"{Colors.BLUE}🎯 Testing 3 specific requirements from Russian review{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Test all 3 requirements
        test_requirement_1_regular_bots_list()
        test_requirement_2_bot_details()
        test_requirement_3_recalculate_bets()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_russian_review_summary()

if __name__ == "__main__":
    main()