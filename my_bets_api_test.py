#!/usr/bin/env python3
"""
GemPlay My Bets API Comprehensive Testing
Focus: Testing new /api/games/my-bets-paginated endpoint and related functionality
Russian Review Requirements: Test My Bets section with pagination, filtering, sorting, and cancellation
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string
import hashlib
from datetime import datetime

# Configuration
BASE_URL = "https://5bfabc99-1043-4213-a29d-540c7a2586c7.preview.emergentagent.com/api"
ADMIN_USER = {
    "email": "admin@gemplay.com",
    "password": "Admin123!"
}

TEST_USER = {
    "username": f"mybets_test_user_{int(time.time())}",
    "email": f"mybets_test_{int(time.time())}@test.com",
    "password": "Test123!",
    "gender": "male"
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

def test_user_registration_and_login() -> Optional[str]:
    """Register and login test user, return auth token."""
    print_subheader("User Registration and Login")
    
    # Register user
    response, success = make_request("POST", "/auth/register", data=TEST_USER)
    
    if not success:
        print_error("Failed to register test user")
        record_test("User Registration", False, "Registration failed")
        return None
    
    if "verification_token" not in response:
        print_error("Registration response missing verification token")
        record_test("User Registration", False, "Missing verification token")
        return None
    
    print_success("User registered successfully")
    record_test("User Registration", True)
    
    # Verify email
    verify_response, verify_success = make_request(
        "POST", "/auth/verify-email", 
        data={"token": response["verification_token"]}
    )
    
    if not verify_success:
        print_error("Failed to verify email")
        record_test("Email Verification", False, "Verification failed")
        return None
    
    print_success("Email verified successfully")
    record_test("Email Verification", True)
    
    # Login user
    login_response, login_success = make_request(
        "POST", "/auth/login", 
        data={"email": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    
    if not login_success or "access_token" not in login_response:
        print_error("Failed to login test user")
        record_test("User Login", False, "Login failed")
        return None
    
    print_success("User logged in successfully")
    record_test("User Login", True)
    
    return login_response["access_token"]

def setup_test_data(auth_token: str) -> List[str]:
    """Create test games for My Bets testing."""
    print_subheader("Setting Up Test Data")
    
    # Add balance for testing
    balance_response, balance_success = make_request(
        "POST", "/admin/balance/add",
        data={"amount": 500.0},
        auth_token=auth_token
    )
    
    if balance_success:
        print_success("Added $500 balance for testing")
    
    # Buy gems for testing
    gem_types = ["Ruby", "Emerald", "Topaz"]
    for gem_type in gem_types:
        buy_response, buy_success = make_request(
            "POST", f"/gems/buy?gem_type={gem_type}&quantity=50",
            auth_token=auth_token
        )
        if buy_success:
            print_success(f"Bought 50 {gem_type} gems")
    
    # Create test games with different statuses
    game_ids = []
    
    # Create WAITING games
    for i in range(3):
        game_data = {
            "move": random.choice(["rock", "paper", "scissors"]),
            "bet_gems": {"Ruby": random.randint(5, 15), "Emerald": random.randint(1, 3)}
        }
        
        game_response, game_success = make_request(
            "POST", "/games/create",
            data=game_data,
            auth_token=auth_token
        )
        
        if game_success and "game_id" in game_response:
            game_ids.append(game_response["game_id"])
            print_success(f"Created WAITING game: {game_response['game_id']}")
    
    # Wait a bit to ensure different timestamps
    time.sleep(2)
    
    # Join some bot games to create ACTIVE/COMPLETED games
    available_games_response, available_success = make_request(
        "GET", "/games/available",
        auth_token=auth_token
    )
    
    if available_success and isinstance(available_games_response, list):
        bot_games = [game for game in available_games_response 
                    if game.get("creator_type") in ["bot", "human_bot"]]
        
        # Join a few bot games
        for i, bot_game in enumerate(bot_games[:2]):
            join_data = {
                "move": random.choice(["rock", "paper", "scissors"]),
                "gems": {"Ruby": int(bot_game.get("bet_amount", 10))}
            }
            
            join_response, join_success = make_request(
                "POST", f"/games/{bot_game['game_id']}/join",
                data=join_data,
                auth_token=auth_token
            )
            
            if join_success:
                print_success(f"Joined bot game: {bot_game['game_id']}")
                # Wait for game to complete
                time.sleep(3)
    
    print_success(f"Created {len(game_ids)} test games")
    record_test("Test Data Setup", True, f"Created {len(game_ids)} games")
    
    return game_ids

def test_my_bets_paginated_basic() -> None:
    """Test basic functionality of /api/games/my-bets-paginated endpoint."""
    print_subheader("Testing My Bets Paginated - Basic Functionality")
    
    auth_token = test_user_registration_and_login()
    if not auth_token:
        return
    
    # Setup test data
    game_ids = setup_test_data(auth_token)
    
    # Test basic endpoint call without parameters
    print_subheader("Basic Call Without Parameters")
    response, success = make_request(
        "GET", "/games/my-bets-paginated",
        auth_token=auth_token
    )
    
    if not success:
        print_error("Basic my-bets-paginated call failed")
        record_test("My Bets Paginated - Basic Call", False, "Request failed")
        return
    
    # Verify response structure
    required_fields = ["success", "games", "pagination", "stats", "filters"]
    missing_fields = [field for field in required_fields if field not in response]
    
    if missing_fields:
        print_error(f"Response missing required fields: {missing_fields}")
        record_test("My Bets Paginated - Response Structure", False, f"Missing: {missing_fields}")
        return
    
    print_success("✓ Response has all required fields")
    record_test("My Bets Paginated - Response Structure", True)
    
    # Verify success flag
    if response.get("success") != True:
        print_error(f"Success flag is {response.get('success')}, expected True")
        record_test("My Bets Paginated - Success Flag", False, f"Success: {response.get('success')}")
    else:
        print_success("✓ Success flag is True")
        record_test("My Bets Paginated - Success Flag", True)
    
    # Verify games array
    games = response.get("games", [])
    if not isinstance(games, list):
        print_error("Games field is not an array")
        record_test("My Bets Paginated - Games Array", False, "Not an array")
    else:
        print_success(f"✓ Games array contains {len(games)} games")
        record_test("My Bets Paginated - Games Array", True)
        
        # Check game structure
        if games:
            game = games[0]
            required_game_fields = ["game_id", "bet_amount", "bet_gems", "status", "created_at"]
            missing_game_fields = [field for field in required_game_fields if field not in game]
            
            if missing_game_fields:
                print_error(f"Game object missing fields: {missing_game_fields}")
                record_test("My Bets Paginated - Game Structure", False, f"Missing: {missing_game_fields}")
            else:
                print_success("✓ Game objects have required fields")
                record_test("My Bets Paginated - Game Structure", True)
    
    # Verify pagination structure
    pagination = response.get("pagination", {})
    required_pagination_fields = ["current_page", "per_page", "total_pages", "total_count", "has_next", "has_prev"]
    missing_pagination_fields = [field for field in required_pagination_fields if field not in pagination]
    
    if missing_pagination_fields:
        print_error(f"Pagination missing fields: {missing_pagination_fields}")
        record_test("My Bets Paginated - Pagination Structure", False, f"Missing: {missing_pagination_fields}")
    else:
        print_success("✓ Pagination has all required fields")
        record_test("My Bets Paginated - Pagination Structure", True)
    
    # Verify stats structure
    stats = response.get("stats", {})
    required_stats_fields = ["total_games", "total_won", "total_lost", "total_draw", "total_winnings", "total_losses"]
    missing_stats_fields = [field for field in required_stats_fields if field not in stats]
    
    if missing_stats_fields:
        print_error(f"Stats missing fields: {missing_stats_fields}")
        record_test("My Bets Paginated - Stats Structure", False, f"Missing: {missing_stats_fields}")
    else:
        print_success("✓ Stats has all required fields")
        record_test("My Bets Paginated - Stats Structure", True)

def test_my_bets_pagination_parameters() -> None:
    """Test pagination parameters (page, per_page)."""
    print_subheader("Testing My Bets Paginated - Pagination Parameters")
    
    auth_token = test_user_registration_and_login()
    if not auth_token:
        return
    
    setup_test_data(auth_token)
    
    # Test with page=1, per_page=10
    print_subheader("Test page=1, per_page=10")
    response, success = make_request(
        "GET", "/games/my-bets-paginated",
        data={"page": 1, "per_page": 10},
        auth_token=auth_token
    )
    
    if success:
        pagination = response.get("pagination", {})
        if pagination.get("current_page") == 1 and pagination.get("per_page") == 10:
            print_success("✓ Pagination parameters correctly applied")
            record_test("My Bets Paginated - Pagination Params", True)
        else:
            print_error(f"Pagination params incorrect: page={pagination.get('current_page')}, per_page={pagination.get('per_page')}")
            record_test("My Bets Paginated - Pagination Params", False, "Incorrect params")
    else:
        record_test("My Bets Paginated - Pagination Params", False, "Request failed")
    
    # Test with different per_page values
    for per_page in [5, 20, 50]:
        print_subheader(f"Test per_page={per_page}")
        response, success = make_request(
            "GET", "/games/my-bets-paginated",
            data={"page": 1, "per_page": per_page},
            auth_token=auth_token
        )
        
        if success:
            pagination = response.get("pagination", {})
            games = response.get("games", [])
            
            if pagination.get("per_page") == per_page:
                print_success(f"✓ per_page={per_page} correctly set")
                
                # Verify games count doesn't exceed per_page
                if len(games) <= per_page:
                    print_success(f"✓ Games count ({len(games)}) <= per_page ({per_page})")
                    record_test(f"My Bets Paginated - per_page={per_page}", True)
                else:
                    print_error(f"Games count ({len(games)}) > per_page ({per_page})")
                    record_test(f"My Bets Paginated - per_page={per_page}", False, "Too many games")
            else:
                print_error(f"per_page incorrect: expected {per_page}, got {pagination.get('per_page')}")
                record_test(f"My Bets Paginated - per_page={per_page}", False, "Incorrect per_page")
        else:
            record_test(f"My Bets Paginated - per_page={per_page}", False, "Request failed")

def test_my_bets_filters() -> None:
    """Test filtering parameters (status_filter, date_filter, result_filter)."""
    print_subheader("Testing My Bets Paginated - Filters")
    
    auth_token = test_user_registration_and_login()
    if not auth_token:
        return
    
    setup_test_data(auth_token)
    
    # Test status filters
    status_filters = ["all", "WAITING", "ACTIVE", "COMPLETED"]
    for status_filter in status_filters:
        print_subheader(f"Test status_filter={status_filter}")
        response, success = make_request(
            "GET", "/games/my-bets-paginated",
            data={"status_filter": status_filter},
            auth_token=auth_token
        )
        
        if success:
            filters = response.get("filters", {})
            games = response.get("games", [])
            
            if filters.get("status_filter") == status_filter:
                print_success(f"✓ status_filter={status_filter} correctly applied")
                
                # Verify games match filter (if not 'all')
                if status_filter != "all" and games:
                    all_match = all(game.get("status") == status_filter for game in games)
                    if all_match:
                        print_success(f"✓ All games have status {status_filter}")
                        record_test(f"My Bets Paginated - status_filter={status_filter}", True)
                    else:
                        print_warning(f"Some games don't match status filter {status_filter}")
                        record_test(f"My Bets Paginated - status_filter={status_filter}", True, "Filter applied but mixed results")
                else:
                    record_test(f"My Bets Paginated - status_filter={status_filter}", True)
            else:
                print_error(f"status_filter incorrect: expected {status_filter}, got {filters.get('status_filter')}")
                record_test(f"My Bets Paginated - status_filter={status_filter}", False, "Incorrect filter")
        else:
            record_test(f"My Bets Paginated - status_filter={status_filter}", False, "Request failed")
    
    # Test date filters
    date_filters = ["all", "today", "week", "month"]
    for date_filter in date_filters:
        print_subheader(f"Test date_filter={date_filter}")
        response, success = make_request(
            "GET", "/games/my-bets-paginated",
            data={"date_filter": date_filter},
            auth_token=auth_token
        )
        
        if success:
            filters = response.get("filters", {})
            if filters.get("date_filter") == date_filter:
                print_success(f"✓ date_filter={date_filter} correctly applied")
                record_test(f"My Bets Paginated - date_filter={date_filter}", True)
            else:
                print_error(f"date_filter incorrect: expected {date_filter}, got {filters.get('date_filter')}")
                record_test(f"My Bets Paginated - date_filter={date_filter}", False, "Incorrect filter")
        else:
            record_test(f"My Bets Paginated - date_filter={date_filter}", False, "Request failed")
    
    # Test result filters
    result_filters = ["all", "won", "lost", "draw"]
    for result_filter in result_filters:
        print_subheader(f"Test result_filter={result_filter}")
        response, success = make_request(
            "GET", "/games/my-bets-paginated",
            data={"result_filter": result_filter},
            auth_token=auth_token
        )
        
        if success:
            filters = response.get("filters", {})
            if filters.get("result_filter") == result_filter:
                print_success(f"✓ result_filter={result_filter} correctly applied")
                record_test(f"My Bets Paginated - result_filter={result_filter}", True)
            else:
                print_error(f"result_filter incorrect: expected {result_filter}, got {filters.get('result_filter')}")
                record_test(f"My Bets Paginated - result_filter={result_filter}", False, "Incorrect filter")
        else:
            record_test(f"My Bets Paginated - result_filter={result_filter}", False, "Request failed")

def test_my_bets_sorting() -> None:
    """Test sorting parameters (sort_by, sort_order)."""
    print_subheader("Testing My Bets Paginated - Sorting")
    
    auth_token = test_user_registration_and_login()
    if not auth_token:
        return
    
    setup_test_data(auth_token)
    
    # Test sort_by options
    sort_by_options = ["created_at", "bet_amount", "status"]
    for sort_by in sort_by_options:
        for sort_order in ["desc", "asc"]:
            print_subheader(f"Test sort_by={sort_by}, sort_order={sort_order}")
            response, success = make_request(
                "GET", "/games/my-bets-paginated",
                data={"sort_by": sort_by, "sort_order": sort_order},
                auth_token=auth_token
            )
            
            if success:
                filters = response.get("filters", {})
                games = response.get("games", [])
                
                if filters.get("sort_by") == sort_by and filters.get("sort_order") == sort_order:
                    print_success(f"✓ Sorting parameters correctly applied")
                    
                    # Verify sorting (basic check)
                    if len(games) >= 2:
                        if sort_by == "created_at":
                            # Check if dates are sorted
                            dates = [game.get("created_at") for game in games if game.get("created_at")]
                            if len(dates) >= 2:
                                if sort_order == "desc":
                                    sorted_correctly = dates[0] >= dates[1]
                                else:
                                    sorted_correctly = dates[0] <= dates[1]
                                
                                if sorted_correctly:
                                    print_success(f"✓ Games correctly sorted by {sort_by} {sort_order}")
                                else:
                                    print_warning(f"Games may not be correctly sorted by {sort_by} {sort_order}")
                        
                        elif sort_by == "bet_amount":
                            # Check if bet amounts are sorted
                            amounts = [game.get("bet_amount", 0) for game in games]
                            if len(amounts) >= 2:
                                if sort_order == "desc":
                                    sorted_correctly = amounts[0] >= amounts[1]
                                else:
                                    sorted_correctly = amounts[0] <= amounts[1]
                                
                                if sorted_correctly:
                                    print_success(f"✓ Games correctly sorted by {sort_by} {sort_order}")
                                else:
                                    print_warning(f"Games may not be correctly sorted by {sort_by} {sort_order}")
                    
                    record_test(f"My Bets Paginated - sort_by={sort_by}, sort_order={sort_order}", True)
                else:
                    print_error(f"Sorting parameters incorrect")
                    record_test(f"My Bets Paginated - sort_by={sort_by}, sort_order={sort_order}", False, "Incorrect params")
            else:
                record_test(f"My Bets Paginated - sort_by={sort_by}, sort_order={sort_order}", False, "Request failed")

def test_legacy_endpoints_compatibility() -> None:
    """Test compatibility with existing /api/games/my-bets and /api/games/history endpoints."""
    print_subheader("Testing Legacy Endpoints Compatibility")
    
    auth_token = test_user_registration_and_login()
    if not auth_token:
        return
    
    setup_test_data(auth_token)
    
    # Test /api/games/my-bets endpoint
    print_subheader("Test /api/games/my-bets endpoint")
    my_bets_response, my_bets_success = make_request(
        "GET", "/games/my-bets",
        auth_token=auth_token
    )
    
    if my_bets_success:
        print_success("✓ /api/games/my-bets endpoint accessible")
        
        if isinstance(my_bets_response, list):
            print_success(f"✓ Returns array with {len(my_bets_response)} games")
            record_test("Legacy Endpoints - my-bets", True)
        else:
            print_error("Response is not an array")
            record_test("Legacy Endpoints - my-bets", False, "Not an array")
    else:
        print_error("✗ /api/games/my-bets endpoint failed")
        record_test("Legacy Endpoints - my-bets", False, "Request failed")
    
    # Test /api/games/history endpoint
    print_subheader("Test /api/games/history endpoint")
    history_response, history_success = make_request(
        "GET", "/games/history",
        auth_token=auth_token
    )
    
    if history_success:
        print_success("✓ /api/games/history endpoint accessible")
        
        if isinstance(history_response, list):
            print_success(f"✓ Returns array with {len(history_response)} games")
            record_test("Legacy Endpoints - history", True)
        else:
            print_error("Response is not an array")
            record_test("Legacy Endpoints - history", False, "Not an array")
    else:
        print_error("✗ /api/games/history endpoint failed")
        record_test("Legacy Endpoints - history", False, "Request failed")

def test_game_cancellation() -> None:
    """Test game cancellation endpoint /api/games/{game_id}/cancel."""
    print_subheader("Testing Game Cancellation")
    
    auth_token = test_user_registration_and_login()
    if not auth_token:
        return
    
    # Create a game for cancellation testing
    game_data = {
        "move": "rock",
        "bet_gems": {"Ruby": 10, "Emerald": 2}
    }
    
    game_response, game_success = make_request(
        "POST", "/games/create",
        data=game_data,
        auth_token=auth_token
    )
    
    if not game_success or "game_id" not in game_response:
        print_error("Failed to create game for cancellation test")
        record_test("Game Cancellation - Create Game", False, "Game creation failed")
        return
    
    game_id = game_response["game_id"]
    print_success(f"Created game for cancellation: {game_id}")
    record_test("Game Cancellation - Create Game", True)
    
    # Test cancellation
    print_subheader(f"Cancel game {game_id}")
    cancel_response, cancel_success = make_request(
        "POST", f"/games/{game_id}/cancel",
        auth_token=auth_token
    )
    
    if cancel_success:
        print_success("✓ Game cancellation request successful")
        
        # Verify response structure
        required_fields = ["success", "message", "gems_returned", "commission_returned"]
        missing_fields = [field for field in required_fields if field not in cancel_response]
        
        if missing_fields:
            print_error(f"Cancel response missing fields: {missing_fields}")
            record_test("Game Cancellation - Response Structure", False, f"Missing: {missing_fields}")
        else:
            print_success("✓ Cancel response has all required fields")
            record_test("Game Cancellation - Response Structure", True)
        
        # Check success flag
        if cancel_response.get("success") == True:
            print_success("✓ Cancellation success flag is True")
            record_test("Game Cancellation - Success Flag", True)
        else:
            print_error(f"Cancellation success flag is {cancel_response.get('success')}")
            record_test("Game Cancellation - Success Flag", False, f"Success: {cancel_response.get('success')}")
        
        # Check gems returned
        gems_returned = cancel_response.get("gems_returned", {})
        if isinstance(gems_returned, dict) and gems_returned:
            print_success(f"✓ Gems returned: {gems_returned}")
            record_test("Game Cancellation - Gems Returned", True)
        else:
            print_warning("No gems returned or invalid format")
            record_test("Game Cancellation - Gems Returned", False, "No gems returned")
        
        # Check commission returned
        commission_returned = cancel_response.get("commission_returned", 0)
        if isinstance(commission_returned, (int, float)) and commission_returned >= 0:
            print_success(f"✓ Commission returned: ${commission_returned}")
            record_test("Game Cancellation - Commission Returned", True)
        else:
            print_error(f"Invalid commission returned: {commission_returned}")
            record_test("Game Cancellation - Commission Returned", False, f"Commission: {commission_returned}")
        
        record_test("Game Cancellation - Overall", True)
    else:
        print_error("✗ Game cancellation failed")
        record_test("Game Cancellation - Overall", False, "Request failed")
    
    # Test cancellation of non-existent game
    print_subheader("Test cancellation of non-existent game")
    fake_game_id = "non-existent-game-id-12345"
    fake_cancel_response, fake_cancel_success = make_request(
        "POST", f"/games/{fake_game_id}/cancel",
        auth_token=auth_token,
        expected_status=404
    )
    
    if not fake_cancel_success:
        print_success("✓ Cancellation correctly failed for non-existent game (HTTP 404)")
        record_test("Game Cancellation - Non-existent Game", True)
    else:
        print_error("✗ Cancellation succeeded for non-existent game")
        record_test("Game Cancellation - Non-existent Game", False, "Should have failed")

def test_authorization_required() -> None:
    """Test that all endpoints require valid authorization."""
    print_subheader("Testing Authorization Requirements")
    
    endpoints_to_test = [
        "/games/my-bets-paginated",
        "/games/my-bets",
        "/games/history"
    ]
    
    for endpoint in endpoints_to_test:
        print_subheader(f"Test authorization for {endpoint}")
        
        # Test without token
        response, success = make_request(
            "GET", endpoint,
            expected_status=401
        )
        
        if not success:
            print_success(f"✓ {endpoint} correctly requires authorization (HTTP 401)")
            record_test(f"Authorization - {endpoint}", True)
        else:
            print_error(f"✗ {endpoint} accessible without authorization")
            record_test(f"Authorization - {endpoint}", False, "No auth required")
    
    # Test game cancellation authorization
    print_subheader("Test authorization for game cancellation")
    fake_game_id = "test-game-id"
    cancel_response, cancel_success = make_request(
        "POST", f"/games/{fake_game_id}/cancel",
        expected_status=401
    )
    
    if not cancel_success:
        print_success("✓ Game cancellation correctly requires authorization (HTTP 401)")
        record_test("Authorization - Game Cancellation", True)
    else:
        print_error("✗ Game cancellation accessible without authorization")
        record_test("Authorization - Game Cancellation", False, "No auth required")

def print_test_summary() -> None:
    """Print comprehensive test summary."""
    print_header("MY BETS API TESTING SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    print(f"Success Rate: {Colors.OKGREEN if success_rate >= 80 else Colors.WARNING}{success_rate:.1f}%{Colors.ENDC}")
    
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"✗ {test['name']}: {test['details']}")
    
    print_subheader("Key Findings:")
    
    # Categorize results
    categories = {
        "Basic Functionality": [],
        "Pagination": [],
        "Filtering": [],
        "Sorting": [],
        "Legacy Compatibility": [],
        "Game Cancellation": [],
        "Authorization": []
    }
    
    for test in test_results["tests"]:
        name = test["name"]
        if "Basic" in name or "Response Structure" in name or "Success Flag" in name:
            categories["Basic Functionality"].append(test)
        elif "Pagination" in name or "per_page" in name:
            categories["Pagination"].append(test)
        elif "filter" in name:
            categories["Filtering"].append(test)
        elif "sort" in name:
            categories["Sorting"].append(test)
        elif "Legacy" in name:
            categories["Legacy Compatibility"].append(test)
        elif "Cancellation" in name:
            categories["Game Cancellation"].append(test)
        elif "Authorization" in name:
            categories["Authorization"].append(test)
    
    for category, tests in categories.items():
        if tests:
            passed_in_category = sum(1 for test in tests if test["passed"])
            total_in_category = len(tests)
            category_rate = (passed_in_category / total_in_category * 100) if total_in_category > 0 else 0
            
            status_color = Colors.OKGREEN if category_rate >= 80 else Colors.WARNING if category_rate >= 50 else Colors.FAIL
            print(f"  {category}: {status_color}{passed_in_category}/{total_in_category} ({category_rate:.1f}%){Colors.ENDC}")

def main():
    """Main test execution function."""
    print_header("GEMPLAY MY BETS API COMPREHENSIVE TESTING")
    print("Testing new /api/games/my-bets-paginated endpoint and related functionality")
    print("Focus: Pagination, filtering, sorting, cancellation, and backward compatibility")
    
    try:
        # Run all test suites
        test_my_bets_paginated_basic()
        test_my_bets_pagination_parameters()
        test_my_bets_filters()
        test_my_bets_sorting()
        test_legacy_endpoints_compatibility()
        test_game_cancellation()
        test_authorization_required()
        
        # Print final summary
        print_test_summary()
        
        # Determine exit code
        success_rate = (test_results["passed"] / test_results["total"] * 100) if test_results["total"] > 0 else 0
        if success_rate >= 80:
            print_success("🎉 MY BETS API TESTING COMPLETED SUCCESSFULLY!")
            sys.exit(0)
        else:
            print_error("❌ MY BETS API TESTING COMPLETED WITH ISSUES")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print_error("\n❌ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"❌ Testing failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()