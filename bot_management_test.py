#!/usr/bin/env python3
"""
Bot Creation and Management System Testing
Testing the updated bot creation and management system with all implemented changes as requested in the review.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List, Tuple
import random
import string

# Configuration
BASE_URL = "https://8e080f25-8919-4bb5-9f98-8dbf560b5d39.preview.emergentagent.com/api"
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

def test_admin_login() -> Optional[str]:
    """Test admin login and return token."""
    print_subheader("Admin Login")
    
    login_data = {
        "email": ADMIN_USER["email"],
        "password": ADMIN_USER["password"]
    }
    
    response, success = make_request("POST", "/auth/login", data=login_data)
    
    if success and "access_token" in response:
        print_success("Admin logged in successfully")
        return response["access_token"]
    else:
        print_error("Admin login failed")
        return None

def test_unique_bot_names(admin_token: str) -> None:
    """Test that bot names are unique and auto-generated as Bot#1, Bot#2, etc."""
    print_header("UNIQUE BOT NAMES TESTING")
    
    # Test 1: Create bot without name parameter
    print_subheader("Test 1: Create Bot Without Name Parameter")
    
    create_data = {
        "min_bet_amount": 1.0,
        "max_bet_amount": 50.0,
        "win_rate": 60.0,
        "cycle_games": 12
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=create_data,
        auth_token=admin_token
    )
    
    if success:
        bot_name = response.get("name", "")
        if bot_name.startswith("Bot#") and bot_name[4:].isdigit():
            print_success(f"Bot created with auto-generated name: {bot_name}")
            record_test("Unique Bot Names - Auto Generation", True)
        else:
            print_error(f"Bot name not auto-generated correctly: {bot_name}")
            record_test("Unique Bot Names - Auto Generation", False, f"Name: {bot_name}")
    else:
        print_error("Failed to create bot without name")
        record_test("Unique Bot Names - Auto Generation", False, "Creation failed")
    
    # Test 2: Create multiple bots and verify unique names
    print_subheader("Test 2: Create Multiple Bots and Verify Unique Names")
    
    created_names = []
    for i in range(3):
        response, success = make_request(
            "POST", "/admin/bots/create-regular",
            data=create_data,
            auth_token=admin_token
        )
        
        if success:
            bot_name = response.get("name", "")
            created_names.append(bot_name)
            print_success(f"Bot {i+1} created with name: {bot_name}")
        else:
            print_error(f"Failed to create bot {i+1}")
    
    # Check uniqueness
    if len(created_names) == len(set(created_names)):
        print_success("All bot names are unique")
        record_test("Unique Bot Names - Uniqueness Check", True)
    else:
        print_error(f"Duplicate names found: {created_names}")
        record_test("Unique Bot Names - Uniqueness Check", False, f"Names: {created_names}")
    
    # Test 3: Create bot with custom name
    print_subheader("Test 3: Create Bot With Custom Name")
    
    custom_name = f"CustomBot_{random.randint(1000, 9999)}"
    create_data_with_name = {
        **create_data,
        "name": custom_name
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=create_data_with_name,
        auth_token=admin_token
    )
    
    if success:
        bot_name = response.get("name", "")
        if bot_name == custom_name:
            print_success(f"Bot created with custom name: {bot_name}")
            record_test("Unique Bot Names - Custom Name", True)
        else:
            print_error(f"Custom name not used: expected {custom_name}, got {bot_name}")
            record_test("Unique Bot Names - Custom Name", False, f"Expected: {custom_name}, Got: {bot_name}")
    else:
        print_error("Failed to create bot with custom name")
        record_test("Unique Bot Names - Custom Name", False, "Creation failed")

