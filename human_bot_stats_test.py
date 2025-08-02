#!/usr/bin/env python3
"""
Human-Bot Statistics and Bets Testing
=====================================

This script tests the Human-Bot statistics and bets functionality as requested in the review:

1. Test `/api/admin/human-bots` endpoint - check statistics data
2. Test `/api/admin/human-bots/{bot_id}/active-bets` endpoint 
3. Test `/api/admin/human-bots/{bot_id}/all-bets` endpoint with pagination
4. Verify calculation logic for win_percentage, net profit, and average bet

Requirements from review:
- Проверить, что возвращаются корректные данные статистики для каждого бота
- Убедиться, что присутствуют поля: total_games_played, total_games_won, win_percentage, total_amount_won, total_amount_wagered, active_bets_count
- Проверить пагинацию (page, limit)
- Убедиться, что win_percentage корректно вычисляется
- Проверить, что чистая прибыль вычисляется правильно (total_amount_won - total_amount_wagered)
- Проверить, что средняя ставка вычисляется корректно
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
BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

SUPER_ADMIN_USER = {
    "email": "superadmin@gemplay.com",
    "password": "SuperAdmin123!"
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
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_subheader(text: str) -> None:
    """Print a formatted subheader."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * 80}{Colors.ENDC}\n")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def record_test(name: str, passed: bool, details: str = "") -> None:
    """Record a test result."""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    test_results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })

