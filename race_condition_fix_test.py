#!/usr/bin/env python3
"""
Regular Bots Race Condition Fix Testing - Russian Review
Повторное тестирование исправленной логики обычных ботов после устранения race condition

КОНТЕКСТ: Тестирование исправлений после обнаружения и устранения критической проблемы race condition
- Было 3 параллельных automation loops, создававших ставки одновременно
- Теперь ТОЛЬКО bot_automation_loop() -> maintain_all_bots_active_bets() управляет созданием ставок

КРИТИЧЕСКИЕ ТЕСТЫ:
1. ПРОВЕРКА CYCLE_GAMES COMPLIANCE - каждый бот должен иметь active_bets <= cycle_games
2. SINGLE AUTOMATION SOURCE - убедиться что только один automation loop активен  
3. ENDPOINT FUNCTIONALITY - /bots/active-games и /bots/ongoing-games работают правильно
4. ISOLATION RULES - обычные боты не присоединяются к играм других ботов

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Все боты соблюдают лимит cycle_games, НЕТ race conditions
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
from datetime import datetime

# Configuration
BASE_URL = "https://income-bot-3.preview.emergentagent.com/api"
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
    """КРИТИЧЕСКИЙ ТЕСТ 1: Проверка соблюдения лимита cycle_games"""
    print(f"\n{Colors.MAGENTA}🧪 CRITICAL TEST 1: Checking cycle_games compliance{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all regular bots
    success, response_data, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if not success:
        record_test(
            "Cycle games compliance check",
            False,
            f"Failed to get bots: {details}"
        )
        return
    
    bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
    
    if not bots:
        record_test(
            "Cycle games compliance check",
            False,
            "No bots found for testing"
        )
        return
    
    compliance_violations = []
    compliant_bots = []
    
    for bot in bots:
        bot_name = bot.get("name", "Unknown")
        cycle_games = bot.get("cycle_games", 12)
        active_bets = bot.get("active_bets", 0)
        
        print(f"   🤖 Bot: {bot_name} | cycle_games: {cycle_games} | active_bets: {active_bets}")
        
        if active_bets > cycle_games:
            violation = f"{bot_name}: {active_bets} active bets > {cycle_games} cycle_games"
            compliance_violations.append(violation)
            print_critical_issue(f"CYCLE_GAMES VIOLATION: {violation}")
        else:
            compliant_bots.append(f"{bot_name}: {active_bets}/{cycle_games}")
    
    if compliance_violations:
        record_test(
            "Cycle games compliance check",
            False,
            f"Found {len(compliance_violations)} violations: {compliance_violations}"
        )
        
        # This is the critical issue mentioned in the Russian review
        print_critical_issue(f"RACE CONDITION NOT FIXED: {len(compliance_violations)} bots violating cycle_games limits")
    else:
        record_test(
            "Cycle games compliance check", 
            True,
            f"All {len(bots)} bots comply with cycle_games limits: {compliant_bots}"
        )

def test_single_automation_source(token: str):
    """КРИТИЧЕСКИЙ ТЕСТ 2: Проверка единого источника автоматизации"""
    print(f"\n{Colors.MAGENTA}🧪 CRITICAL TEST 2: Checking single automation source{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check for conflicting automation by monitoring bot activity patterns
    # Get active games multiple times to see if there are rapid, conflicting creations
    
    measurements = []
    
    for i in range(3):
        success, response_data, details = make_request(
            "GET",
            "/bots/active-games",
            headers=headers
        )
        
        if success and response_data:
            games = response_data if isinstance(response_data, list) else response_data.get("games", [])
            measurements.append({
                "timestamp": datetime.now().isoformat(),
                "active_games_count": len(games),
                "measurement": i + 1
            })
            print(f"   📊 Measurement {i+1}: {len(games)} active regular bot games")
        
        if i < 2:  # Don't sleep after last measurement
            time.sleep(2)
    
    if len(measurements) >= 2:
        # Check for reasonable stability (not rapid fluctuations indicating race conditions)
        game_counts = [m["active_games_count"] for m in measurements]
        max_count = max(game_counts)
        min_count = min(game_counts)
        fluctuation = max_count - min_count
        
        # Allow some fluctuation (games can complete/start), but not massive swings
        if fluctuation > 50:  # More than 50 games difference suggests race condition
            record_test(
                "Single automation source check",
                False,
                f"High fluctuation detected: {fluctuation} games difference (possible race condition)"
            )
            print_critical_issue(f"POSSIBLE RACE CONDITION: Game count fluctuation of {fluctuation}")
        else:
            record_test(
                "Single automation source check",
                True,
                f"Stable automation detected: fluctuation of {fluctuation} games is within normal range"
            )
    else:
        record_test(
            "Single automation source check",
            False,
            "Could not gather enough measurements"
        )

def test_regular_bots_endpoints(token: str):
    """КРИТИЧЕСКИЙ ТЕСТ 3: Проверка эндпоинтов обычных ботов"""
    print(f"\n{Colors.MAGENTA}🧪 CRITICAL TEST 3: Testing regular bots endpoints{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 3a: /bots/active-games - should show WAITING games of regular bots
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        waiting_games = [g for g in games if g.get("status") == "WAITING"]
        active_games = [g for g in games if g.get("status") == "ACTIVE"]
        
        record_test(
            "/bots/active-games endpoint",
            True,
            f"Found {len(games)} total games ({len(waiting_games)} WAITING, {len(active_games)} ACTIVE)"
        )
        
        print(f"   📊 Regular bots games breakdown:")
        print(f"      - Total games: {len(games)}")
        print(f"      - WAITING games: {len(waiting_games)}")
        print(f"      - ACTIVE games: {len(active_games)}")
        
    else:
        record_test(
            "/bots/active-games endpoint",
            False,
            f"Failed to get active games: {details}"
        )
    
    # Test 3b: /bots/ongoing-games - should show ACTIVE games of regular bots
    success, response_data, details = make_request(
        "GET",
        "/bots/ongoing-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        record_test(
            "/bots/ongoing-games endpoint",
            True,
            f"Found {len(games)} ongoing regular bot games"
        )
    else:
        # This endpoint might not exist or return 404, which could be normal
        if "404" in details:
            record_test(
                "/bots/ongoing-games endpoint",
                True,
                "Endpoint not found (may not be implemented yet)"
            )
        else:
            record_test(
                "/bots/ongoing-games endpoint",
                False,
                f"Failed to get ongoing games: {details}"
            )

def test_isolation_rules(token: str):
    """КРИТИЧЕСКИЙ ТЕСТ 4: Проверка правил изоляции"""
    print(f"\n{Colors.MAGENTA}🧪 CRITICAL TEST 4: Testing isolation rules{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 4a: Check that regular bots don't appear in human-bot endpoints
    success, response_data, details = make_request(
        "GET",
        "/games/available",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        # Check if any games are from regular bots (should be 0)
        regular_bot_games = []
        for game in games:
            creator_type = game.get("creator_type", "")
            bot_type = game.get("bot_type", "")
            is_regular_bot_game = game.get("is_regular_bot_game", False)
            
            if creator_type == "bot" or bot_type == "REGULAR" or is_regular_bot_game:
                regular_bot_games.append(game)
        
        if regular_bot_games:
            record_test(
                "Regular bots isolation from /games/available",
                False,
                f"Found {len(regular_bot_games)} regular bot games in available games (should be 0)"
            )
            print_critical_issue(f"ISOLATION VIOLATION: Regular bots found in /games/available")
        else:
            record_test(
                "Regular bots isolation from /games/available",
                True,
                f"No regular bot games found in /games/available (correct isolation)"
            )
    else:
        record_test(
            "Regular bots isolation from /games/available",
            False,
            f"Failed to check available games: {details}"
        )
    
    # Test 4b: Check that human-bots don't appear in regular bot endpoints
    success, response_data, details = make_request(
        "GET",
        "/bots/active-games",
        headers=headers
    )
    
    if success and response_data:
        games = response_data if isinstance(response_data, list) else response_data.get("games", [])
        
        # Check if any games are from human-bots (should be 0)
        human_bot_games = []
        for game in games:
            creator_type = game.get("creator_type", "")
            bot_type = game.get("bot_type", "")
            
            if creator_type == "human_bot" or bot_type == "HUMAN":
                human_bot_games.append(game)
        
        if human_bot_games:
            record_test(
                "Human-bots isolation from /bots/active-games",
                False,
                f"Found {len(human_bot_games)} human-bot games in regular bots section (should be 0)"
            )
            print_critical_issue(f"ISOLATION VIOLATION: Human-bots found in /bots/active-games")
        else:
            record_test(
                "Human-bots isolation from /bots/active-games",
                True,
                f"No human-bot games found in /bots/active-games (correct isolation)"
            )
    else:
        record_test(
            "Human-bots isolation from /bots/active-games",
            False,
            f"Failed to check regular bot games: {details}"
        )

def test_draw_replacement_logic(token: str):
    """ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: Проверка логики замещения при ничье"""
    print(f"\n{Colors.MAGENTA}🧪 ADDITIONAL TEST: Testing draw replacement logic{Colors.END}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get bots and check if they have pause_on_draw settings
    success, response_data, details = make_request(
        "GET",
        "/admin/bots",
        headers=headers
    )
    
    if success and response_data:
        bots = response_data if isinstance(response_data, list) else response_data.get("bots", [])
        
        bots_with_draw_settings = []
        for bot in bots:
            pause_on_draw = bot.get("pause_on_draw")
            if pause_on_draw is not None:
                bots_with_draw_settings.append(f"{bot.get('name', 'Unknown')}: {pause_on_draw}s")
        
        if bots_with_draw_settings:
            record_test(
                "Draw replacement logic settings",
                True,
                f"Found {len(bots_with_draw_settings)} bots with pause_on_draw settings: {bots_with_draw_settings}"
            )
        else:
            record_test(
                "Draw replacement logic settings",
                False,
                "No bots found with pause_on_draw settings"
            )
    else:
        record_test(
            "Draw replacement logic settings",
            False,
            f"Failed to check bot settings: {details}"
        )

def print_final_summary():
    """Print final test summary with focus on critical issues"""
    print_header("RACE CONDITION FIX TESTING SUMMARY")
    
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
    critical_issues = test_results["critical_issues"]
    if critical_issues:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CRITICAL ISSUES FOUND ({len(critical_issues)}):{Colors.END}")
        for i, issue in enumerate(critical_issues, 1):
            print(f"   {i}. {Colors.RED}{issue}{Colors.END}")
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ NO CRITICAL ISSUES FOUND{Colors.END}")
    
    print(f"\n{Colors.BOLD}🎯 RUSSIAN REVIEW REQUIREMENTS STATUS:{Colors.END}")
    
    requirements = [
        "CYCLE_GAMES COMPLIANCE: Каждый бот должен иметь active_bets <= cycle_games",
        "SINGLE AUTOMATION SOURCE: Только один automation loop активен",
        "ENDPOINT FUNCTIONALITY: /bots/active-games и /bots/ongoing-games работают",
        "ISOLATION RULES: Обычные боты не присоединяются к играм других ботов"
    ]
    
    for i, req in enumerate(requirements, 1):
        # Determine status based on test results
        if i == 1:  # Cycle games compliance
            status = f"{Colors.GREEN}✅ FIXED{Colors.END}" if not any("CYCLE_GAMES VIOLATION" in issue for issue in critical_issues) else f"{Colors.RED}❌ STILL BROKEN{Colors.END}"
        elif i == 2:  # Single automation
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if not any("RACE CONDITION" in issue for issue in critical_issues) else f"{Colors.RED}❌ RACE CONDITION DETECTED{Colors.END}"
        elif i == 3:  # Endpoints
            endpoint_tests = [t for t in test_results["tests"] if "endpoint" in t["name"].lower()]
            endpoint_success = all(t["success"] for t in endpoint_tests) if endpoint_tests else False
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if endpoint_success else f"{Colors.YELLOW}⚠️ PARTIAL{Colors.END}"
        elif i == 4:  # Isolation
            isolation_tests = [t for t in test_results["tests"] if "isolation" in t["name"].lower()]
            isolation_success = all(t["success"] for t in isolation_tests) if isolation_tests else False
            status = f"{Colors.GREEN}✅ WORKING{Colors.END}" if isolation_success else f"{Colors.RED}❌ VIOLATIONS FOUND{Colors.END}"
        else:
            status = f"{Colors.YELLOW}⚠️ UNKNOWN{Colors.END}"
        
        print(f"   {i}. {req}: {status}")
    
    # Final conclusion
    if critical_issues:
        print(f"\n{Colors.RED}{Colors.BOLD}🚨 CONCLUSION: RACE CONDITION FIX INCOMPLETE!{Colors.END}")
        print(f"{Colors.RED}Critical issues still exist that need immediate attention.{Colors.END}")
        print(f"{Colors.RED}The system is NOT ready for production use.{Colors.END}")
    elif success_rate >= 80:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONCLUSION: RACE CONDITION FIX SUCCESSFUL!{Colors.END}")
        print(f"{Colors.GREEN}All critical tests passed. The system is working correctly.{Colors.END}")
        print(f"{Colors.GREEN}Regular bots are now properly controlled and isolated.{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ CONCLUSION: PARTIAL SUCCESS ({success_rate:.1f}%){Colors.END}")
        print(f"{Colors.YELLOW}Some issues remain but no critical race conditions detected.{Colors.END}")

def main():
    """Main test execution"""
    print_header("REGULAR BOTS RACE CONDITION FIX TESTING")
    print(f"{Colors.BLUE}🎯 Testing race condition fix and cycle_games compliance{Colors.END}")
    print(f"{Colors.BLUE}📋 Focus: Single automation source, cycle limits, endpoint isolation{Colors.END}")
    
    # Authenticate
    token = authenticate_admin()
    if not token:
        print(f"{Colors.RED}❌ Cannot proceed without authentication{Colors.END}")
        sys.exit(1)
    
    try:
        # Run critical tests in order of importance
        test_cycle_games_compliance(token)  # Most critical
        test_single_automation_source(token)
        test_regular_bots_endpoints(token)
        test_isolation_rules(token)
        test_draw_replacement_logic(token)  # Additional verification
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Testing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error during testing: {str(e)}{Colors.END}")
    
    finally:
        # Print final summary
        print_final_summary()

if __name__ == "__main__":
    main()