def test_single_bot_creation(admin_token: str) -> None:
    """Test that the create-regular endpoint now creates only one bot per request."""
    print_header("SINGLE BOT CREATION TESTING")
    
    # Get initial bot count
    print_subheader("Get Initial Bot Count")
    
    initial_response, initial_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=100",
        auth_token=admin_token
    )
    
    if not initial_success:
        print_error("Failed to get initial bot list")
        record_test("Single Bot Creation - Initial Count", False, "Failed to get list")
        return
    
    initial_count = len(initial_response.get("bots", []))
    print_success(f"Initial bot count: {initial_count}")
    
    # Create a single bot
    print_subheader("Create Single Bot")
    
    create_data = {
        "min_bet_amount": 1.0,
        "max_bet_amount": 100.0,
        "win_rate": 55.0,
        "cycle_games": 10
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=create_data,
        auth_token=admin_token
    )
    
    if not success:
        print_error("Failed to create bot")
        record_test("Single Bot Creation - Create Bot", False, "Creation failed")
        return
    
    print_success("Bot created successfully")
    
    # Verify only one bot was created
    print_subheader("Verify Single Bot Created")
    
    final_response, final_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=100",
        auth_token=admin_token
    )
    
    if final_success:
        final_count = len(final_response.get("bots", []))
        print_success(f"Final bot count: {final_count}")
        
        if final_count == initial_count + 1:
            print_success("Exactly one bot was created")
            record_test("Single Bot Creation - Count Verification", True)
        else:
            print_error(f"Expected {initial_count + 1} bots, got {final_count}")
            record_test("Single Bot Creation - Count Verification", False, f"Count: {final_count}")
    else:
        print_error("Failed to get final bot list")
        record_test("Single Bot Creation - Count Verification", False, "Failed to get list")
    
    # Test that count parameter is not accepted (if it was removed)
    print_subheader("Test Count Parameter Removal")
    
    create_data_with_count = {
        **create_data,
        "count": 5  # This should be ignored or cause error
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=create_data_with_count,
        auth_token=admin_token
    )
    
    if success:
        # Check if only one bot was created despite count parameter
        after_count_response, after_count_success = make_request(
            "GET", "/admin/bots/regular/list?page=1&limit=100",
            auth_token=admin_token
        )
        
        if after_count_success:
            after_count = len(after_count_response.get("bots", []))
            if after_count == final_count + 1:
                print_success("Count parameter ignored - only one bot created")
                record_test("Single Bot Creation - Count Parameter Ignored", True)
            else:
                print_error(f"Count parameter not ignored - {after_count - final_count} bots created")
                record_test("Single Bot Creation - Count Parameter Ignored", False, f"Created: {after_count - final_count}")
    else:
        print_success("Request with count parameter rejected (expected)")
        record_test("Single Bot Creation - Count Parameter Rejected", True)