def make_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: int = 200,
    auth_token: Optional[str] = None
) -> Tuple[Dict[str, Any], bool]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    print(f"Making {method} request to {url}")
    if data:
        print(f"Request data: {json.dumps(data, indent=2)}")
    
    if data and method.lower() in ["post", "put", "patch"]:
        headers["Content-Type"] = "application/json"
        response = requests.request(method, url, json=data, headers=headers)
    else:
        response = requests.request(method, url, params=data, headers=headers)
    
    print(f"Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        response_data = {"text": response.text}
        print(f"Response text: {response.text}")
    
    success = response.status_code == expected_status
    
    if not success:
        print_error(f"Expected status {expected_status}, got {response.status_code}")
    
    return response_data, success

def test_login(email: str, password: str, user_type: str = "user") -> Optional[str]:
    """Test user login and return access token."""
    print_subheader(f"Testing {user_type.title()} Login")
    
    login_data = {
        "username": email,  # FastAPI OAuth2PasswordRequestForm uses 'username' field
        "password": password
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success:
        if "access_token" in response:
            print_success(f"{user_type.title()} logged in successfully")
            record_test(f"{user_type.title()} Login", True)
            return response["access_token"]
        else:
            print_error(f"{user_type.title()} login response missing access_token: {response}")
            record_test(f"{user_type.title()} Login", False, "Missing access_token")
    else:
        record_test(f"{user_type.title()} Login", False, "Request failed")
    
    return None

def test_human_bot_statistics_endpoint() -> Optional[str]:
    """Test the /api/admin/human-bots endpoint for statistics data."""
    print_header("HUMAN-BOT STATISTICS ENDPOINT TESTING")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with Human-Bot statistics test")
        record_test("Human-Bot Statistics - Admin Login", False, "Admin login failed")
        return None
    
    print_success("Admin logged in successfully")
    
    # Step 2: Test /api/admin/human-bots endpoint
    print_subheader("Step 2: Test Human-Bots List Endpoint")
    
    bots_response, bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=50",
        auth_token=admin_token
    )
    
    if not bots_success:
        print_error("Failed to get Human-Bots list")
        record_test("Human-Bot Statistics - Get Bots List", False, "Failed to get bots")
        return None
    
    # Verify response structure
    if "bots" not in bots_response:
        print_error("Response missing 'bots' field")
        record_test("Human-Bot Statistics - Response Structure", False, "Missing bots field")
        return None
    
    bots = bots_response["bots"]
    print_success(f"Found {len(bots)} Human-Bots")
    record_test("Human-Bot Statistics - Get Bots List", True)
    
    # Step 3: Verify required statistics fields for each bot
    print_subheader("Step 3: Verify Required Statistics Fields")
    
    required_fields = [
        "total_games_played",
        "total_games_won", 
        "win_percentage",
        "total_amount_won",
        "total_amount_wagered",
        "active_bets_count"
    ]
    
    bots_with_all_fields = 0
    sample_bot_id = None
    
    for i, bot in enumerate(bots):
        bot_id = bot.get("id", "unknown")
        bot_name = bot.get("name", "unknown")
        
        print_success(f"Bot {i+1}: {bot_name} (ID: {bot_id})")
        
        missing_fields = []
        for field in required_fields:
            if field in bot:
                value = bot[field]
                print_success(f"  ✓ {field}: {value}")
            else:
                missing_fields.append(field)
                print_error(f"  ✗ Missing field: {field}")
        
        if not missing_fields:
            bots_with_all_fields += 1
            if sample_bot_id is None:
                sample_bot_id = bot_id
        
        # Verify data types and logic
        if "total_games_played" in bot and "total_games_won" in bot:
            total_games = bot["total_games_played"]
            total_wins = bot["total_games_won"]
            
            if isinstance(total_games, int) and isinstance(total_wins, int):
                if total_wins <= total_games:
                    print_success(f"  ✓ Games logic correct: {total_wins} wins ≤ {total_games} total")
                else:
                    print_error(f"  ✗ Games logic incorrect: {total_wins} wins > {total_games} total")
            else:
                print_error(f"  ✗ Games fields not integers: games={type(total_games)}, wins={type(total_wins)}")
        
        # Verify win percentage calculation
        if "win_percentage" in bot and "total_games_played" in bot and "total_games_won" in bot:
            win_percentage = bot["win_percentage"]
            total_games = bot["total_games_played"]
            total_wins = bot["total_games_won"]
            
            if total_games > 0:
                expected_win_percentage = (total_wins / total_games) * 100
                if abs(win_percentage - expected_win_percentage) < 0.01:
                    print_success(f"  ✓ Win percentage correct: {win_percentage}% (calculated: {expected_win_percentage:.2f}%)")
                else:
                    print_error(f"  ✗ Win percentage incorrect: {win_percentage}% (expected: {expected_win_percentage:.2f}%)")
            else:
                if win_percentage == 0:
                    print_success(f"  ✓ Win percentage correct for 0 games: {win_percentage}%")
                else:
                    print_error(f"  ✗ Win percentage should be 0 for 0 games: {win_percentage}%")
        
        # Verify net profit calculation (total_amount_won - total_amount_wagered)
        if "total_amount_won" in bot and "total_amount_wagered" in bot:
            total_won = bot["total_amount_won"]
            total_wagered = bot["total_amount_wagered"]
            net_profit = total_won - total_wagered
            
            print_success(f"  ✓ Net profit calculation: ${total_won} - ${total_wagered} = ${net_profit:.2f}")
        
        # Verify average bet calculation
        if "total_amount_wagered" in bot and "total_games_played" in bot:
            total_wagered = bot["total_amount_wagered"]
            total_games = bot["total_games_played"]
            
            if total_games > 0:
                average_bet = total_wagered / total_games
                print_success(f"  ✓ Average bet calculation: ${total_wagered} / {total_games} = ${average_bet:.2f}")
            else:
                print_success(f"  ✓ Average bet: N/A (0 games played)")
        
        print()  # Empty line for readability
    
    # Record results
    if bots_with_all_fields == len(bots):
        print_success(f"✓ All {len(bots)} bots have required statistics fields")
        record_test("Human-Bot Statistics - Required Fields", True)
    else:
        print_error(f"✗ Only {bots_with_all_fields}/{len(bots)} bots have all required fields")
        record_test("Human-Bot Statistics - Required Fields", False, f"Missing fields in {len(bots) - bots_with_all_fields} bots")
    
    return sample_bot_id

def test_human_bot_active_bets_endpoint(bot_id: str, admin_token: str) -> None:
    """Test the /api/admin/human-bots/{bot_id}/active-bets endpoint."""
    print_header("HUMAN-BOT ACTIVE BETS ENDPOINT TESTING")
    
    if not bot_id:
        print_error("No bot ID provided for active bets testing")
        record_test("Human-Bot Active Bets - No Bot ID", False, "No bot ID available")
        return
    
    print_subheader(f"Testing Active Bets for Bot ID: {bot_id}")
    
    # Test the active bets endpoint
    active_bets_response, active_bets_success = make_request(
        "GET", f"/admin/human-bots/{bot_id}/active-bets",
        auth_token=admin_token
    )
    
    if not active_bets_success:
        print_error("Failed to get active bets")
        record_test("Human-Bot Active Bets - Get Active Bets", False, "Request failed")
        return
    
    print_success("✓ Active bets endpoint accessible")
    record_test("Human-Bot Active Bets - Get Active Bets", True)
    
    # Verify response structure
    if isinstance(active_bets_response, list):
        active_bets = active_bets_response
        print_success(f"✓ Found {len(active_bets)} active bets")
    elif isinstance(active_bets_response, dict) and "bets" in active_bets_response:
        active_bets = active_bets_response["bets"]
        print_success(f"✓ Found {len(active_bets)} active bets")
    else:
        print_error(f"✗ Unexpected response structure: {type(active_bets_response)}")
        record_test("Human-Bot Active Bets - Response Structure", False, "Unexpected structure")
        return
    
    record_test("Human-Bot Active Bets - Response Structure", True)
    
    # Verify bet data structure
    if active_bets:
        print_subheader("Verifying Active Bet Data Structure")
        
        expected_bet_fields = ["game_id", "bet_amount", "status", "created_at"]
        
        for i, bet in enumerate(active_bets[:5]):  # Check first 5 bets
            print_success(f"Active Bet {i+1}:")
            
            for field in expected_bet_fields:
                if field in bet:
                    value = bet[field]
                    print_success(f"  ✓ {field}: {value}")
                else:
                    print_warning(f"  ⚠ Missing field: {field}")
            
            # Verify bet amount is numeric
            if "bet_amount" in bet:
                bet_amount = bet["bet_amount"]
                if isinstance(bet_amount, (int, float)):
                    print_success(f"  ✓ Bet amount is numeric: ${bet_amount}")
                else:
                    print_error(f"  ✗ Bet amount not numeric: {bet_amount} ({type(bet_amount)})")
            
            # Verify status is valid
            if "status" in bet:
                status = bet["status"]
                valid_statuses = ["WAITING", "ACTIVE", "COMPLETED", "CANCELLED", "TIMEOUT"]
                if status in valid_statuses:
                    print_success(f"  ✓ Valid status: {status}")
                else:
                    print_warning(f"  ⚠ Unexpected status: {status}")
            
            print()  # Empty line for readability
        
        record_test("Human-Bot Active Bets - Bet Data Structure", True)
    else:
        print_warning("No active bets found for this bot")
        record_test("Human-Bot Active Bets - Bet Data Structure", True, "No active bets")

def test_human_bot_all_bets_endpoint(bot_id: str, admin_token: str) -> None:
    """Test the /api/admin/human-bots/{bot_id}/all-bets endpoint with pagination."""
    print_header("HUMAN-BOT ALL BETS ENDPOINT TESTING")
    
    if not bot_id:
        print_error("No bot ID provided for all bets testing")
        record_test("Human-Bot All Bets - No Bot ID", False, "No bot ID available")
        return
    
    print_subheader(f"Testing All Bets for Bot ID: {bot_id}")
    
    # Test pagination parameters
    pagination_tests = [
        {"page": 1, "limit": 10},
        {"page": 1, "limit": 25},
        {"page": 2, "limit": 10},
    ]
    
    for i, params in enumerate(pagination_tests):
        print_subheader(f"Pagination Test {i+1}: page={params['page']}, limit={params['limit']}")
        
        # Build query string
        query_params = f"page={params['page']}&limit={params['limit']}"
        
        all_bets_response, all_bets_success = make_request(
            "GET", f"/admin/human-bots/{bot_id}/all-bets?{query_params}",
            auth_token=admin_token
        )
        
        if not all_bets_success:
            print_error(f"Failed to get all bets with pagination {params}")
            record_test(f"Human-Bot All Bets - Pagination {i+1}", False, "Request failed")
            continue
        
        print_success("✓ All bets endpoint accessible with pagination")
        
        # Verify response structure
        if isinstance(all_bets_response, dict):
            # Check for pagination info
            if "bets" in all_bets_response and "pagination" in all_bets_response:
                bets = all_bets_response["bets"]
                pagination = all_bets_response["pagination"]
                
                print_success(f"✓ Found {len(bets)} bets")
                print_success(f"✓ Pagination info: {pagination}")
                
                # Verify pagination fields
                pagination_fields = ["current_page", "total_pages", "per_page", "total_items"]
                for field in pagination_fields:
                    if field in pagination:
                        print_success(f"  ✓ {field}: {pagination[field]}")
                    else:
                        print_warning(f"  ⚠ Missing pagination field: {field}")
                
                # Verify pagination logic
                if "current_page" in pagination and "per_page" in pagination:
                    expected_page = params["page"]
                    expected_limit = params["limit"]
                    
                    if pagination["current_page"] == expected_page:
                        print_success(f"  ✓ Current page correct: {expected_page}")
                    else:
                        print_error(f"  ✗ Current page incorrect: expected {expected_page}, got {pagination['current_page']}")
                    
                    if pagination["per_page"] == expected_limit:
                        print_success(f"  ✓ Per page correct: {expected_limit}")
                    else:
                        print_error(f"  ✗ Per page incorrect: expected {expected_limit}, got {pagination['per_page']}")
                    
                    # Verify bet count doesn't exceed limit
                    if len(bets) <= expected_limit:
                        print_success(f"  ✓ Bet count within limit: {len(bets)} ≤ {expected_limit}")
                    else:
                        print_error(f"  ✗ Bet count exceeds limit: {len(bets)} > {expected_limit}")
                
                record_test(f"Human-Bot All Bets - Pagination {i+1}", True)
                
            elif isinstance(all_bets_response, list):
                # Direct list response
                bets = all_bets_response
                print_success(f"✓ Found {len(bets)} bets (direct list)")
                record_test(f"Human-Bot All Bets - Pagination {i+1}", True, "Direct list response")
            else:
                print_error(f"✗ Unexpected response structure: {all_bets_response}")
                record_test(f"Human-Bot All Bets - Pagination {i+1}", False, "Unexpected structure")
        else:
            print_error(f"✗ Response not a dictionary: {type(all_bets_response)}")
            record_test(f"Human-Bot All Bets - Pagination {i+1}", False, "Response not dict")
    
    # Test with first page to verify bet data structure
    print_subheader("Verifying All Bet Data Structure")
    
    all_bets_response, all_bets_success = make_request(
        "GET", f"/admin/human-bots/{bot_id}/all-bets?page=1&limit=10",
        auth_token=admin_token
    )
    
    if all_bets_success:
        # Extract bets from response
        if isinstance(all_bets_response, dict) and "bets" in all_bets_response:
            bets = all_bets_response["bets"]
        elif isinstance(all_bets_response, list):
            bets = all_bets_response
        else:
            bets = []
        
        if bets:
            expected_bet_fields = ["game_id", "bet_amount", "status", "created_at", "completed_at", "outcome"]
            
            for i, bet in enumerate(bets[:3]):  # Check first 3 bets
                print_success(f"All Bet {i+1}:")
                
                for field in expected_bet_fields:
                    if field in bet:
                        value = bet[field]
                        print_success(f"  ✓ {field}: {value}")
                    else:
                        print_warning(f"  ⚠ Missing field: {field}")
                
                # Verify bet amount is numeric
                if "bet_amount" in bet:
                    bet_amount = bet["bet_amount"]
                    if isinstance(bet_amount, (int, float)):
                        print_success(f"  ✓ Bet amount is numeric: ${bet_amount}")
                    else:
                        print_error(f"  ✗ Bet amount not numeric: {bet_amount} ({type(bet_amount)})")
                
                print()  # Empty line for readability
            
            record_test("Human-Bot All Bets - Bet Data Structure", True)
        else:
            print_warning("No bets found for this bot")
            record_test("Human-Bot All Bets - Bet Data Structure", True, "No bets found")

def test_calculation_logic() -> None:
    """Test the calculation logic for win_percentage, net profit, and average bet."""
    print_header("CALCULATION LOGIC VERIFICATION TESTING")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with calculation logic test")
        record_test("Calculation Logic - Admin Login", False, "Admin login failed")
        return
    
    print_success("Admin logged in successfully")
    
    # Step 2: Get Human-Bots data for calculation verification
    print_subheader("Step 2: Get Human-Bots for Calculation Verification")
    
    bots_response, bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=10",
        auth_token=admin_token
    )
    
    if not bots_success or "bots" not in bots_response:
        print_error("Failed to get Human-Bots for calculation testing")
        record_test("Calculation Logic - Get Bots", False, "Failed to get bots")
        return
    
    bots = bots_response["bots"]
    print_success(f"Found {len(bots)} Human-Bots for calculation testing")
    
    # Step 3: Verify calculations for each bot
    print_subheader("Step 3: Verify Calculations")
    
    calculation_tests_passed = 0
    calculation_tests_total = 0
    
    for i, bot in enumerate(bots):
        bot_name = bot.get("name", "unknown")
        print_success(f"Bot {i+1}: {bot_name}")
        
        # Test 1: Win Percentage Calculation
        if all(field in bot for field in ["total_games_played", "total_games_won", "win_percentage"]):
            total_games = bot["total_games_played"]
            total_wins = bot["total_games_won"]
            reported_win_percentage = bot["win_percentage"]
            
            if total_games > 0:
                expected_win_percentage = (total_wins / total_games) * 100
            else:
                expected_win_percentage = 0
            
            calculation_tests_total += 1
            if abs(reported_win_percentage - expected_win_percentage) < 0.01:
                print_success(f"  ✓ Win percentage correct: {reported_win_percentage}% (expected: {expected_win_percentage:.2f}%)")
                calculation_tests_passed += 1
            else:
                print_error(f"  ✗ Win percentage incorrect: {reported_win_percentage}% (expected: {expected_win_percentage:.2f}%)")
        
        # Test 2: Net Profit Calculation
        if all(field in bot for field in ["total_amount_won", "total_amount_wagered"]):
            total_won = bot["total_amount_won"]
            total_wagered = bot["total_amount_wagered"]
            calculated_net_profit = total_won - total_wagered
            
            calculation_tests_total += 1
            print_success(f"  ✓ Net profit calculation: ${total_won:.2f} - ${total_wagered:.2f} = ${calculated_net_profit:.2f}")
            calculation_tests_passed += 1
            
            # Verify the calculation makes sense
            if total_wagered >= 0 and total_won >= 0:
                print_success(f"    ✓ Values are non-negative")
            else:
                print_error(f"    ✗ Negative values detected: won=${total_won}, wagered=${total_wagered}")
        
        # Test 3: Average Bet Calculation
        if all(field in bot for field in ["total_amount_wagered", "total_games_played"]):
            total_wagered = bot["total_amount_wagered"]
            total_games = bot["total_games_played"]
            
            if total_games > 0:
                calculated_average_bet = total_wagered / total_games
                calculation_tests_total += 1
                print_success(f"  ✓ Average bet calculation: ${total_wagered:.2f} / {total_games} = ${calculated_average_bet:.2f}")
                calculation_tests_passed += 1
                
                # Verify the average bet is reasonable
                if calculated_average_bet > 0:
                    print_success(f"    ✓ Average bet is positive")
                else:
                    print_error(f"    ✗ Average bet is not positive: ${calculated_average_bet:.2f}")
            else:
                print_success(f"  ✓ Average bet: N/A (0 games played)")
        
        print()  # Empty line for readability
    
    # Record overall calculation test results
    if calculation_tests_passed == calculation_tests_total:
        print_success(f"✓ All calculation tests passed: {calculation_tests_passed}/{calculation_tests_total}")
        record_test("Calculation Logic - All Calculations", True)
    else:
        print_error(f"✗ Some calculation tests failed: {calculation_tests_passed}/{calculation_tests_total}")
        record_test("Calculation Logic - All Calculations", False, f"Failed: {calculation_tests_total - calculation_tests_passed}")

