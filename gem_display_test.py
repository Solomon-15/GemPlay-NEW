#!/usr/bin/env python3
"""
Test script for Gem Display Changes from Dollars to Gems
Testing the changes in bot bet range display from dollars to gems.

CONTEXT: Implemented changes for displaying bot bets in gems instead of dollars. Changes include:
1. Added formatAsGems() function in /app/frontend/src/utils/economy.js for converting dollars to gems display
2. HumanBotsList.js: changed display from "Min: $X, Max: $Y" → "Мин: X, Макс: Y" 
3. HumanBotsManagement.js: changed field labels from "Мин./Макс. ставка ($)" → "Мин./Макс. ставка (гемы)" and parameters (step="1", parseInt instead of parseFloat)
4. RegularBotsManagement.js: similar changes for regular bots

CONVERSION LOGIC: Since $1 = 1 gem, formatAsGems() simply removes the $ sign and formats as integer.

TESTING TASKS:
1. Check that all API endpoints for bots work correctly
2. Ensure that bet creation logic is not broken  
3. Verify that backend correctly handles integer values instead of float
4. Test creation of Human-bots and regular bots with new parameters
5. Ensure that existing bots display correctly
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://baf8f4bf-8f93-48f1-becd-06acae851bae.preview.emergentagent.com/api"
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
        "email": email,
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

def test_human_bot_api_endpoints() -> None:
    """Test Human-Bot API endpoints with integer values for min_bet/max_bet."""
    print_header("HUMAN-BOT API ENDPOINTS TESTING - GEM DISPLAY CHANGES")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with Human-Bot API test")
        record_test("Human-Bot API - Admin Login", False, "Admin login failed")
        return
    
    print_success(f"Admin logged in successfully")
    
    # Step 2: Test Human-Bot creation with integer values
    print_subheader("Step 2: Test Human-Bot Creation with Integer Values")
    
    # Test creating Human-Bot with integer min_bet/max_bet values (gems)
    test_bot_data = {
        "name": f"GemTestBot_{int(time.time())}",
        "character": "BALANCED",
        "min_bet": 5,  # Integer value (5 gems = $5)
        "max_bet": 50,  # Integer value (50 gems = $50)
        "bet_limit": 12,
        "win_percentage": 40.0,
        "loss_percentage": 40.0,
        "draw_percentage": 20.0,
        "min_delay": 30,
        "max_delay": 90,
        "use_commit_reveal": True,
        "logging_level": "INFO",
        "can_play_with_other_bots": True,
        "can_play_with_players": True
    }
    
    create_response, create_success = make_request(
        "POST", "/admin/human-bots",
        data=test_bot_data,
        auth_token=admin_token
    )
    
    if create_success:
        test_bot_id = create_response.get("id")
        if test_bot_id:
            print_success(f"✓ Human-Bot created successfully with integer values")
            print_success(f"  Bot ID: {test_bot_id}")
            print_success(f"  Min bet: {test_bot_data['min_bet']} gems")
            print_success(f"  Max bet: {test_bot_data['max_bet']} gems")
            record_test("Human-Bot API - Create with Integer Values", True)
        else:
            print_error("Human-Bot creation response missing ID")
            record_test("Human-Bot API - Create with Integer Values", False, "Missing bot ID")
            return
    else:
        print_error(f"Failed to create Human-Bot with integer values: {create_response}")
        record_test("Human-Bot API - Create with Integer Values", False, "Creation failed")
        return
    
    # Step 3: Test Human-Bot retrieval and verify integer values
    print_subheader("Step 3: Test Human-Bot Retrieval and Verify Integer Values")
    
    # Get the created bot details
    bot_details_response, bot_details_success = make_request(
        "GET", f"/admin/human-bots/{test_bot_id}",
        auth_token=admin_token
    )
    
    if bot_details_success:
        min_bet = bot_details_response.get("min_bet")
        max_bet = bot_details_response.get("max_bet")
        
        print_success(f"✓ Bot details retrieved successfully")
        print_success(f"  Retrieved min_bet: {min_bet} (type: {type(min_bet).__name__})")
        print_success(f"  Retrieved max_bet: {max_bet} (type: {type(max_bet).__name__})")
        
        # Verify values are correct and can be treated as integers
        if min_bet == 5 and max_bet == 50:
            print_success("✓ Min/Max bet values are correct")
            record_test("Human-Bot API - Retrieve Integer Values", True)
        else:
            print_error(f"✗ Min/Max bet values incorrect: min={min_bet}, max={max_bet}")
            record_test("Human-Bot API - Retrieve Integer Values", False, f"Values: min={min_bet}, max={max_bet}")
        
        # Test that values can be formatted as integers (no decimal places)
        try:
            min_bet_int = int(min_bet)
            max_bet_int = int(max_bet)
            print_success(f"✓ Values can be converted to integers: {min_bet_int}, {max_bet_int}")
            record_test("Human-Bot API - Integer Conversion", True)
        except (ValueError, TypeError) as e:
            print_error(f"✗ Cannot convert values to integers: {e}")
            record_test("Human-Bot API - Integer Conversion", False, str(e))
    else:
        print_error("Failed to retrieve bot details")
        record_test("Human-Bot API - Retrieve Integer Values", False, "Retrieval failed")
    
    # Step 4: Test Human-Bot list endpoint
    print_subheader("Step 4: Test Human-Bot List Endpoint")
    
    list_response, list_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=50",
        auth_token=admin_token
    )
    
    if list_success:
        bots = list_response.get("bots", [])
        print_success(f"✓ Human-Bot list retrieved successfully ({len(bots)} bots)")
        
        # Find our test bot in the list
        test_bot_found = False
        for bot in bots:
            if bot.get("id") == test_bot_id:
                test_bot_found = True
                list_min_bet = bot.get("min_bet")
                list_max_bet = bot.get("max_bet")
                
                print_success(f"✓ Test bot found in list")
                print_success(f"  List min_bet: {list_min_bet} (type: {type(list_min_bet).__name__})")
                print_success(f"  List max_bet: {list_max_bet} (type: {type(list_max_bet).__name__})")
                
                # Verify consistency
                if list_min_bet == 5 and list_max_bet == 50:
                    print_success("✓ List values consistent with creation")
                    record_test("Human-Bot API - List Consistency", True)
                else:
                    print_error(f"✗ List values inconsistent: min={list_min_bet}, max={list_max_bet}")
                    record_test("Human-Bot API - List Consistency", False, f"Values: min={list_min_bet}, max={list_max_bet}")
                break
        
        if not test_bot_found:
            print_error("✗ Test bot not found in list")
            record_test("Human-Bot API - List Contains Bot", False, "Bot not found")
        else:
            record_test("Human-Bot API - List Contains Bot", True)
    else:
        print_error("Failed to retrieve Human-Bot list")
        record_test("Human-Bot API - List Endpoint", False, "List retrieval failed")
    
    # Step 5: Test Human-Bot update with integer values
    print_subheader("Step 5: Test Human-Bot Update with Integer Values")
    
    update_data = {
        "min_bet": 10,  # Update to 10 gems
        "max_bet": 100,  # Update to 100 gems
        "bet_limit": 15
    }
    
    update_response, update_success = make_request(
        "PUT", f"/admin/human-bots/{test_bot_id}",
        data=update_data,
        auth_token=admin_token
    )
    
    if update_success:
        print_success("✓ Human-Bot updated successfully with integer values")
        
        # Verify updated values
        updated_min_bet = update_response.get("min_bet")
        updated_max_bet = update_response.get("max_bet")
        
        if updated_min_bet == 10 and updated_max_bet == 100:
            print_success(f"✓ Updated values correct: min={updated_min_bet}, max={updated_max_bet}")
            record_test("Human-Bot API - Update Integer Values", True)
        else:
            print_error(f"✗ Updated values incorrect: min={updated_min_bet}, max={updated_max_bet}")
            record_test("Human-Bot API - Update Integer Values", False, f"Values: min={updated_min_bet}, max={updated_max_bet}")
    else:
        print_error(f"Failed to update Human-Bot: {update_response}")
        record_test("Human-Bot API - Update Integer Values", False, "Update failed")
    
    # Step 6: Test bulk creation with integer values
    print_subheader("Step 6: Test Bulk Human-Bot Creation with Integer Values")
    
    bulk_create_data = {
        "count": 3,
        "character": "AGGRESSIVE",
        "min_bet_range": [15, 20],  # Integer range for min_bet
        "max_bet_range": [80, 120],  # Integer range for max_bet
        "bet_limit_range": [10, 15],
        "win_percentage": 45.0,
        "loss_percentage": 35.0,
        "draw_percentage": 20.0,
        "delay_range": [30, 90],
        "use_commit_reveal": True,
        "logging_level": "INFO"
    }
    
    bulk_create_response, bulk_create_success = make_request(
        "POST", "/admin/human-bots/bulk-create",
        data=bulk_create_data,
        auth_token=admin_token
    )
    
    if bulk_create_success:
        created_bots = bulk_create_response.get("bots", [])
        print_success(f"✓ Bulk creation successful ({len(created_bots)} bots created)")
        
        # Verify each created bot has integer values within expected ranges
        all_values_correct = True
        for i, bot in enumerate(created_bots):
            min_bet = bot.get("min_bet")
            max_bet = bot.get("max_bet")
            
            print_success(f"  Bot {i+1}: min_bet={min_bet}, max_bet={max_bet}")
            
            # Check if values are within expected ranges
            if not (15 <= min_bet <= 20 and 80 <= max_bet <= 120):
                all_values_correct = False
                print_error(f"  ✗ Bot {i+1} values outside expected ranges")
        
        if all_values_correct:
            print_success("✓ All bulk-created bots have correct integer values")
            record_test("Human-Bot API - Bulk Create Integer Values", True)
        else:
            print_error("✗ Some bulk-created bots have incorrect values")
            record_test("Human-Bot API - Bulk Create Integer Values", False, "Values outside ranges")
        
        # Store bot IDs for cleanup
        bulk_bot_ids = [bot.get("id") for bot in created_bots if bot.get("id")]
    else:
        print_error(f"Failed to bulk create Human-Bots: {bulk_create_response}")
        record_test("Human-Bot API - Bulk Create Integer Values", False, "Bulk creation failed")
        bulk_bot_ids = []
    
    # Step 7: Test game creation logic with integer bet values
    print_subheader("Step 7: Test Game Creation Logic with Integer Bet Values")
    
    # Get available Human-bot games to verify bet amounts are integers
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        human_bot_games = [game for game in available_games_response if game.get("creator_type") == "human_bot"]
        
        if human_bot_games:
            print_success(f"✓ Found {len(human_bot_games)} Human-bot games")
            
            # Check first few games for integer bet amounts
            integer_bets_count = 0
            for i, game in enumerate(human_bot_games[:5]):
                bet_amount = game.get("bet_amount", 0)
                game_id = game.get("game_id", "unknown")
                
                print_success(f"  Game {i+1}: ID={game_id}, Bet=${bet_amount}")
                
                # Check if bet amount is effectively an integer (no decimal part)
                if isinstance(bet_amount, (int, float)) and bet_amount == int(bet_amount):
                    integer_bets_count += 1
                    print_success(f"    ✓ Bet amount is integer-compatible: {int(bet_amount)}")
                else:
                    print_warning(f"    ⚠ Bet amount has decimal part: {bet_amount}")
            
            if integer_bets_count >= 3:  # At least 3 out of 5 should be integer-compatible
                print_success("✓ Most Human-bot games have integer-compatible bet amounts")
                record_test("Human-Bot API - Integer Bet Amounts", True)
            else:
                print_warning("⚠ Some Human-bot games have non-integer bet amounts")
                record_test("Human-Bot API - Integer Bet Amounts", False, f"Only {integer_bets_count}/5 integer bets")
        else:
            print_warning("No Human-bot games found for bet amount verification")
            record_test("Human-Bot API - Integer Bet Amounts", False, "No games found")
    else:
        print_error("Failed to get available games")
        record_test("Human-Bot API - Integer Bet Amounts", False, "Games retrieval failed")
    
    # Step 8: Cleanup - Delete test bots
    print_subheader("Step 8: Cleanup - Delete Test Bots")
    
    # Delete main test bot
    delete_response, delete_success = make_request(
        "DELETE", f"/admin/human-bots/{test_bot_id}",
        auth_token=admin_token
    )
    
    if delete_success:
        print_success("✓ Main test bot deleted successfully")
    else:
        print_warning("⚠ Failed to delete main test bot")
    
    # Delete bulk-created bots
    for bot_id in bulk_bot_ids:
        delete_response, delete_success = make_request(
            "DELETE", f"/admin/human-bots/{bot_id}",
            auth_token=admin_token
        )
        if delete_success:
            print_success(f"✓ Bulk test bot {bot_id} deleted")
        else:
            print_warning(f"⚠ Failed to delete bulk test bot {bot_id}")
    
    print_success("✓ Cleanup completed")

def test_regular_bot_api_endpoints() -> None:
    """Test Regular Bot API endpoints with integer values for min_bet/max_bet."""
    print_header("REGULAR BOT API ENDPOINTS TESTING - GEM DISPLAY CHANGES")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with Regular Bot API test")
        record_test("Regular Bot API - Admin Login", False, "Admin login failed")
        return
    
    print_success(f"Admin logged in successfully")
    
    # Step 2: Test Regular Bot creation with integer values
    print_subheader("Step 2: Test Regular Bot Creation with Integer Values")
    
    # Test creating Regular Bot with integer min_bet_amount/max_bet_amount values (gems)
    test_bot_data = {
        "name": f"GemRegularBot_{int(time.time())}",
        "bot_type": "REGULAR",
        "min_bet_amount": 3,  # Integer value (3 gems = $3)
        "max_bet_amount": 30,  # Integer value (30 gems = $30)
        "win_rate": 55.0,
        "cycle_games": 15,
        "individual_limit": 15,
        "creation_mode": "queue-based",
        "priority_order": 50,
        "pause_between_games": 5,
        "profit_strategy": "balanced",
        "can_accept_bets": False,
        "can_play_with_bots": False,
        "avatar_gender": "male",
        "simple_mode": False
    }
    
    create_response, create_success = make_request(
        "POST", "/admin/bots/regular",
        data=test_bot_data,
        auth_token=admin_token
    )
    
    if create_success:
        test_bot_id = create_response.get("id")
        if test_bot_id:
            print_success(f"✓ Regular Bot created successfully with integer values")
            print_success(f"  Bot ID: {test_bot_id}")
            print_success(f"  Min bet: {test_bot_data['min_bet_amount']} gems")
            print_success(f"  Max bet: {test_bot_data['max_bet_amount']} gems")
            record_test("Regular Bot API - Create with Integer Values", True)
        else:
            print_error("Regular Bot creation response missing ID")
            record_test("Regular Bot API - Create with Integer Values", False, "Missing bot ID")
            return
    else:
        print_error(f"Failed to create Regular Bot with integer values: {create_response}")
        record_test("Regular Bot API - Create with Integer Values", False, "Creation failed")
        return
    
    # Step 3: Test Regular Bot list endpoint
    print_subheader("Step 3: Test Regular Bot List Endpoint")
    
    list_response, list_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=50",
        auth_token=admin_token
    )
    
    if list_success:
        bots = list_response.get("bots", [])
        print_success(f"✓ Regular Bot list retrieved successfully ({len(bots)} bots)")
        
        # Find our test bot in the list
        test_bot_found = False
        for bot in bots:
            if bot.get("id") == test_bot_id:
                test_bot_found = True
                list_min_bet = bot.get("min_bet_amount")
                list_max_bet = bot.get("max_bet_amount")
                
                print_success(f"✓ Test bot found in list")
                print_success(f"  List min_bet_amount: {list_min_bet} (type: {type(list_min_bet).__name__})")
                print_success(f"  List max_bet_amount: {list_max_bet} (type: {type(list_max_bet).__name__})")
                
                # Verify consistency
                if list_min_bet == 3 and list_max_bet == 30:
                    print_success("✓ List values consistent with creation")
                    record_test("Regular Bot API - List Consistency", True)
                else:
                    print_error(f"✗ List values inconsistent: min={list_min_bet}, max={list_max_bet}")
                    record_test("Regular Bot API - List Consistency", False, f"Values: min={list_min_bet}, max={list_max_bet}")
                break
        
        if not test_bot_found:
            print_error("✗ Test bot not found in list")
            record_test("Regular Bot API - List Contains Bot", False, "Bot not found")
        else:
            record_test("Regular Bot API - List Contains Bot", True)
    else:
        print_error("Failed to retrieve Regular Bot list")
        record_test("Regular Bot API - List Endpoint", False, "List retrieval failed")
    
    # Step 4: Test Regular Bot update with integer values
    print_subheader("Step 4: Test Regular Bot Update with Integer Values")
    
    update_data = {
        "min_bet_amount": 5,  # Update to 5 gems
        "max_bet_amount": 50,  # Update to 50 gems
        "cycle_games": 20
    }
    
    update_response, update_success = make_request(
        "PUT", f"/admin/bots/regular/{test_bot_id}",
        data=update_data,
        auth_token=admin_token
    )
    
    if update_success:
        print_success("✓ Regular Bot updated successfully with integer values")
        
        # Verify updated values
        updated_min_bet = update_response.get("min_bet_amount")
        updated_max_bet = update_response.get("max_bet_amount")
        
        if updated_min_bet == 5 and updated_max_bet == 50:
            print_success(f"✓ Updated values correct: min={updated_min_bet}, max={updated_max_bet}")
            record_test("Regular Bot API - Update Integer Values", True)
        else:
            print_error(f"✗ Updated values incorrect: min={updated_min_bet}, max={updated_max_bet}")
            record_test("Regular Bot API - Update Integer Values", False, f"Values: min={updated_min_bet}, max={updated_max_bet}")
    else:
        print_error(f"Failed to update Regular Bot: {update_response}")
        record_test("Regular Bot API - Update Integer Values", False, "Update failed")
    
    # Step 5: Test Regular Bot game creation with integer bet values
    print_subheader("Step 5: Test Regular Bot Game Creation with Integer Bet Values")
    
    # Get available Regular bot games to verify bet amounts are integers
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        regular_bot_games = [game for game in available_games_response if game.get("creator_type") == "bot" and game.get("bot_type") == "REGULAR"]
        
        if regular_bot_games:
            print_success(f"✓ Found {len(regular_bot_games)} Regular bot games")
            
            # Check first few games for integer bet amounts
            integer_bets_count = 0
            for i, game in enumerate(regular_bot_games[:5]):
                bet_amount = game.get("bet_amount", 0)
                game_id = game.get("game_id", "unknown")
                
                print_success(f"  Game {i+1}: ID={game_id}, Bet=${bet_amount}")
                
                # Check if bet amount is effectively an integer (no decimal part)
                if isinstance(bet_amount, (int, float)) and bet_amount == int(bet_amount):
                    integer_bets_count += 1
                    print_success(f"    ✓ Bet amount is integer-compatible: {int(bet_amount)}")
                else:
                    print_warning(f"    ⚠ Bet amount has decimal part: {bet_amount}")
            
            if integer_bets_count >= 3:  # At least 3 out of 5 should be integer-compatible
                print_success("✓ Most Regular bot games have integer-compatible bet amounts")
                record_test("Regular Bot API - Integer Bet Amounts", True)
            else:
                print_warning("⚠ Some Regular bot games have non-integer bet amounts")
                record_test("Regular Bot API - Integer Bet Amounts", False, f"Only {integer_bets_count}/5 integer bets")
        else:
            print_warning("No Regular bot games found for bet amount verification")
            record_test("Regular Bot API - Integer Bet Amounts", False, "No games found")
    else:
        print_error("Failed to get available games")
        record_test("Regular Bot API - Integer Bet Amounts", False, "Games retrieval failed")
    
    # Step 6: Cleanup - Delete test bot
    print_subheader("Step 6: Cleanup - Delete Test Bot")
    
    delete_response, delete_success = make_request(
        "DELETE", f"/admin/bots/regular/{test_bot_id}",
        auth_token=admin_token
    )
    
    if delete_success:
        print_success("✓ Test Regular Bot deleted successfully")
    else:
        print_warning("⚠ Failed to delete test Regular Bot")
    
    print_success("✓ Cleanup completed")

def test_existing_bots_compatibility() -> None:
    """Test that existing bots still work correctly with the gem display changes."""
    print_header("EXISTING BOTS COMPATIBILITY TESTING - GEM DISPLAY CHANGES")
    
    # Step 1: Login as admin user
    print_subheader("Step 1: Admin Login")
    admin_token = test_login(ADMIN_USER["email"], ADMIN_USER["password"], "admin")
    
    if not admin_token:
        print_error("Failed to login as admin - cannot proceed with compatibility test")
        record_test("Existing Bots Compatibility - Admin Login", False, "Admin login failed")
        return
    
    print_success(f"Admin logged in successfully")
    
    # Step 2: Test existing Human-Bots
    print_subheader("Step 2: Test Existing Human-Bots")
    
    human_bots_response, human_bots_success = make_request(
        "GET", "/admin/human-bots?page=1&limit=20",
        auth_token=admin_token
    )
    
    if human_bots_success:
        human_bots = human_bots_response.get("bots", [])
        print_success(f"✓ Found {len(human_bots)} existing Human-Bots")
        
        if human_bots:
            # Check first few bots for proper min_bet/max_bet values
            compatible_bots = 0
            for i, bot in enumerate(human_bots[:5]):
                bot_id = bot.get("id", "unknown")
                bot_name = bot.get("name", "unknown")
                min_bet = bot.get("min_bet")
                max_bet = bot.get("max_bet")
                
                print_success(f"  Bot {i+1}: {bot_name}")
                print_success(f"    ID: {bot_id}")
                print_success(f"    Min bet: {min_bet} (type: {type(min_bet).__name__})")
                print_success(f"    Max bet: {max_bet} (type: {type(max_bet).__name__})")
                
                # Check if values are numeric and reasonable
                if isinstance(min_bet, (int, float)) and isinstance(max_bet, (int, float)):
                    if 1 <= min_bet <= 10000 and 1 <= max_bet <= 10000 and min_bet <= max_bet:
                        compatible_bots += 1
                        print_success(f"    ✓ Values are compatible with gem display")
                    else:
                        print_warning(f"    ⚠ Values outside expected range or invalid order")
                else:
                    print_error(f"    ✗ Values are not numeric")
            
            if compatible_bots >= len(human_bots[:5]) * 0.8:  # At least 80% should be compatible
                print_success("✓ Most existing Human-Bots are compatible with gem display")
                record_test("Existing Bots Compatibility - Human-Bots", True)
            else:
                print_warning("⚠ Some existing Human-Bots may have compatibility issues")
                record_test("Existing Bots Compatibility - Human-Bots", False, f"Only {compatible_bots}/{len(human_bots[:5])} compatible")
        else:
            print_warning("No existing Human-Bots found")
            record_test("Existing Bots Compatibility - Human-Bots", False, "No bots found")
    else:
        print_error("Failed to retrieve existing Human-Bots")
        record_test("Existing Bots Compatibility - Human-Bots", False, "Retrieval failed")
    
    # Step 3: Test existing Regular Bots
    print_subheader("Step 3: Test Existing Regular Bots")
    
    regular_bots_response, regular_bots_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=20",
        auth_token=admin_token
    )
    
    if regular_bots_success:
        regular_bots = regular_bots_response.get("bots", [])
        print_success(f"✓ Found {len(regular_bots)} existing Regular Bots")
        
        if regular_bots:
            # Check first few bots for proper min_bet_amount/max_bet_amount values
            compatible_bots = 0
            for i, bot in enumerate(regular_bots[:5]):
                bot_id = bot.get("id", "unknown")
                bot_name = bot.get("name", "unknown")
                min_bet = bot.get("min_bet_amount")
                max_bet = bot.get("max_bet_amount")
                
                print_success(f"  Bot {i+1}: {bot_name}")
                print_success(f"    ID: {bot_id}")
                print_success(f"    Min bet amount: {min_bet} (type: {type(min_bet).__name__})")
                print_success(f"    Max bet amount: {max_bet} (type: {type(max_bet).__name__})")
                
                # Check if values are numeric and reasonable
                if isinstance(min_bet, (int, float)) and isinstance(max_bet, (int, float)):
                    if 1 <= min_bet <= 10000 and 1 <= max_bet <= 10000 and min_bet <= max_bet:
                        compatible_bots += 1
                        print_success(f"    ✓ Values are compatible with gem display")
                    else:
                        print_warning(f"    ⚠ Values outside expected range or invalid order")
                else:
                    print_error(f"    ✗ Values are not numeric")
            
            if compatible_bots >= len(regular_bots[:5]) * 0.8:  # At least 80% should be compatible
                print_success("✓ Most existing Regular Bots are compatible with gem display")
                record_test("Existing Bots Compatibility - Regular Bots", True)
            else:
                print_warning("⚠ Some existing Regular Bots may have compatibility issues")
                record_test("Existing Bots Compatibility - Regular Bots", False, f"Only {compatible_bots}/{len(regular_bots[:5])} compatible")
        else:
            print_warning("No existing Regular Bots found")
            record_test("Existing Bots Compatibility - Regular Bots", False, "No bots found")
    else:
        print_error("Failed to retrieve existing Regular Bots")
        record_test("Existing Bots Compatibility - Regular Bots", False, "Retrieval failed")
    
    # Step 4: Test that existing bot games still work
    print_subheader("Step 4: Test Existing Bot Games")
    
    available_games_response, available_games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if available_games_success and isinstance(available_games_response, list):
        bot_games = [game for game in available_games_response if game.get("creator_type") in ["bot", "human_bot"]]
        
        if bot_games:
            print_success(f"✓ Found {len(bot_games)} existing bot games")
            
            # Check games for reasonable bet amounts
            reasonable_bets = 0
            for i, game in enumerate(bot_games[:10]):
                game_id = game.get("game_id", "unknown")
                bet_amount = game.get("bet_amount", 0)
                creator_type = game.get("creator_type", "unknown")
                
                print_success(f"  Game {i+1}: ID={game_id}, Creator={creator_type}, Bet=${bet_amount}")
                
                # Check if bet amount is reasonable (between $1 and $10000)
                if isinstance(bet_amount, (int, float)) and 1 <= bet_amount <= 10000:
                    reasonable_bets += 1
                    print_success(f"    ✓ Bet amount is reasonable")
                else:
                    print_warning(f"    ⚠ Bet amount outside reasonable range")
            
            if reasonable_bets >= len(bot_games[:10]) * 0.8:  # At least 80% should be reasonable
                print_success("✓ Most existing bot games have reasonable bet amounts")
                record_test("Existing Bots Compatibility - Game Bet Amounts", True)
            else:
                print_warning("⚠ Some existing bot games have unreasonable bet amounts")
                record_test("Existing Bots Compatibility - Game Bet Amounts", False, f"Only {reasonable_bets}/{len(bot_games[:10])} reasonable")
        else:
            print_warning("No existing bot games found")
            record_test("Existing Bots Compatibility - Game Bet Amounts", False, "No games found")
    else:
        print_error("Failed to retrieve existing bot games")
        record_test("Existing Bots Compatibility - Game Bet Amounts", False, "Games retrieval failed")

def print_test_summary() -> None:
    """Print a summary of all test results."""
    print_header("GEM DISPLAY CHANGES TEST SUMMARY")
    
    print_success(f"Total tests run: {test_results['total']}")
    print_success(f"Tests passed: {test_results['passed']}")
    
    if test_results['failed'] > 0:
        print_error(f"Tests failed: {test_results['failed']}")
    else:
        print_success(f"Tests failed: {test_results['failed']}")
    
    if test_results['total'] > 0:
        success_rate = (test_results['passed'] / test_results['total']) * 100
        print_success(f"Success rate: {success_rate:.1f}%")
    
    # Print failed tests details
    if test_results['failed'] > 0:
        print_subheader("Failed Tests Details")
        for test in test_results['tests']:
            if not test['passed']:
                print_error(f"❌ {test['name']}")
                if test['details']:
                    print_error(f"   Details: {test['details']}")
    
    # Overall assessment
    print_subheader("Overall Assessment")
    
    if test_results['failed'] == 0:
        print_success("🎉 ALL TESTS PASSED!")
        print_success("✅ Gem display changes are working correctly")
        print_success("✅ Backend APIs handle integer values properly")
        print_success("✅ Bot creation and management work with gem values")
        print_success("✅ Existing bots are compatible with the changes")
        print_success("✅ Game creation logic is not broken")
    elif test_results['failed'] <= test_results['total'] * 0.1:  # Less than 10% failed
        print_success("✅ MOSTLY SUCCESSFUL!")
        print_success("✅ Gem display changes are mostly working correctly")
        print_warning("⚠ Minor issues detected - see failed tests above")
    else:
        print_error("❌ SIGNIFICANT ISSUES DETECTED!")
        print_error("❌ Gem display changes have problems")
        print_error("❌ Review failed tests and fix issues")

def main():
    """Main test execution function."""
    print_header("GEM DISPLAY CHANGES TESTING")
    print("Testing changes in bot bet range display from dollars to gems")
    print("CONVERSION LOGIC: $1 = 1 gem (formatAsGems() removes $ and formats as integer)")
    print()
    
    try:
        # Run all test suites
        test_human_bot_api_endpoints()
        test_regular_bot_api_endpoints()
        test_existing_bots_compatibility()
        
        # Print summary
        print_test_summary()
        
    except KeyboardInterrupt:
        print_error("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()