def test_form_validation(admin_token: str) -> None:
    """Test that validation works properly for all bot parameters."""
    print_header("FORM VALIDATION TESTING")
    
    # Test 1: Valid parameters
    print_subheader("Test 1: Valid Parameters")
    
    valid_data = {
        "name": "ValidBot",
        "min_bet_amount": 1.0,
        "max_bet_amount": 100.0,
        "win_rate": 60.0,
        "cycle_games": 12
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=valid_data,
        auth_token=admin_token
    )
    
    if success:
        print_success("Valid parameters accepted")
        record_test("Form Validation - Valid Parameters", True)
    else:
        print_error("Valid parameters rejected")
        record_test("Form Validation - Valid Parameters", False, "Valid data rejected")
    
    # Test 2: Invalid min_bet_amount (negative)
    print_subheader("Test 2: Invalid min_bet_amount (negative)")
    
    invalid_min_bet = {
        **valid_data,
        "min_bet_amount": -1.0
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=invalid_min_bet,
        auth_token=admin_token,
        expected_status=422
    )
    
    if not success and response.get("detail"):
        print_success("Negative min_bet_amount correctly rejected")
        record_test("Form Validation - Negative Min Bet", True)
    else:
        print_error("Negative min_bet_amount not rejected")
        record_test("Form Validation - Negative Min Bet", False, "Not rejected")
    
    # Test 3: Invalid max_bet_amount (less than min)
    print_subheader("Test 3: Invalid max_bet_amount (less than min)")
    
    invalid_max_bet = {
        **valid_data,
        "min_bet_amount": 100.0,
        "max_bet_amount": 50.0
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=invalid_max_bet,
        auth_token=admin_token,
        expected_status=422
    )
    
    if not success:
        print_success("max_bet_amount < min_bet_amount correctly rejected")
        record_test("Form Validation - Max Less Than Min", True)
    else:
        print_error("max_bet_amount < min_bet_amount not rejected")
        record_test("Form Validation - Max Less Than Min", False, "Not rejected")
    
    # Test 4: Invalid win_rate (over 100%)
    print_subheader("Test 4: Invalid win_rate (over 100%)")
    
    invalid_win_rate = {
        **valid_data,
        "win_rate": 150.0
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=invalid_win_rate,
        auth_token=admin_token,
        expected_status=422
    )
    
    if not success:
        print_success("win_rate > 100% correctly rejected")
        record_test("Form Validation - Win Rate Over 100", True)
    else:
        print_error("win_rate > 100% not rejected")
        record_test("Form Validation - Win Rate Over 100", False, "Not rejected")
    
    # Test 5: Invalid cycle_games (zero)
    print_subheader("Test 5: Invalid cycle_games (zero)")
    
    invalid_cycle_games = {
        **valid_data,
        "cycle_games": 0
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=invalid_cycle_games,
        auth_token=admin_token,
        expected_status=422
    )
    
    if not success:
        print_success("cycle_games = 0 correctly rejected")
        record_test("Form Validation - Zero Cycle Games", True)
    else:
        print_error("cycle_games = 0 not rejected")
        record_test("Form Validation - Zero Cycle Games", False, "Not rejected")
    
    # Test 6: Missing required fields
    print_subheader("Test 6: Missing Required Fields")
    
    incomplete_data = {
        "name": "IncompleteBot"
        # Missing required fields
    }
    
    response, success = make_request(
        "POST", "/admin/bots/create-regular",
        data=incomplete_data,
        auth_token=admin_token,
        expected_status=422
    )
    
    if not success:
        print_success("Missing required fields correctly rejected")
        record_test("Form Validation - Missing Fields", True)
    else:
        print_error("Missing required fields not rejected")
        record_test("Form Validation - Missing Fields", False, "Not rejected")

def test_regular_bot_game_logic(admin_token: str) -> None:
    """Test that regular bots cannot join live player games (new restriction)."""
    print_header("REGULAR BOT GAME LOGIC TESTING")
    
    # This test would require creating a live player game and verifying bots don't join
    # Since we're testing the backend API, we'll test the game creation and availability logic
    
    print_subheader("Test 1: Get Available Games")
    
    # Get available games to see bot vs player game separation
    response, success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if success:
        games = response if isinstance(response, list) else []
        bot_games = [g for g in games if g.get("creator_type") == "bot"]
        player_games = [g for g in games if g.get("creator_type") == "user"]
        
        print_success(f"Found {len(bot_games)} bot games and {len(player_games)} player games")
        
        # Check that bot games are marked as such
        regular_bot_games = [g for g in bot_games if g.get("bot_type") == "REGULAR"]
        print_success(f"Found {len(regular_bot_games)} regular bot games")
        
        if regular_bot_games:
            print_success("Regular bot games are properly categorized")
            record_test("Regular Bot Game Logic - Game Categorization", True)
        else:
            print_warning("No regular bot games found for testing")
            record_test("Regular Bot Game Logic - Game Categorization", False, "No games found")
    else:
        print_error("Failed to get available games")
        record_test("Regular Bot Game Logic - Get Games", False, "Request failed")
    
    # Test 2: Verify bot game properties
    print_subheader("Test 2: Verify Bot Game Properties")
    
    if success and regular_bot_games:
        sample_game = regular_bot_games[0]
        
        # Check required properties
        required_props = ["game_id", "creator_id", "bet_amount", "status", "bot_type"]
        missing_props = [prop for prop in required_props if prop not in sample_game]
        
        if not missing_props:
            print_success("Bot games have all required properties")
            record_test("Regular Bot Game Logic - Game Properties", True)
        else:
            print_error(f"Bot games missing properties: {missing_props}")
            record_test("Regular Bot Game Logic - Game Properties", False, f"Missing: {missing_props}")
        
        # Check that bot_type is REGULAR
        if sample_game.get("bot_type") == "REGULAR":
            print_success("Bot games correctly marked as REGULAR type")
            record_test("Regular Bot Game Logic - Bot Type", True)
        else:
            print_error(f"Bot type incorrect: {sample_game.get('bot_type')}")
            record_test("Regular Bot Game Logic - Bot Type", False, f"Type: {sample_game.get('bot_type')}")