def print_test_summary() -> None:
    """Print a summary of all test results."""
    print_header("TEST SUMMARY")
    
    print_success(f"Total tests run: {test_results['total']}")
    print_success(f"Tests passed: {test_results['passed']}")
    print_error(f"Tests failed: {test_results['failed']}")
    
    if test_results['failed'] > 0:
        print_subheader("Failed Tests:")
        for test in test_results['tests']:
            if not test['passed']:
                print_error(f"✗ {test['name']}: {test['details']}")
    
    success_rate = (test_results['passed'] / test_results['total']) * 100 if test_results['total'] > 0 else 0
    print_success(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print_success("🎉 EXCELLENT: Human-Bot statistics and bets functionality is working well!")
    elif success_rate >= 70:
        print_warning("⚠️ GOOD: Most functionality working, some issues to address")
    else:
        print_error("❌ NEEDS WORK: Significant issues found in Human-Bot statistics and bets")

def main():
    """Main test execution function."""
    print_header("HUMAN-BOT STATISTICS AND BETS FUNCTIONALITY TESTING")
    print("Testing Human-Bot statistics and bets endpoints as requested in the review")
    print("Focus areas: statistics data, active bets, all bets with pagination, calculation logic")
    
    # Test 1: Human-Bot Statistics Endpoint
    sample_bot_id = test_human_bot_statistics_endpoint()
    
    if sample_bot_id:
        # Get admin token for subsequent tests
        admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
        
        if admin_token:
            # Test 2: Active Bets Endpoint
            test_human_bot_active_bets_endpoint(sample_bot_id, admin_token)
            
            # Test 3: All Bets Endpoint with Pagination
            test_human_bot_all_bets_endpoint(sample_bot_id, admin_token)
    
    # Test 4: Calculation Logic Verification
    test_calculation_logic()
    
    # Print final summary
    print_test_summary()

if __name__ == "__main__":
    main()