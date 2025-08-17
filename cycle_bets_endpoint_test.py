#!/usr/bin/env python3
"""
RUSSIAN REVIEW TESTING - Extended GET /api/admin/bots/{bot_id}/cycle-bets Endpoint
Протестировать расширенный эндпоинт GET /api/admin/bots/{bot_id}/cycle-bets

ЦЕЛЬ: убедиться, что теперь он возвращает:
- sums: wins_sum, losses_sum, draws_sum, total_sum, active_pool, profit, roi_active
- counts: wins_count, losses_count, draws_count, total_count
- breakdown: wins[], losses[], draws[] (целочисленные ставки)
- cycle_length и exact_cycle_total

ШАГИ:
1) Логин админом (admin@gemplay.com / Admin123!)
2) Создать regular бота c INT-параметрами (min=1, max=100, cycle=16, 6/6/4, проценты 44/36/20) через POST /api/admin/bots/create-regular
3) Подождать 15 секунд пока сформируется цикл
4) Вызвать GET /api/admin/bots/{bot_id}/cycle-bets и проверить:
   - sums.total_sum == sums.wins_sum + sums.losses_sum + sums.draws_sum
   - roi_active == (wins_sum - losses_sum)/(wins_sum + losses_sum)*100 (с точностью 0.01)
   - counts соответствуют длинам массивов breakdown
   - Все ставки в breakdown лежат в [1..100] и целые
   - cycle_length == 16
   - exact_cycle_total == 808
Вывести отчет PASSED/FAILED по каждому условию.
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
BASE_URL = "https://modalni-dialogi.preview.emergentagent.com/api"
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

def create_regular_bot_with_int_parameters(admin_token: str) -> Optional[str]:
    """Step 2: Создать regular бота c INT-параметрами"""
    print(f"\n{Colors.MAGENTA}🧪 Step 2: Creating Regular Bot with INT Parameters{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create Regular bot with EXACT INT settings from Russian review
    bot_data = {
        "name": "CycleBets_Test_Bot",
        "min_bet_amount": 1,      # INT parameter
        "max_bet_amount": 100,    # INT parameter  
        "cycle_games": 16,        # INT parameter
        "wins_count": 6,          # Balance games - wins
        "losses_count": 6,        # Balance games - losses
        "draws_count": 4,         # Balance games - draws
        "wins_percentage": 44.0,  # Percentage outcomes - wins
        "losses_percentage": 36.0, # Percentage outcomes - losses
        "draws_percentage": 20.0,  # Percentage outcomes - draws
        "pause_between_cycles": 5,
        "pause_on_draw": 1,
        "profit_strategy": "balanced",
        "creation_mode": "queue-based"
    }
    
    print(f"   📝 Creating Regular bot 'CycleBets_Test_Bot'")
    print(f"   📊 INT Parameters: min=1, max=100, cycle=16, 6/6/4, percentages 44/36/20")
    
    # Create the bot
    success, response_data, details = make_request(
        "POST",
        "/admin/bots/create-regular",
        headers=headers,
        data=bot_data
    )
    
    if not success or not response_data:
        record_test(
            "Regular Bot Creation with INT Parameters",
            False,
            f"Failed to create Regular bot: {details}"
        )
        return None
    
    bot_id = response_data.get("bot_id")
    if not bot_id:
        record_test(
            "Regular Bot Creation with INT Parameters",
            False,
            "Bot created but no bot_id returned"
        )
        return None
    
    print(f"   ✅ Regular bot created successfully with ID: {bot_id}")
    record_test(
        "Regular Bot Creation with INT Parameters",
        True,
        f"Bot created with ID: {bot_id}, INT params: min=1, max=100, cycle=16"
    )
    
    return bot_id

def wait_for_cycle_formation():
    """Step 3: Подождать 15 секунд пока сформируется цикл"""
    print(f"\n{Colors.MAGENTA}🧪 Step 3: Waiting for Cycle Formation{Colors.END}")
    print(f"   ⏳ Waiting 15 seconds for cycle formation as specified in Russian review...")
    
    for i in range(15, 0, -1):
        print(f"   ⏰ {i} seconds remaining...", end='\r')
        time.sleep(1)
    
    print(f"   ✅ 15 second wait completed - cycle should be formed")
    record_test(
        "Cycle Formation Wait",
        True,
        "Waited 15 seconds for cycle formation as per Russian review requirements"
    )

def test_extended_cycle_bets_endpoint(admin_token: str, bot_id: str):
    """Step 4: Вызвать GET /api/admin/bots/{bot_id}/cycle-bets и проверить все условия"""
    print(f"\n{Colors.MAGENTA}🧪 Step 4: Testing Extended GET /api/admin/bots/{bot_id}/cycle-bets Endpoint{Colors.END}")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Call the extended cycle-bets endpoint
    success, response_data, details = make_request(
        "GET",
        f"/admin/bots/{bot_id}/cycle-bets",
        headers=headers
    )
    
    if not success or not response_data:
        record_test(
            "Extended Cycle-Bets Endpoint Call",
            False,
            f"Failed to call cycle-bets endpoint: {details}"
        )
        return
    
    print(f"   ✅ Successfully called GET /api/admin/bots/{bot_id}/cycle-bets")
    print(f"   📊 Response structure analysis:")
    
    # Check response structure
    has_sums = "sums" in response_data
    has_counts = "counts" in response_data
    has_breakdown = "breakdown" in response_data
    has_cycle_length = "cycle_length" in response_data
    has_exact_cycle_total = "exact_cycle_total" in response_data
    
    print(f"      - Has 'sums' section: {has_sums}")
    print(f"      - Has 'counts' section: {has_counts}")
    print(f"      - Has 'breakdown' section: {has_breakdown}")
    print(f"      - Has 'cycle_length' field: {has_cycle_length}")
    print(f"      - Has 'exact_cycle_total' field: {has_exact_cycle_total}")
    
    if not all([has_sums, has_counts, has_breakdown, has_cycle_length, has_exact_cycle_total]):
        record_test(
            "Extended Cycle-Bets Endpoint Structure",
            False,
            f"Missing required fields in response structure"
        )
        return
    
    record_test(
        "Extended Cycle-Bets Endpoint Structure",
        True,
        "All required fields present: sums, counts, breakdown, cycle_length, exact_cycle_total"
    )
    
    # Extract data for detailed testing
    sums = response_data.get("sums", {})
    counts = response_data.get("counts", {})
    breakdown = response_data.get("breakdown", {})
    cycle_length = response_data.get("cycle_length")
    exact_cycle_total = response_data.get("exact_cycle_total")
    
    # Test 4.1: Check sums section
    test_sums_section(sums)
    
    # Test 4.2: Check counts section
    test_counts_section(counts, breakdown)
    
    # Test 4.3: Check breakdown section
    test_breakdown_section(breakdown)
    
    # Test 4.4: Check cycle_length
    test_cycle_length(cycle_length)
    
    # Test 4.5: Check exact_cycle_total
    test_exact_cycle_total(exact_cycle_total)
    
    # Test 4.6: Check ROI calculation
    test_roi_calculation(sums)

def test_sums_section(sums: Dict):
    """Test 4.1: sums.total_sum == sums.wins_sum + sums.losses_sum + sums.draws_sum"""
    print(f"\n   🔍 Test 4.1: Sums Section Validation")
    
    required_sum_fields = ["wins_sum", "losses_sum", "draws_sum", "total_sum", "active_pool", "profit", "roi_active"]
    missing_fields = [field for field in required_sum_fields if field not in sums]
    
    if missing_fields:
        record_test(
            "Sums Section - Required Fields",
            False,
            f"Missing required sum fields: {missing_fields}"
        )
        return
    
    wins_sum = sums.get("wins_sum", 0)
    losses_sum = sums.get("losses_sum", 0)
    draws_sum = sums.get("draws_sum", 0)
    total_sum = sums.get("total_sum", 0)
    
    calculated_total = wins_sum + losses_sum + draws_sum
    is_total_correct = abs(total_sum - calculated_total) < 0.01
    
    print(f"      wins_sum: {wins_sum}")
    print(f"      losses_sum: {losses_sum}")
    print(f"      draws_sum: {draws_sum}")
    print(f"      total_sum: {total_sum}")
    print(f"      calculated_total: {calculated_total}")
    print(f"      active_pool: {sums.get('active_pool', 'N/A')}")
    print(f"      profit: {sums.get('profit', 'N/A')}")
    print(f"      roi_active: {sums.get('roi_active', 'N/A')}")
    
    if is_total_correct:
        record_test(
            "Sums Section - Total Sum Calculation",
            True,
            f"total_sum ({total_sum}) == wins_sum + losses_sum + draws_sum ({calculated_total})"
        )
    else:
        record_test(
            "Sums Section - Total Sum Calculation",
            False,
            f"total_sum ({total_sum}) != wins_sum + losses_sum + draws_sum ({calculated_total})"
        )

def test_counts_section(counts: Dict, breakdown: Dict):
    """Test 4.2: counts соответствуют длинам массивов breakdown"""
    print(f"\n   🔍 Test 4.2: Counts Section Validation")
    
    required_count_fields = ["wins_count", "losses_count", "draws_count", "total_count"]
    missing_fields = [field for field in required_count_fields if field not in counts]
    
    if missing_fields:
        record_test(
            "Counts Section - Required Fields",
            False,
            f"Missing required count fields: {missing_fields}"
        )
        return
    
    wins_count = counts.get("wins_count", 0)
    losses_count = counts.get("losses_count", 0)
    draws_count = counts.get("draws_count", 0)
    total_count = counts.get("total_count", 0)
    
    # Check breakdown arrays
    wins_array = breakdown.get("wins", [])
    losses_array = breakdown.get("losses", [])
    draws_array = breakdown.get("draws", [])
    
    wins_length = len(wins_array)
    losses_length = len(losses_array)
    draws_length = len(draws_array)
    calculated_total_count = wins_length + losses_length + draws_length
    
    print(f"      wins_count: {wins_count} (breakdown length: {wins_length})")
    print(f"      losses_count: {losses_count} (breakdown length: {losses_length})")
    print(f"      draws_count: {draws_count} (breakdown length: {draws_length})")
    print(f"      total_count: {total_count} (calculated: {calculated_total_count})")
    
    # Check if counts match breakdown lengths
    counts_match_breakdown = (
        wins_count == wins_length and
        losses_count == losses_length and
        draws_count == draws_length and
        total_count == calculated_total_count
    )
    
    if counts_match_breakdown:
        record_test(
            "Counts Section - Breakdown Length Match",
            True,
            f"All counts match breakdown array lengths: wins={wins_count}, losses={losses_count}, draws={draws_count}, total={total_count}"
        )
    else:
        record_test(
            "Counts Section - Breakdown Length Match",
            False,
            f"Counts don't match breakdown lengths: wins={wins_count}≠{wins_length}, losses={losses_count}≠{losses_length}, draws={draws_count}≠{draws_length}"
        )

def test_breakdown_section(breakdown: Dict):
    """Test 4.3: Все ставки в breakdown лежат в [1..100] и целые"""
    print(f"\n   🔍 Test 4.3: Breakdown Section Validation")
    
    required_breakdown_fields = ["wins", "losses", "draws"]
    missing_fields = [field for field in required_breakdown_fields if field not in breakdown]
    
    if missing_fields:
        record_test(
            "Breakdown Section - Required Fields",
            False,
            f"Missing required breakdown fields: {missing_fields}"
        )
        return
    
    wins_array = breakdown.get("wins", [])
    losses_array = breakdown.get("losses", [])
    draws_array = breakdown.get("draws", [])
    
    all_bets = wins_array + losses_array + draws_array
    
    print(f"      wins array: {wins_array}")
    print(f"      losses array: {losses_array}")
    print(f"      draws array: {draws_array}")
    print(f"      total bets: {len(all_bets)}")
    
    # Check if all bets are integers in range [1..100]
    invalid_bets = []
    for bet in all_bets:
        if not isinstance(bet, int) or bet < 1 or bet > 100:
            invalid_bets.append(bet)
    
    if not invalid_bets:
        record_test(
            "Breakdown Section - Integer Range Validation",
            True,
            f"All {len(all_bets)} bets are integers in range [1..100]"
        )
    else:
        record_test(
            "Breakdown Section - Integer Range Validation",
            False,
            f"Found {len(invalid_bets)} invalid bets (not integers or outside [1..100]): {invalid_bets[:5]}..."
        )

def test_cycle_length(cycle_length):
    """Test 4.4: cycle_length == 16"""
    print(f"\n   🔍 Test 4.4: Cycle Length Validation")
    
    print(f"      cycle_length: {cycle_length}")
    print(f"      expected: 16")
    
    if cycle_length == 16:
        record_test(
            "Cycle Length Validation",
            True,
            f"cycle_length is correct: {cycle_length} == 16"
        )
    else:
        record_test(
            "Cycle Length Validation",
            False,
            f"cycle_length is incorrect: {cycle_length} != 16"
        )

def test_exact_cycle_total(exact_cycle_total):
    """Test 4.5: exact_cycle_total == 808"""
    print(f"\n   🔍 Test 4.5: Exact Cycle Total Validation")
    
    print(f"      exact_cycle_total: {exact_cycle_total}")
    print(f"      expected: 808")
    print(f"      calculation: (1+100)/2 * 16 = 50.5 * 16 = 808")
    
    if exact_cycle_total == 808:
        record_test(
            "Exact Cycle Total Validation",
            True,
            f"exact_cycle_total is correct: {exact_cycle_total} == 808"
        )
    else:
        record_test(
            "Exact Cycle Total Validation",
            False,
            f"exact_cycle_total is incorrect: {exact_cycle_total} != 808"
        )

def test_roi_calculation(sums: Dict):
    """Test 4.6: roi_active == (wins_sum - losses_sum)/(wins_sum + losses_sum)*100 (с точностью 0.01)"""
    print(f"\n   🔍 Test 4.6: ROI Active Calculation Validation")
    
    wins_sum = sums.get("wins_sum", 0)
    losses_sum = sums.get("losses_sum", 0)
    roi_active = sums.get("roi_active", 0)
    
    # Calculate expected ROI
    if wins_sum + losses_sum > 0:
        expected_roi = (wins_sum - losses_sum) / (wins_sum + losses_sum) * 100
    else:
        expected_roi = 0
    
    roi_difference = abs(roi_active - expected_roi)
    is_roi_correct = roi_difference <= 0.01
    
    print(f"      wins_sum: {wins_sum}")
    print(f"      losses_sum: {losses_sum}")
    print(f"      roi_active: {roi_active}")
    print(f"      expected_roi: {expected_roi:.2f}")
    print(f"      difference: {roi_difference:.4f}")
    print(f"      formula: ({wins_sum} - {losses_sum}) / ({wins_sum} + {losses_sum}) * 100")
    
    if is_roi_correct:
        record_test(
            "ROI Active Calculation",
            True,
            f"roi_active ({roi_active}) matches expected calculation ({expected_roi:.2f}) within 0.01 precision"
        )
    else:
        record_test(
            "ROI Active Calculation",
            False,
            f"roi_active ({roi_active}) doesn't match expected calculation ({expected_roi:.2f}), difference: {roi_difference:.4f}"
        )

def print_final_summary():
    """Print final testing summary"""
    print_header("EXTENDED CYCLE-BETS ENDPOINT TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 DETAILED TEST RESULTS:{Colors.END}")
    for test in test_results["tests"]:
        status = f"{Colors.GREEN}✅ PASSED{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
        print(f"   {status} - {test['name']}")
        if test["details"]:
            print(f"      {Colors.YELLOW}{test['details']}{Colors.END}")
    
    # Overall conclusion
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: EXTENDED CYCLE-BETS ENDPOINT IS FULLY FUNCTIONAL!{Colors.END}")
        print(f"{Colors.GREEN}✅ All required fields are present and correctly calculated{Colors.END}")
        print(f"{Colors.GREEN}✅ Sums, counts, breakdown, cycle_length, and exact_cycle_total all working{Colors.END}")
        print(f"{Colors.GREEN}✅ ROI calculation is accurate within required precision{Colors.END}")
    elif success_rate >= 80:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: MOSTLY FUNCTIONAL ({success_rate:.1f}%){Colors.END}")
        print(f"{Colors.YELLOW}Most features working correctly, minor issues detected{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: SIGNIFICANT ISSUES DETECTED ({success_rate:.1f}%){Colors.END}")
        print(f"{Colors.RED}Extended cycle-bets endpoint needs attention{Colors.END}")

def main():
    """Main test execution for Extended Cycle-Bets Endpoint"""
    print_header("EXTENDED GET /api/admin/bots/{bot_id}/cycle-bets ENDPOINT TESTING")
    print(f"{Colors.BLUE}🎯 Testing расширенный эндпоинт GET /api/admin/bots/{{bot_id}}/cycle-bets{Colors.END}")
    print(f"{Colors.BLUE}🌐 Backend URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}📋 Requirements: sums, counts, breakdown, cycle_length=16, exact_cycle_total=808{Colors.END}")
    print(f"{Colors.BLUE}🔑 Using admin@gemplay.com / Admin123! for authorization{Colors.END}")
    
    try:
        # Step 1: Admin authentication
        admin_token = authenticate_admin()
        if not admin_token:
            print(f"{Colors.RED}❌ Cannot proceed without admin authentication{Colors.END}")
            return
        
        # Step 2: Create regular bot with INT parameters
        bot_id = create_regular_bot_with_int_parameters(admin_token)
        if not bot_id:
            print(f"{Colors.RED}❌ Cannot proceed without bot creation{Colors.END}")
            return
        
        # Step 3: Wait for cycle formation
        wait_for_cycle_formation()
        
        # Step 4: Test extended cycle-bets endpoint
        test_extended_cycle_bets_endpoint(admin_token, bot_id)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()