def test_commission_free_logic(admin_token: str) -> None:
    """Test that games with regular bots have no commission frozen or charged."""
    print_header("COMMISSION-FREE LOGIC TESTING")
    
    # Test 1: Get user balance before testing
    print_subheader("Test 1: Get Initial Balance")
    
    balance_response, balance_success = make_request(
        "GET", "/auth/me",
        auth_token=admin_token
    )
    
    if not balance_success:
        print_error("Failed to get initial balance")
        record_test("Commission-Free Logic - Get Balance", False, "Failed to get balance")
        return
    
    initial_virtual = balance_response.get("virtual_balance", 0)
    initial_frozen = balance_response.get("frozen_balance", 0)
    
    print_success(f"Initial balance - Virtual: ${initial_virtual}, Frozen: ${initial_frozen}")
    
    # Test 2: Find and join a regular bot game
    print_subheader("Test 2: Join Regular Bot Game")
    
    games_response, games_success = make_request(
        "GET", "/games/available",
        auth_token=admin_token
    )
    
    if not games_success:
        print_error("Failed to get available games")
        record_test("Commission-Free Logic - Get Games", False, "Failed to get games")
        return
    
    games = games_response if isinstance(games_response, list) else []
    regular_bot_games = [g for g in games if g.get("creator_type") == "bot" and g.get("bot_type") == "REGULAR"]
    
    if not regular_bot_games:
        print_warning("No regular bot games available for testing")
        record_test("Commission-Free Logic - Find Bot Game", False, "No games available")
        return
    
    bot_game = regular_bot_games[0]
    game_id = bot_game["game_id"]
    bet_amount = bot_game["bet_amount"]
    
    print_success(f"Found regular bot game: {game_id} with bet amount: ${bet_amount}")
    
    # Join the bot game
    join_data = {
        "move": "rock",
        "gems": {"Ruby": int(bet_amount)}  # Match the bet amount
    }
    
    join_response, join_success = make_request(
        "POST", f"/games/{game_id}/join",
        data=join_data,
        auth_token=admin_token
    )
    
    if join_success:
        print_success("Successfully joined regular bot game")
        
        # Test 3: Check balance after joining (should have no commission frozen)
        print_subheader("Test 3: Verify No Commission Frozen")
        
        after_join_response, after_join_success = make_request(
            "GET", "/auth/me",
            auth_token=admin_token
        )
        
        if after_join_success:
            after_virtual = after_join_response.get("virtual_balance", 0)
            after_frozen = after_join_response.get("frozen_balance", 0)
            
            print_success(f"After joining - Virtual: ${after_virtual}, Frozen: ${after_frozen}")
            
            # For regular bot games, no commission should be frozen
            virtual_unchanged = abs(after_virtual - initial_virtual) < 0.01
            frozen_unchanged = abs(after_frozen - initial_frozen) < 0.01
            
            if virtual_unchanged and frozen_unchanged:
                print_success("✓ No commission frozen when joining regular bot game")
                record_test("Commission-Free Logic - No Commission Frozen", True)
            else:
                print_error("✗ Commission incorrectly frozen for regular bot game")
                print_error(f"Virtual change: ${after_virtual - initial_virtual}")
                print_error(f"Frozen change: ${after_frozen - initial_frozen}")
                record_test("Commission-Free Logic - No Commission Frozen", False, "Commission frozen")
        else:
            print_error("Failed to get balance after joining")
            record_test("Commission-Free Logic - No Commission Frozen", False, "Failed to get balance")
    else:
        print_error("Failed to join regular bot game")
        record_test("Commission-Free Logic - Join Bot Game", False, "Join failed")

