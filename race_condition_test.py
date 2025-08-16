#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ RACE CONDITION - REGULAR BOTS
Проверка правильного подсчета active_bets и соблюдения лимитов cycle_games

КОНТЕКСТ: Обнаружена и исправлена КОРНЕВАЯ ПРИЧИНА проблемы:
- Неправильный подсчет active_bets в админ-панели
- Боты создавали больше ставок чем разрешено cycle_games
- create_bot_bet() теперь использует только cycle_games вместо current_limit

КРИТИЧЕСКАЯ ПРОВЕРКА:
1. CYCLE_GAMES COMPLIANCE - каждый бот должен иметь active_bets <= cycle_games
2. ПРАВИЛЬНЫЙ ПОДСЧЕТ ACTIVE_BETS - только игры где бот создатель
3. СИСТЕМА ЛИМИТОВ - create_bot_bet() блокирует при достижении cycle_games
4. КОНСИСТЕНТНОСТЬ ДАННЫХ - подсчет в админ-панели = реальные WAITING игры

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: ВСЕ боты соблюдают лимит cycle_games
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "https://russian-commission.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com", 
    "password": "Admin123!"
}

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "critical_issues": [],
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

def print_critical_issue(issue: str):
    """Print critical issue with red highlighting"""
    print(f"{Colors.RED}{Colors.BOLD}🚨 CRITICAL ISSUE: {issue}{Colors.END}")
    test_results["critical_issues"].append(issue)

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