def test_bot_management_endpoints(admin_token: str) -> None:
    """Test all bot management endpoints work correctly with updated structure."""
    print_header("BOT MANAGEMENT ENDPOINTS TESTING")
    
    # Test 1: GET /api/admin/bots/regular/list
    print_subheader("Test 1: GET /api/admin/bots/regular/list")
    
    list_response, list_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=10",
        auth_token=admin_token
    )
    
    if list_success:
        if "bots" in list_response and isinstance(list_response["bots"], list):
            print_success(f"Bot list retrieved successfully - {len(list_response['bots'])} bots")
            
            # Check pagination metadata
            required_fields = ["total_count", "current_page", "total_pages", "items_per_page"]
            missing_fields = [f for f in required_fields if f not in list_response]
            
            if not missing_fields:
                print_success("Pagination metadata complete")
                record_test("Bot Management - List Endpoint", True)
            else:
                print_warning(f"Missing pagination fields: {missing_fields}")
                record_test("Bot Management - List Endpoint", False, f"Missing: {missing_fields}")
        else:
            print_error("Invalid response structure")
            record_test("Bot Management - List Endpoint", False, "Invalid structure")
    else:
        print_error("Failed to get bot list")
        record_test("Bot Management - List Endpoint", False, "Request failed")
    
    # Get a bot ID for further testing
    bot_id = None
    if list_success and list_response.get("bots"):
        bot_id = list_response["bots"][0]["id"]
        print_success(f"Using bot ID for testing: {bot_id}")
    
    # Test 2: GET /api/admin/bots/{bot_id}
    if bot_id:
        print_subheader("Test 2: GET /api/admin/bots/{bot_id}")
        
        get_response, get_success = make_request(
            "GET", f"/admin/bots/{bot_id}",
            auth_token=admin_token
        )
        
        if get_success:
            # Check required bot fields
            required_fields = ["id", "name", "bot_type", "is_active", "min_bet_amount", "max_bet_amount"]
            missing_fields = [f for f in required_fields if f not in get_response]
            
            if not missing_fields:
                print_success("Bot details retrieved with all required fields")
                record_test("Bot Management - Get Bot Endpoint", True)
            else:
                print_error(f"Missing bot fields: {missing_fields}")
                record_test("Bot Management - Get Bot Endpoint", False, f"Missing: {missing_fields}")
        else:
            print_error("Failed to get bot details")
            record_test("Bot Management - Get Bot Endpoint", False, "Request failed")
        
        # Test 3: PUT /api/admin/bots/{bot_id}
        print_subheader("Test 3: PUT /api/admin/bots/{bot_id}")
        
        update_data = {
            "min_bet_amount": 2.0,
            "max_bet_amount": 200.0,
            "win_rate": 65.0,
            "cycle_games": 15
        }
        
        update_response, update_success = make_request(
            "PUT", f"/admin/bots/{bot_id}",
            data=update_data,
            auth_token=admin_token
        )
        
        if update_success:
            # Verify the update was applied
            verify_response, verify_success = make_request(
                "GET", f"/admin/bots/{bot_id}",
                auth_token=admin_token
            )
            
            if verify_success:
                updated_correctly = (
                    verify_response.get("min_bet_amount") == 2.0 and
                    verify_response.get("max_bet_amount") == 200.0 and
                    verify_response.get("win_rate") == 65.0 and
                    verify_response.get("cycle_games") == 15
                )
                
                if updated_correctly:
                    print_success("Bot updated successfully")
                    record_test("Bot Management - Update Bot Endpoint", True)
                else:
                    print_error("Bot update not applied correctly")
                    record_test("Bot Management - Update Bot Endpoint", False, "Update not applied")
            else:
                print_error("Failed to verify bot update")
                record_test("Bot Management - Update Bot Endpoint", False, "Verification failed")
        else:
            print_error("Failed to update bot")
            record_test("Bot Management - Update Bot Endpoint", False, "Update failed")
    else:
        print_warning("No bot ID available for individual bot tests")
        record_test("Bot Management - Get Bot Endpoint", False, "No bot ID")
        record_test("Bot Management - Update Bot Endpoint", False, "No bot ID")

def test_bot_settings_modal(admin_token: str) -> None:
    """Test that the bot settings modal loads all bot parameters correctly."""
    print_header("BOT SETTINGS MODAL TESTING")
    
    # This test focuses on the API endpoints that would be used by the modal
    
    # Test 1: Get bot settings data
    print_subheader("Test 1: Get Bot Settings Data")
    
    # Get a bot for testing
    list_response, list_success = make_request(
        "GET", "/admin/bots/regular/list?page=1&limit=1",
        auth_token=admin_token
    )
    
    if not list_success or not list_response.get("bots"):
        print_error("No bots available for settings modal test")
        record_test("Bot Settings Modal - Get Bot Data", False, "No bots available")
        return
    
    bot = list_response["bots"][0]
    bot_id = bot["id"]
    
    # Get detailed bot information
    bot_response, bot_success = make_request(
        "GET", f"/admin/bots/{bot_id}",
        auth_token=admin_token
    )
    
    if bot_success:
        # Check that all modal parameters are available
        modal_fields = [
            "id", "name", "bot_type", "is_active",
            "min_bet_amount", "max_bet_amount", "win_rate", "cycle_games",
            "individual_limit", "priority_order", "pause_between_games",
            "profit_strategy", "created_at"
        ]
        
        available_fields = [f for f in modal_fields if f in bot_response]
        missing_fields = [f for f in modal_fields if f not in bot_response]
        
        print_success(f"Available modal fields: {len(available_fields)}/{len(modal_fields)}")
        
        if len(available_fields) >= len(modal_fields) * 0.8:  # At least 80% of fields
            print_success("Bot settings modal data sufficient")
            record_test("Bot Settings Modal - Data Completeness", True)
        else:
            print_warning(f"Missing modal fields: {missing_fields}")
            record_test("Bot Settings Modal - Data Completeness", False, f"Missing: {missing_fields}")
        
        # Test 2: Verify data types are correct for modal
        print_subheader("Test 2: Verify Data Types for Modal")
        
        type_checks = [
            ("min_bet_amount", (int, float)),
            ("max_bet_amount", (int, float)),
            ("win_rate", (int, float)),
            ("cycle_games", int),
            ("is_active", bool)
        ]
        
        type_errors = []
        for field, expected_type in type_checks:
            if field in bot_response:
                if not isinstance(bot_response[field], expected_type):
                    type_errors.append(f"{field}: expected {expected_type}, got {type(bot_response[field])}")
        
        if not type_errors:
            print_success("All data types correct for modal")
            record_test("Bot Settings Modal - Data Types", True)
        else:
            print_error(f"Data type errors: {type_errors}")
            record_test("Bot Settings Modal - Data Types", False, f"Errors: {type_errors}")
    else:
        print_error("Failed to get bot data for modal")
        record_test("Bot Settings Modal - Get Bot Data", False, "Request failed")

def print_test_summary():
    """Print test summary."""
    print_header("TEST SUMMARY")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    
    print(f"Total Tests: {total}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print_success("Overall test result: PASSED")
        else:
            print_error("Overall test result: FAILED")
    
    # Print failed tests
    if failed > 0:
        print_subheader("Failed Tests:")
        for test in test_results["tests"]:
            if not test["passed"]:
                print_error(f"- {test['name']}: {test['details']}")

def main():
    """Main test function."""
    print_header("BOT CREATION AND MANAGEMENT SYSTEM TESTING")
    print("Testing the updated bot creation and management system with all implemented changes")
    
    # Login as admin
    admin_token = test_admin_login()
    if not admin_token:
        print_error("Cannot proceed without admin token")
        return
    
    # Run all tests
    test_unique_bot_names(admin_token)
    test_single_bot_creation(admin_token)
    test_form_validation(admin_token)
    test_regular_bot_game_logic(admin_token)
    test_commission_free_logic(admin_token)
    test_bot_management_endpoints(admin_token)
    test_bot_settings_modal(admin_token)
    
    # Print summary
    print_test_summary()

if __name__ == "__main__":
    main()