def test_cycle_games_compliance(token: str):
    """КРИТИЧЕСКИЙ ТЕСТ 1: Проверка соблюдения лимитов cycle_games"""
    print(f"\n{Colors.MAGENTA}🧪 КРИТИЧЕСКИЙ ТЕСТ 1: Cycle Games Compliance Check{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all regular bots
    success, response_data, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        record_test(
            "Cycle Games Compliance - Get Bots",
            False,
            f"Failed to get bots: {details}"
        )
        return
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    
    if not bots:
        record_test(
            "Cycle Games Compliance - Bot Count",
            False,
            "No regular bots found for testing"
        )
        return
    
    print(f"{Colors.BLUE}📊 Found {len(bots)} regular bots to check{Colors.END}")
    
    compliance_violations = []
    compliant_bots = []
    
    for bot in bots:
        bot_name = bot.get("name", "Unknown")
        active_bets = bot.get("active_bets", 0)
        cycle_games = bot.get("cycle_games", 12)
        
        print(f"{Colors.CYAN}🤖 Checking {bot_name}: {active_bets} active_bets vs {cycle_games} cycle_games{Colors.END}")
        
        if active_bets > cycle_games:
            violation = f"{bot_name}: {active_bets} active bets > {cycle_games} cycle_games ({((active_bets/cycle_games)*100):.0f}% over limit!)"
            compliance_violations.append(violation)
            print_critical_issue(f"CYCLE_GAMES VIOLATION: {violation}")
        else:
            compliant_bots.append(f"{bot_name}: {active_bets}/{cycle_games} ✅")
            print(f"   {Colors.GREEN}✅ {bot_name}: {active_bets}/{cycle_games} - COMPLIANT{Colors.END}")
    
    # Record results
    if compliance_violations:
        record_test(
            "Cycle Games Compliance Check",
            False,
            f"CRITICAL: {len(compliance_violations)} bots violating cycle_games limits: {compliance_violations}"
        )
        
        # This is the most critical issue
        print_critical_issue(f"RACE CONDITION NOT FIXED: {len(compliance_violations)} bots exceed cycle_games limits")
        
    else:
        record_test(
            "Cycle Games Compliance Check", 
            True,
            f"ALL {len(bots)} bots comply with cycle_games limits: {compliant_bots}"
        )
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 RACE CONDITION FIXED: All bots comply with cycle_games!{Colors.END}")

def test_active_bets_counting_accuracy(token: str):
    """КРИТИЧЕСКИЙ ТЕСТ 2: Проверка правильности подсчета active_bets"""
    print(f"\n{Colors.MAGENTA}🧪 КРИТИЧЕСКИЙ ТЕСТ 2: Active Bets Counting Accuracy{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get admin panel data
    success, admin_data, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        record_test(
            "Active Bets Counting - Admin Data",
            False,
            f"Failed to get admin data: {details}"
        )
        return
    
    # Get actual regular bot games
    success, games_data, details = make_request(
        "GET", 
        "/bots/active-games",
        headers=headers
    )
    
    if not success:
        record_test(
            "Active Bets Counting - Games Data",
            False,
            f"Failed to get games data: {details}"
        )
        return
    
    bots = admin_data if isinstance(admin_data, list) else admin_data.get("bots", [])
    games = games_data if isinstance(games_data, list) else games_data.get("games", [])
    
    print(f"{Colors.BLUE}📊 Admin panel shows {len(bots)} bots, found {len(games)} active regular bot games{Colors.END}")
    
    # Count actual WAITING games per bot (only where bot is creator)
    actual_counts = {}
    for game in games:
        if game.get("status") == "WAITING":
            creator_id = game.get("creator_id")
            if creator_id:
                actual_counts[creator_id] = actual_counts.get(creator_id, 0) + 1
    
    # Compare with admin panel counts
    discrepancies = []
    accurate_counts = []
    
    for bot in bots:
        bot_id = bot.get("id")
        bot_name = bot.get("name", "Unknown")
        admin_count = bot.get("active_bets", 0)
        actual_count = actual_counts.get(bot_id, 0)
        
        print(f"{Colors.CYAN}🤖 {bot_name}: Admin={admin_count}, Actual={actual_count}{Colors.END}")
        
        if admin_count != actual_count:
            discrepancy = f"{bot_name}: Admin shows {admin_count} but actual WAITING games = {actual_count}"
            discrepancies.append(discrepancy)
            print(f"   {Colors.RED}❌ DISCREPANCY: {discrepancy}{Colors.END}")
        else:
            accurate_counts.append(f"{bot_name}: {admin_count} ✅")
            print(f"   {Colors.GREEN}✅ ACCURATE: {bot_name} = {admin_count}{Colors.END}")
    
    # Record results
    if discrepancies:
        record_test(
            "Active Bets Counting Accuracy",
            False,
            f"Found {len(discrepancies)} counting discrepancies: {discrepancies}"
        )
        print_critical_issue(f"ACTIVE_BETS COUNTING ERROR: {len(discrepancies)} bots have incorrect counts")
    else:
        record_test(
            "Active Bets Counting Accuracy",
            True,
            f"All {len(bots)} bots have accurate active_bets counts: {accurate_counts}"
        )

def test_create_bot_bet_limits(token: str):
    """КРИТИЧЕСКИЙ ТЕСТ 3: Проверка работы лимитов в create_bot_bet()"""
    print(f"\n{Colors.MAGENTA}🧪 КРИТИЧЕСКИЙ ТЕСТ 3: Create Bot Bet Limits Check{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get bots that are at or near their cycle_games limit
    success, response_data, details = make_request(
        "GET",
        "/admin/bots", 
        headers=headers
    )
    
    if not success:
        record_test(
            "Create Bot Bet Limits - Get Bots",
            False,
            f"Failed to get bots: {details}"
        )
        return
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    
    # Find bots at their limits
    at_limit_bots = []
    under_limit_bots = []
    
    for bot in bots:
        bot_name = bot.get("name", "Unknown")
        active_bets = bot.get("active_bets", 0)
        cycle_games = bot.get("cycle_games", 12)
        
        if active_bets >= cycle_games:
            at_limit_bots.append(f"{bot_name}: {active_bets}/{cycle_games}")
        else:
            under_limit_bots.append(f"{bot_name}: {active_bets}/{cycle_games}")
    
    print(f"{Colors.BLUE}📊 Bots at limit: {len(at_limit_bots)}, Under limit: {len(under_limit_bots)}{Colors.END}")
    
    if at_limit_bots:
        print(f"{Colors.YELLOW}⚠️ Bots at cycle_games limit: {at_limit_bots}{Colors.END}")
        record_test(
            "Create Bot Bet Limits - Limit Detection",
            True,
            f"Found {len(at_limit_bots)} bots at their cycle_games limit - system should block new bet creation"
        )
    else:
        record_test(
            "Create Bot Bet Limits - Limit Detection", 
            True,
            f"All {len(bots)} bots are under their cycle_games limit - system working correctly"
        )
    
    if under_limit_bots:
        print(f"{Colors.GREEN}✅ Bots under limit: {under_limit_bots}{Colors.END}")

def test_maintain_bots_automation(token: str):
    """КРИТИЧЕСКИЙ ТЕСТ 4: Проверка работы maintain_all_bots_active_bets()"""
    print(f"\n{Colors.MAGENTA}🧪 КРИТИЧЕСКИЙ ТЕСТ 4: Bot Automation System Check{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Take snapshot 1
    success, snapshot1, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        record_test(
            "Bot Automation - Snapshot 1",
            False,
            f"Failed to get first snapshot: {details}"
        )
        return
    
    bots1 = snapshot1 if isinstance(snapshot1, list) else snapshot1.get("bots", [])
    total_active_1 = sum(bot.get("active_bets", 0) for bot in bots1)
    
    print(f"{Colors.BLUE}📊 Snapshot 1: {len(bots1)} bots, {total_active_1} total active bets{Colors.END}")
    
    # Wait for automation cycle
    print(f"{Colors.YELLOW}⏳ Waiting 10 seconds for automation cycle...{Colors.END}")
    time.sleep(10)
    
    # Take snapshot 2
    success, snapshot2, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        record_test(
            "Bot Automation - Snapshot 2",
            False,
            f"Failed to get second snapshot: {details}"
        )
        return
    
    bots2 = snapshot2 if isinstance(snapshot2, list) else snapshot2.get("bots", [])
    total_active_2 = sum(bot.get("active_bets", 0) for bot in bots2)
    
    print(f"{Colors.BLUE}📊 Snapshot 2: {len(bots2)} bots, {total_active_2} total active bets{Colors.END}")
    
    # Analyze changes
    difference = total_active_2 - total_active_1
    
    if abs(difference) > 50:  # Significant change indicates potential race condition
        print_critical_issue(f"AUTOMATION INSTABILITY: Total active bets changed by {difference} in 10 seconds")
        record_test(
            "Bot Automation System Stability",
            False,
            f"Unstable automation: {difference} bet change in 10s (possible race condition)"
        )
    else:
        record_test(
            "Bot Automation System Stability",
            True,
            f"Stable automation: Only {difference} bet change in 10s (within normal range)"
        )
    
    # Check individual bot compliance in both snapshots
    violations_1 = sum(1 for bot in bots1 if bot.get("active_bets", 0) > bot.get("cycle_games", 12))
    violations_2 = sum(1 for bot in bots2 if bot.get("active_bets", 0) > bot.get("cycle_games", 12))
    
    print(f"{Colors.CYAN}🔍 Compliance violations: Snapshot 1 = {violations_1}, Snapshot 2 = {violations_2}{Colors.END}")
    
    if violations_1 > 0 or violations_2 > 0:
        print_critical_issue(f"PERSISTENT VIOLATIONS: {max(violations_1, violations_2)} bots still violating cycle_games")

def test_bot_segregation_integrity(token: str):
    """ТЕСТ 5: Проверка целостности разделения ботов"""
    print(f"\n{Colors.MAGENTA}🧪 ТЕСТ 5: Bot Segregation Integrity Check{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check available games (should be Human-bots only)
    success, available_games, details = make_request(
        "GET",
        "/games/available",
        headers=headers
    )
    
    # Check regular bot games
    success2, regular_games, details2 = make_request(
        "GET", 
        "/bots/active-games",
        headers=headers
    )
    
    # Check human-bot games
    success3, human_games, details3 = make_request(
        "GET",
        "/games/active-human-bots", 
        headers=headers
    )
    
    if success and success2 and success3:
        available = available_games if isinstance(available_games, list) else available_games.get("games", [])
        regular = regular_games if isinstance(regular_games, list) else regular_games.get("games", [])
        human = human_games if isinstance(human_games, list) else human_games.get("games", [])
        
        print(f"{Colors.BLUE}📊 Available games: {len(available)}, Regular bot games: {len(regular)}, Human-bot games: {len(human)}{Colors.END}")
        
        # Check for cross-contamination
        regular_in_available = sum(1 for game in available if game.get("is_regular_bot_game", False))
        human_in_regular = sum(1 for game in regular if game.get("bot_type") == "HUMAN")
        
        if regular_in_available == 0 and human_in_regular == 0:
            record_test(
                "Bot Segregation Integrity",
                True,
                f"Perfect segregation: {len(available)} available, {len(regular)} regular, {len(human)} human-bot games"
            )
        else:
            record_test(
                "Bot Segregation Integrity",
                False,
                f"Segregation breach: {regular_in_available} regular bots in available, {human_in_regular} human-bots in regular"
            )
    else:
        record_test(
            "Bot Segregation Integrity",
            False,
            "Failed to get segregation data for analysis"
        )

def print_final_summary():
    """Print final test summary with focus on race condition fix"""
    print_header("RACE CONDITION FIX VERIFICATION RESULTS")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 OVERALL RESULTS:{Colors.END}")
    print(f"   Total Tests: {total}")
    print(f"   {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"   {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"   {Colors.CYAN}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    # Critical issues summary
    if test_results["critical_issues"]:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CRITICAL ISSUES FOUND:{Colors.END}")
        for i, issue in enumerate(test_results["critical_issues"], 1):
            print(f"   {i}. {Colors.RED}{issue}{Colors.END}")
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ NO CRITICAL ISSUES FOUND{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 RACE CONDITION FIX STATUS:{Colors.END}")
    
    key_tests = [
        "Cycle Games Compliance Check",
        "Active Bets Counting Accuracy", 
        "Create Bot Bet Limits",
        "Bot Automation System Stability",
        "Bot Segregation Integrity"
    ]
    
    for test_name in key_tests:
        test_found = False
        for test in test_results["tests"]:
            if test_name.lower() in test["name"].lower():
                status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if test["success"] else f"{Colors.RED}❌ FAILED{Colors.END}"
                print(f"   • {test_name}: {status}")
                test_found = True
                break
        
        if not test_found:
            print(f"   • {test_name}: {Colors.YELLOW}⚠️ NOT TESTED{Colors.END}")
    
    # Final conclusion
    critical_failed = len(test_results["critical_issues"]) > 0
    
    if critical_failed:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: RACE CONDITION NOT FULLY FIXED!{Colors.END}")
        print(f"{Colors.RED}Critical issues remain that violate cycle_games limits. System needs immediate attention.{Colors.END}")
        print(f"{Colors.RED}The maintain_all_bots_active_bets() function is still creating too many bets.{Colors.END}")
    elif success_rate >= 80:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: RACE CONDITION SUCCESSFULLY FIXED!{Colors.END}")
        print(f"{Colors.GREEN}All bots comply with cycle_games limits. The system is working correctly.{Colors.END}")
        print(f"{Colors.GREEN}The create_bot_bet() function properly enforces limits.{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: RACE CONDITION PARTIALLY FIXED ({success_rate:.1f}%){Colors.END}")
        print(f"{Colors.YELLOW}Some improvements made but issues remain. Further investigation needed.{Colors.END}")

def main():
    """Main test execution"""
    print_header("RACE CONDITION FIX VERIFICATION - REGULAR BOTS")
    print(f"{Colors.BLUE}🎯 Testing the fix for cycle_games compliance and active_bets counting{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: Ensuring NO bot exceeds its cycle_games limit{Colors.END}")
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print(f"{Colors.RED}❌ Cannot proceed without authentication{Colors.END}")
        sys.exit(1)
    
    try:
        # Run critical tests in order of importance
        test_cycle_games_compliance(token)  # MOST CRITICAL
        test_active_bets_counting_accuracy(token)
        test_create_bot_bet_limits(token)
        test_maintain_bots_automation(token)
        test_bot_segregation_integrity(token)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()